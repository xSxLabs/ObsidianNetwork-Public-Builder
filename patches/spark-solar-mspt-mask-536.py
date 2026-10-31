#!/usr/bin/env python3
"""B536: Spark solar MSPT: invalidation-aware endpoint presence mask and no duplicate dirty writes.

Works after XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1 and B502 unlimited output.
Unconnected/blocked solar panels previously checked six ENERGY caps every tick
despite NeoForge capability invalidation being available. Cache the live-face
bitmask, refresh on invalidation plus periodic fail-safe, but preserve the exact
per-tick solar generation, side order, FE transfer, transaction and export budget.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
s=p.read_text(encoding="utf-8")
assert "XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1" in s
assert "XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1" in s
assert "XSXLABS_SPARK_SOLAR_STATIC_DIRECTIONS_V1" in s
assert "B536_SOLAR_MSPT_FACE_MASK" not in s
for contract in (
 "long budget = be.energy.stored();",
 "long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());",
 "be.energyJournal.updateSnapshots(tx);",
 "long extracted = be.energy.extract(accepted);",
 "tx.commit();",
 "budget -= accepted;",
 "int start = be.nextSide++ % sides.length;",
 "Direction side = sides[(start + off) % sides.length];",
):
 assert s.count(contract)==1,("B536_SOLAR_CONTRACT_CHANGED",contract,s.count(contract))
assert s.index("be.energyJournal.updateSnapshots(tx);") < s.index("long extracted = be.energy.extract(accepted);") < s.index("tx.commit();")
def once(a,b):
 global s
 n=s.count(a)
 assert n==1,("B536_SOLAR_SOURCE_DRIFT",a[:100],n)
 s=s.replace(a,b,1)

once("private ServerLevel energyCacheLevel;",
'''// B536_SOLAR_MSPT_FACE_MASK: zero-capability panels do not query six
 // neighbors every server tick. Invalidation catches cable/block changes,
 // 40-tick periodic recheck covers dynamic capabilities lacking notification.
 private int xsxSolarFaceMask=0;
 private boolean xsxSolarFacesDirty=true;
 private long xsxSolarLastFaceScan=Long.MIN_VALUE;
 private ServerLevel energyCacheLevel;''')
# Existing lifecycle invalidation: 2 in onLoad/setRemoved; and one level swap.
assert s.count("java.util.Arrays.fill(energyNeighbors,null);")==3
s=s.replace("java.util.Arrays.fill(energyNeighbors,null);",
'''java.util.Arrays.fill(energyNeighbors,null);
  xsxSolarFacesDirty=true;''')
# Ask cached NeoForge capabilities to flag topology changes as they invalidate.
once("() -> !isRemoved() && level==server, () -> {});",
     "() -> !isRemoved() && level==server, () -> {xsxSolarFacesDirty=true;});")
helper=r'''
 // B536_SOLAR_CACHED_NEIGHBORS: no allocations, no BE/world scans
 // when all external faces remain absent. Does not cache FE balances.
 private int xsxLiveSolarFaces(ServerLevel server) {
  long now=server.getGameTime();
  // Refresh after world changes, capability invalidation or every 40 ticks.
  if(energyCacheLevel!=server)xsxSolarFacesDirty=true;
  if(!xsxSolarFacesDirty && now>=xsxSolarLastFaceScan
       && now-xsxSolarLastFaceScan<40L)return xsxSolarFaceMask;
  xsxSolarFacesDirty=false;
  xsxSolarLastFaceScan=now;
  int mask=0;
  for(Direction side:SOLAR_SCAN_SIDES){
   if(neighborEnergy(server,side)!=null)mask|=1<<side.get3DDataValue();
  }
  xsxSolarFaceMask=mask;
  return mask;
 }
'''
needle="private EnergyHandler neighborEnergy(ServerLevel server,Direction side)"
assert s.count(needle)==1
s=s.replace(needle,helper+"\n "+needle,1)
once("if (budget > 0L) {","if (budget > 0L && be.xsxLiveSolarFaces(server)!=0) {")
# Only probe currently connected sides, but preserve original 0..5 rotation.
once("Direction side = sides[(start + off) % sides.length];",
     """Direction side = sides[(start + off) % sides.length];
               if((be.xsxSolarFaceMask&(1<<side.get3DDataValue()))==0)continue;""")
# The journal marks changed energy on root transaction commit, so the separate
# post-loop setChanged on that same successful FE output was redundant.
matches=list(re.finditer(r"(?s)\n\s*if \(changed\) \{\s*be\.setChanged\(\);\s*\}",s))
assert len(matches)==1,("B536_SOLAR_DOUBLE_DIRTY_GUARD",len(matches))
s=s[:matches[0].start()]+"\n            // B536_SOLAR_JOURNAL_ONLY_DIRTY: onRootCommit already calls setChanged()."+s[matches[0].end():]
assert s.count("xsxLiveSolarFaces(server)") == 1
assert s.count("B536_SOLAR_MSPT_FACE_MASK") == 1
assert s.count("budget -= accepted;")==1
assert s.count("be.energyJournal.updateSnapshots(tx);")==1
assert s.count("tx.commit();")==1
p.write_text(s,encoding="utf-8")
print("B536_SPARK_SOLAR_MSPT_OPTIMIZED_PASS: invalidation-aware cached mask, 40tick fall-back, 6-side fairness, unlimited output, journal-only persistence")
