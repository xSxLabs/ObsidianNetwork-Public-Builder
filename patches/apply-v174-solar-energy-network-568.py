#!/usr/bin/env python3
"""B568: memoize live cable BlockEntities per server tick; solar auto-INPUT.

Only the identity of an existing physical EnergyCableBlockEntity is reused
within a single tick. Never cache mode values, cable BlockStates, conduit
bundles, endpoints, inventories, FE, acceptances or transactions. Stale
instances are rejected after removal, level change or replacement.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
path=root/"blockentity/EnergyCableBlockEntity.java"
s=path.read_text(encoding="utf-8")
marker="B568_PER_TICK_LIVE_CABLE_BE_LOOKUP"
assert marker not in s
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert s.count(cls)==1
for name in ("B497_ENERGY_SIDE_IO","XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1",
             "B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK","public int energySideMode(",
             "public void cycleEnergySide(","private static boolean canEnergyEndpoint(",
             "private static boolean canEnergyWire(",
             "private EnergyHandler liveBoundaryEnergy("):
 assert s.count(name)==1,("B568_SOURCE_CHANGED",name,s.count(name))
helper=r'''
 // B568_PER_TICK_LIVE_CABLE_BE_LOOKUP: one live identity lookup per cable
 // per server tick even if hundreds of panels inject into the same grid.
 // Transfer state and capabilities are ALWAYS queried live, never memoized.
 private static final class XsxCableTickRefs {
  ServerLevel world;
  long tick=Long.MIN_VALUE;
  final it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap<EnergyCableBlockEntity> entries=
      new it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap<>();
 }
 private static final ThreadLocal<XsxCableTickRefs> XSX_CABLE_TICK_REFS=
     ThreadLocal.withInitial(XsxCableTickRefs::new);
 private static EnergyCableBlockEntity xsxLiveCable(ServerLevel server,BlockPos pos) {
  var refs=XSX_CABLE_TICK_REFS.get();
  long tick=server.getGameTime();
  if(refs.world!=server || refs.tick!=tick) {
   refs.entries.clear();refs.world=server;refs.tick=tick;
  }
  long key=pos.asLong();
  EnergyCableBlockEntity known=refs.entries.get(key);
  if(known!=null && !known.isRemoved() && known.level==server
     && known.worldPosition.equals(pos))return known;
  // Do not cache negative misses: a newly placed cable is visible immediately.
  var fresh=server.getBlockEntity(pos);
  if(fresh instanceof EnergyCableBlockEntity live && !live.isRemoved()) {
   refs.entries.put(key,live);return live;
  }
  refs.entries.remove(key);
  return null;
 }
 // B568_SOLAR_AUTO_IMPORT_FACE: cable-side direction faces a solar block.
 // Do not override OFF/OUTPUT/manually selected modes; only BOTH -> INPUT.
 private void xsxSolarInputIfBoth(Direction side) {
  int i=side.get3DDataValue();
  if((energySideMode[i]&255)!=3)return;
  energySideMode[i]=1;
  setChanged();
  if(level!=null&&!level.isClientSide())sync();
 }
 private void xsxSolarNeighborsAtLoad() {
  if(!(level instanceof ServerLevel sl))return;
  for(Direction side:ENERGY_SCAN_DIRECTIONS) {
   BlockPos at=worldPosition.relative(side);
   if(sl.hasChunkAt(at) && sl.getBlockState(at).getBlock() instanceof
       dev.obsidiannetwork.block.SolarGeneratorBlock)
    xsxSolarInputIfBoth(side);
  }
 }
 public static void xsxAutoImportSolar(ServerLevel sl,BlockPos solar) {
  for(Direction side:ENERGY_SCAN_DIRECTIONS) {
   BlockPos at=solar.relative(side);
   if(!sl.hasChunkAt(at))continue;
   if(sl.getBlockEntity(at) instanceof EnergyCableBlockEntity be)
    be.xsxSolarInputIfBoth(side.getOpposite());
  }
 }
'''
s=s.replace(cls,cls+"\n"+helper,1)
# Existing mode checks must still run EVERY request. Only BE identity is reused.
for method in ("canEnergyEndpoint","canEnergyWire"):
 start=s.index("private static boolean "+method+"(")
 stop=s.index("}",start)
 body=s[start:stop]
 old="world.getBlockEntity(cable)"
 assert body.count(old)==1,("B568_EXPECT_LIVE_MODE_LOOKUP",method,body[:400])
 body=body.replace(old,"xsxLiveCable(world,cable)",1)
 s=s[:start]+body+s[stop:]
# The endpoint cache owner is likewise looked up by live position, not by
# stale handler or by an arbitrary BFS root.
start=s.index("private EnergyHandler liveBoundaryEnergy(")
end=s.index("}",start)
body=s[start:end]
old="server.getBlockEntity(cable)"
assert body.count(old)==1,("B568_BOUNDARY_BE_SHAPE",body[:750])
body=body.replace(old,"xsxLiveCable(server,cable)",1)
s=s[:start]+body+s[end:]
# BE load after full NBT restore; newly placed cables see already placed panels.
assert s.count("clearEnergyEndpointCaches();")>=3
old="super.onLoad();\n      clearEnergyEndpointCaches();"
assert s.count(old)==1,("B568_CABLE_ONLOAD_DRIFT",s.count(old))
s=s.replace(old,old+"\n      xsxSolarNeighborsAtLoad();",1)
path.write_text(s,encoding="utf-8")
# Solar placement when cable was already in the world; call its existing
# lifecycle hook instead of doing extra neighbor scans on EVERY 20Hz tick.
p=root/"blockentity/SolarGeneratorBlockEntity.java"
solar=p.read_text(encoding="utf-8")
assert solar.count("B566_SOLAR_SKY_BLOCKPOS_REUSE")==1
assert solar.count("super.onLoad();")==1
assert "B568_SOLAR_AUTO_IMPORT_NEIGHBOR" not in solar
solar=solar.replace("super.onLoad();","super.onLoad();\n   // B568_SOLAR_AUTO_IMPORT_NEIGHBOR: one placement/load scan, never on tick.\n   if(level instanceof ServerLevel sl)\n     EnergyCableBlockEntity.xsxAutoImportSolar(sl,worldPosition);",1)
p.write_text(solar,encoding="utf-8")
print("B568_CABLE_TICK_BE_CACHE_SOLAR_AUTO_INPUT_PASS: cached identity, live modes, no FE/rate changes")
