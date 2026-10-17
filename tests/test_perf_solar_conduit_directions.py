#!/usr/bin/env python3
"""Source invariants and fail-closed tests for Spark hot-path Direction clones."""
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCH = Path(__file__).resolve().parents[1] / "patches/spark-solar-conduit-direction-arrays.py"
ROOT = "dev/obsidiannetwork/"
SOLAR = """public final class SolarGeneratorBlockEntity extends BlockEntity {
 public static void serverTick(Level level,BlockPos pos,BlockState state,SolarGeneratorBlockEntity be){
  if(!server.canSeeSky(pos.above())) return;
  long budget=5;
  Direction[] sides = Direction.values();
  int start = be.nextSide++ % sides.length;
  for(int off=0;off<sides.length&&budget>0L;off++){
   Direction side = sides[(start + off) % sides.length];
   EnergyHandler target=(EnergyHandler)server.getCapability(Energy.BLOCK, pos.relative(side), side.getOpposite());
   try(Transaction tx=Transaction.openRoot()){
    be.energyJournal.updateSnapshots(tx);
    tx.commit();budget -= accepted;
   }
  }
 }
}
"""
CONDUIT = """public final class EnergyConduitTicker implements ConduitTicker {
 public void tick(ServerLevel level,ConduitNetwork network){
  for(var node:network.nodes()){
   for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()){
    if(connected.size()<2)return;
    try(Transaction tx=Transaction.openRoot()){
     int got=from.extract(1000,tx);
     int put=to.insert(got,tx);
     from.insert(got-put,tx);tx.commit();return;
    }
   }
  }
 }
}
"""

def apply(s=SOLAR,c=CONDUIT):
    with tempfile.TemporaryDirectory() as d:
        sr=Path(d)/ROOT/"blockentity/SolarGeneratorBlockEntity.java"
        cr=Path(d)/ROOT/"conduit/EnergyConduitTicker.java"
        sr.parent.mkdir(parents=True);cr.parent.mkdir(parents=True)
        sr.write_text(s);cr.write_text(c)
        result=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=d),capture_output=True,text=True)
        return result,sr.read_text(),cr.read_text()

class SparkDirectionArraysTests(unittest.TestCase):
    def test_batch_preserves_fe_and_round_robin(self):
        r,s,c=apply()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("Direction[] sides = SOLAR_SCAN_SIDES;",s)
        self.assertIn("for(net.minecraft.core.Direction d:CONDUIT_SCAN_SIDES)",c)
        self.assertEqual(s.count("Direction.values()"),1)
        self.assertEqual(c.count("net.minecraft.core.Direction.values()"),1)
        for value in ("int start = be.nextSide++ % sides.length;", "Direction side = sides[(start + off) % sides.length];", "server.getCapability(Energy.BLOCK, pos.relative(side), side.getOpposite())", "be.energyJournal.updateSnapshots(tx);", "budget -= accepted;"):
            self.assertIn(value,s)
        for value in ("from.extract(1000,tx)","to.insert(got,tx)","from.insert(got-put,tx)","tx.commit();return;"):
            self.assertIn(value,c)

    def test_fail_closed_batch_atomicity_and_idempotence(self):
        for s,c in (
            (SOLAR.replace("budget -= accepted;","budget = 0;"),CONDUIT),
            (SOLAR,CONDUIT.replace("to.insert(got,tx)","to.insert(0,tx)")),
            (SOLAR.replace("Direction[] sides = Direction.values();","Direction[] sides = ALL_SIDES;"),CONDUIT),
            (SOLAR,CONDUIT.replace("for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values())","for(Direction d:ALL_SIDES)")),
        ):
            result,after_s,after_c=apply(s,c)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual((after_s,after_c),(s,c))
        good,s,c=apply()
        self.assertEqual(good.returncode,0,good.stderr)
        again,after_s,after_c=apply(s,c)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual((after_s,after_c),(s,c))

    def test_10000_rotation_and_direction_order_cases(self):
        rng=random.Random(20261017)
        values=tuple(range(6))
        # Enum.values() returns a new array with exactly the same enum objects
        # in the same order as the private static array.
        for _ in range(10000):
            start=rng.randrange(0,2**31)
            count=rng.randrange(0,7)
            old=[list(values)[(start+i)%6] for i in range(count)]
            new=[values[(start+i)%6] for i in range(count)]
            self.assertEqual(old,new)

if __name__=="__main__":unittest.main()
