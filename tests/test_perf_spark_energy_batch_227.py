#!/usr/bin/env python3
"""Unit and fail-closed tests for grouped Spark energy hotpaths in build #227."""
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCH = Path(__file__).resolve().parents[1] / "patches"
CABLE = """// XSXLABS_SPARK_BFS_POSITION_REUSE_V1
// XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1
public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {
 private final class CableEnergyHandler implements EnergyHandler {
""" + ("""
 void walk(){
 HashSet visited = new HashSet();
 visited.add(EnergyCableBlockEntity.this.worldPosition);
 BlockPos next = cable.relative(side);
 if(visited.add(next)) queue.addLast(next);
 while(cableBudget-- > 0){}
 }
""" * 3) + """
 }
}
"""
TOPOLOGY = """public final class ConduitTopology {
 private static final Direction[] XSXLABS_SPARK_TOPOLOGY_DIRECTIONS_V1 = Direction.values();
 void validate(){
 for(Direction d:XSXLABS_SPARK_TOPOLOGY_DIRECTIONS_V1){
 ConduitBundleBlockEntity other=ConduitRuntime.bundle(level,bundle.getBlockPos().relative(d),type);
 boolean cachedConnected=network.containsPosition(bundle.getBlockPos().relative(d));
 if(physicallyConnected!=cachedConnected){network.nodeChanged(node);}
 }}
}
"""
TICKER = """public final class EnergyConduitTicker implements ConduitTicker {
 // XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1
 // XSXLABS_SPARK_CONDUIT_STATIC_DIRECTIONS_V1
 void tick(){
 if(ConduitRuntime.bundle(level,bundle.getBlockPos().relative(d),ConduitType.ENERGY)!=null)continue;
 EnergyHandler candidate=level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite());
 try(Transaction tx=Transaction.openRoot()){
 int got=from.extract(1000,tx);
 int put=to.insert(got,tx);
 if(put<got)from.insert(got-put,tx);
 tx.commit();return;
 }}
}
"""
SOURCES = {
 "blockentity/EnergyCableBlockEntity.java": CABLE,
 "conduit/ConduitTopology.java": TOPOLOGY,
 "conduit/EnergyConduitTicker.java": TICKER,
}
SCRIPTS = (
 "spark-energy-bfs-primitive-visited.py",
 "spark-topology-neighbor-position-reuse.py",
 "spark-energy-ticker-neighbor-position-reuse.py",
)

def apply(changes=None,repeat=False):
 with tempfile.TemporaryDirectory() as directory:
  base=Path(directory)/"dev/obsidiannetwork"
  for name,source in SOURCES.items():
   path=base/name
   path.parent.mkdir(parents=True,exist_ok=True)
   path.write_text((changes or {}).get(name,source))
  def execute(script):
   return subprocess.run([sys.executable,str(PATCH/script)],
     env=dict(os.environ,V1_SOURCE_ROOT=directory),capture_output=True,text=True)
  first=[execute(script) for script in SCRIPTS]
  second=[execute(script) for script in SCRIPTS] if repeat else []
  files={name:(base/name).read_text() for name in SOURCES}
  return first,second,files

class SparkEnergyBatch227Tests(unittest.TestCase):
 def test_all_three_hotpath_patches_preserve_transactions(self):
  runs,_,files=apply()
  self.assertTrue(all(run.returncode==0 for run in runs),str([run.stderr for run in runs]))
  cable=files["blockentity/EnergyCableBlockEntity.java"]
  self.assertEqual(cable.count("LongOpenHashSet visited"),3)
  self.assertEqual(cable.count("visited.add(next.asLong())"),3)
  self.assertEqual(cable.count("visited.add(EnergyCableBlockEntity.this.worldPosition.asLong())"),3)
  self.assertEqual(cable.count("queue.addLast(next);"),3)
  topology=files["conduit/ConduitTopology.java"]
  self.assertIn("network.containsPosition(neighborPos)",topology)
  self.assertIn("ConduitRuntime.bundle(level,neighborPos,type)",topology)
  self.assertIn("physicallyConnected!=cachedConnected",topology)
  ticker=files["conduit/EnergyConduitTicker.java"]
  self.assertIn("ConduitRuntime.bundle(level,neighborPos,ConduitType.ENERGY)",ticker)
  self.assertIn("getCapability(Capabilities.Energy.BLOCK,neighborPos,d.getOpposite())",ticker)
  for original in ("Transaction.openRoot()","from.extract(1000,tx)","to.insert(got,tx)","from.insert(got-put,tx)","tx.commit();return;"):
   self.assertIn(original,ticker)

 def test_multiple_independent_invalidation_sites_preserved(self):
  # Real reconstructed topology contains more than one network.nodeChanged(node).
  src=TOPOLOGY.replace(" void validate(){",
      " void unrelatedDirtySignal(){network.nodeChanged(node);}\n void validate(){")
  runs,_,files=apply({"conduit/ConduitTopology.java":src})
  self.assertTrue(all(run.returncode==0 for run in runs),str([run.stderr for run in runs]))
  topology=files["conduit/ConduitTopology.java"]
  self.assertEqual(topology.count("network.nodeChanged(node)"),2)
  self.assertIn("network.containsPosition(neighborPos)",topology)
  self.assertIn("physicallyConnected!=cachedConnected",topology)

 def test_reapplication_refused_for_all_patches(self):
  first,second,_=apply(repeat=True)
  self.assertTrue(all(run.returncode==0 for run in first))
  self.assertTrue(all(run.returncode!=0 for run in second))

 def test_changed_sources_fail_closed(self):
  cases=(
   ("blockentity/EnergyCableBlockEntity.java","visited.add(next)","visited.add(next.toImmutable())",0),
   ("conduit/ConduitTopology.java","network.containsPosition(bundle.getBlockPos().relative(d))","network.containsPosition(otherPos)",1),
   ("conduit/EnergyConduitTicker.java","to.insert(got,tx)","to.insert(0,tx)",2),
  )
  for filename,old,new,index in cases:
   broken=SOURCES[filename].replace(old,new,1)
   outputs,_,after=apply({filename:broken})
   self.assertNotEqual(outputs[index].returncode,0,filename)
   self.assertEqual(after[filename],broken)

 def test_10000_packed_position_equivalence_within_world_border(self):
  rng=random.Random(20261017)
  values=set()
  packed=set()
  def encoded(x,y,z):
   return ((x&0x3ffffff)<<38) | ((z&0x3ffffff)<<12) | (y&0xfff)
  for _ in range(10000):
   x=rng.randint(-30000000,30000000)
   y=rng.randint(-64,319)
   z=rng.randint(-30000000,30000000)
   p=(x,y,z)
   key=encoded(*p)
   self.assertEqual(p in values,key in packed)
   values.add(p)
   packed.add(key)

if __name__=="__main__":
 unittest.main()
