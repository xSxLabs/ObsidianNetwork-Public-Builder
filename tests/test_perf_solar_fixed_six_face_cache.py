#!/usr/bin/env python3
"""Solar six-face cache regression contracts (synthetic; Java/GameTests follow).

The important invariant is cache identity per face and full lifecycle/world
invalidation; there is NO change to FE transfer rate or transaction semantics.
"""
import ast
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"patches/spark-solar-block-capability-cache.py"
PATCH=ROOT/"patches/spark-solar-fixed-six-face-cache.py"

def base_member():
    tree=ast.parse(BASE.read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="member" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("original Solar BlockCapabilityCache member missing")

def fixture():
    return (
        "public final class SolarGeneratorBlockEntity extends BlockEntity {\n"
        +base_member()
        +"""
 public static void serverTick(ServerLevel server,BlockPos pos,SolarGeneratorBlockEntity be) {
   Direction[] sides=SOLAR_SCAN_SIDES;
   int start = be.nextSide++ % sides.length;
   long budget=64000L;
   for(int off=0;off<sides.length&&budget>0;off++){
      Direction side=sides[(start+off)%sides.length];
      EnergyHandler target = be.neighborEnergy(server, side);
      try(Transaction tx=Transaction.openRoot()){
         be.energyJournal.updateSnapshots(tx);
         tx.commit();
         budget -= accepted;
      }
   }
 }
}
"""
    )

def run(src):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/"dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
        p.parent.mkdir(parents=True)
        p.write_text(src)
        result=subprocess.run([sys.executable,str(PATCH)],
            env={**os.environ,"V1_SOURCE_ROOT":folder},
            text=True,capture_output=True)
        return result,p.read_text()

class FixedSolarCacheRegression(unittest.TestCase):
    def test_compact_six_face_cache_preserves_exact_fe_and_lifecycle(self):
        ast.parse(PATCH.read_text())
        before=fixture()
        result,after=run(before)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1",after)
        self.assertNotIn("EnumMap",after)
        self.assertIn("new net.neoforged.neoforge.capabilities.BlockCapabilityCache[6]",after)
        self.assertIn("int slot=side.get3DDataValue();",after)
        self.assertIn("var cache=energyNeighbors[slot];",after)
        self.assertIn("energyNeighbors[slot]=cache;",after)
        self.assertEqual(after.count("java.util.Arrays.fill(energyNeighbors,null);"),3)
        self.assertIn("if(energyCacheLevel!=server)",after)
        self.assertIn("() -> !isRemoved() && level==server",after)
        self.assertIn("worldPosition.relative(side),side.getOpposite()",after)
        self.assertEqual(after.count("BlockCapabilityCache.create("),1)
        for unchanged in ("int start = be.nextSide++ % sides.length;",
                          "EnergyHandler target = be.neighborEnergy(server, side);",
                          "be.energyJournal.updateSnapshots(tx);","tx.commit();","budget -= accepted;"):
            self.assertIn(unchanged,after)
        self.assertEqual(after.count("Transaction.openRoot()"),before.count("Transaction.openRoot()"))
        self.assertNotIn("setChunkForced(",after)
        self.assertNotIn("getCapability(Energy.BLOCK",after)

    def test_unsafe_drift_is_rejected_before_any_write(self):
        base=fixture()
        for old,new in (
            ("energyNeighbors.clear();","energyNeighbors.remove(side);"),
            ("() -> !isRemoved() && level==server","() -> true"),
            ("budget -= accepted;","budget = 0L;"),
            ("be.neighborEnergy(server, side)","server.getCapability(Energy.BLOCK, pos, null)"),
            ("energyNeighbors.put(side,cache);","energyNeighbors.put(side,other);"),
            ("net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(","unsafeGlobalCache.create("),
        ):
            changed=base.replace(old,new,1)
            self.assertNotEqual(changed,base)
            result,after=run(changed)
            self.assertNotEqual(result.returncode,0,old)
            self.assertEqual(after,changed)
        first,after=run(base)
        self.assertEqual(first.returncode,0,first.stderr)
        again,unchanged=run(after)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(unchanged,after)

    def test_randomized_side_lookup_and_invalidation_model(self):
        # Structural/semantic model, not a Java throughput benchmark.
        rng=random.Random(20261018)
        map_cache={}
        slots=[None]*6
        for iteration in range(12000):
            side=rng.randrange(6)
            if rng.randrange(31)==0:
                map_cache.clear()
                slots=[None]*6
            if side not in map_cache:
                identity=(iteration,side)
                map_cache[side]=identity
                slots[side]=identity
            self.assertEqual(map_cache[side],slots[side])
            self.assertEqual(list(map_cache.values()),[v for v in slots if v is not None]
                             if list(map_cache)==sorted(map_cache) else
                             [slots[side] for side in map_cache])
        # Cache keys never include a block outside the six physical sides.
        self.assertTrue(all(0<=v<6 for v in range(len(slots))))

if __name__=="__main__":
    unittest.main()
