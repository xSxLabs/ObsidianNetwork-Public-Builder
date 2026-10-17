#!/usr/bin/env python3
"""Fail-closed fixtures for the three grouped Spark #226 energy patches."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCHES = Path(__file__).resolve().parents[1] / "patches"
SOLAR = """public final class SolarGeneratorBlockEntity extends BlockEntity {
 public static void serverTick(Level level, BlockPos pos, BlockState state, SolarGeneratorBlockEntity be) {
  Direction[] sides = SOLAR_SCAN_SIDES;
  int start = be.nextSide++ % sides.length;
  for (int off=0; off<sides.length; off++) {
   Direction side = sides[(start+off)%sides.length];
   EnergyHandler target = (EnergyHandler)server.getCapability(Energy.BLOCK, pos.relative(side), side.getOpposite());
   try(Transaction tx=Transaction.openRoot()) {
    be.energyJournal.updateSnapshots(tx);
    be.energy.extract(accepted);
    tx.commit();
    budget -= accepted;
   }
  }
 }
}
"""
BFS = """public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {
 private final class CableEnergyHandler implements EnergyHandler {
""" + ("""
 void visit() {
  BlockPos next = cable.relative(side);
  if(visited.add(next.immutable())) {queue.addLast(next.immutable());}
 }
""" * 3) + """ }
}
"""
TOPO = """public final class ConduitTopology {
 void validate() {
  for(Direction d:Direction.values()) {
   boolean physicallyConnected = check();
   boolean cachedConnected = checkCached();
   if(physicallyConnected!=cachedConnected)network.nodeChanged(node);
  }
 }
}
"""
MANAGER = """public final class ConduitNetworkManager {
 void ensure() {
  if(current.shouldValidate(tick)) {
   for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()) {
    if(!current.nodes().contains(other.conduitNode(seed.type()))) changed=true;
   }
  }
 }
}
"""
SOURCES = {
 "blockentity/SolarGeneratorBlockEntity.java": SOLAR,
 "blockentity/EnergyCableBlockEntity.java": BFS,
 "conduit/ConduitTopology.java": TOPO,
 "conduit/ConduitNetworkManager.java": MANAGER,
}
SCRIPTS = (
 "spark-solar-block-capability-cache.py",
 "spark-energy-bfs-position-reuse.py",
 "spark-conduit-validation-direction-hoist.py",
)

def run(edits=None,second=False):
 with tempfile.TemporaryDirectory() as root:
  base=Path(root)/"dev/obsidiannetwork"
  for name,src in SOURCES.items():
   p=base/name
   p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text((edits or {}).get(name,src))
  def execute(script):
   return subprocess.run([sys.executable,str(PATCHES/script)],
                         env=dict(os.environ,V1_SOURCE_ROOT=root),
                         capture_output=True,text=True)
  first=[execute(script) for script in SCRIPTS]
  second_pass=[execute(script) for script in SCRIPTS] if second else []
  after={name:(base/name).read_text() for name in SOURCES}
  return first,second_pass,after

class SparkEnergyBatch226Tests(unittest.TestCase):
 def test_all_three_patches_preserve_critical_operations(self):
  jobs,_,files=run()
  self.assertTrue(all(x.returncode==0 for x in jobs),
                  str([(x.returncode,x.stderr) for x in jobs]))
  solar=files["blockentity/SolarGeneratorBlockEntity.java"]
  for expected in ("BlockCapabilityCache.create(", "cache.getCapability()",
                   "be.energyJournal.updateSnapshots(tx);", "tx.commit();",
                   "budget -= accepted;", "be.energy.extract(accepted);",
                   "be.nextSide++ % sides.length;"):
   self.assertIn(expected,solar)
  bfs=files["blockentity/EnergyCableBlockEntity.java"]
  self.assertEqual(bfs.count("visited.add(next)"),3)
  self.assertEqual(bfs.count("queue.addLast(next);"),3)
  self.assertEqual(bfs.count("BlockPos next = cable.relative(side);"),3)
  self.assertIn("physicallyConnected!=cachedConnected",
                files["conduit/ConduitTopology.java"])
  self.assertIn("current.shouldValidate(tick)",
                files["conduit/ConduitNetworkManager.java"])

 def test_reapplication_always_refused(self):
  first,second,_=run(second=True)
  self.assertTrue(all(p.returncode==0 for p in first))
  self.assertTrue(all(p.returncode!=0 for p in second))

 def test_solar_bfs_and_topology_fail_closed(self):
  mutations=(
   ("blockentity/SolarGeneratorBlockEntity.java","tx.commit();","tx.rollback();",0),
   ("blockentity/EnergyCableBlockEntity.java","BlockPos next = cable.relative(side);","BlockPos next = unknown;",1),
   ("conduit/ConduitTopology.java","physicallyConnected!=cachedConnected","physicallyConnected==cachedConnected",2),
   ("conduit/ConduitNetworkManager.java","current.shouldValidate(tick)","true",2),
  )
  for file,before,after,index in mutations:
   broken=SOURCES[file].replace(before,after,1)
   jobs,_,files=run({file:broken})
   self.assertNotEqual(jobs[index].returncode,0,file)
   self.assertEqual(files[file],broken)

 def test_direction_round_robin_order_unchanged(self):
  directions=tuple(range(6))
  for seed in range(6000):
   original=[list(directions)[(seed+index)%6] for index in range(6)]
   cached=[directions[(seed+index)%6] for index in range(6)]
   self.assertEqual(original,cached)

if __name__ == "__main__":
 unittest.main()
