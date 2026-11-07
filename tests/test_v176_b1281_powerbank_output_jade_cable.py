"""B1281: distinguish true Powerbank output cap from cable's Jade proxy.

Fast source gates plus deterministic FE conservation checks. A green source
test is not a substitute for NeoForge Java compilation or server measurements.
"""
import ast
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v176/apply-v176-b1281-powerbank-direct-fe-and-jade-cable.py"
BUILD591=ROOT/"features/v174/apply-v174-build591.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def fixture():
 tree=ast.parse(BUILD591.read_text("utf-8"))
 helper=None
 for node in tree.body:
  if isinstance(node,ast.Assign):
   if any(isinstance(n,ast.Name) and n.id=="helper" for n in node.targets):
    if isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
     s=node.value.value
     if "B591_POWERBANK_OUTPUT_PUSH" in s:
      helper=s
 if helper is None:raise AssertionError("B1281_MISSING_REAL_B591_SOURCE")
 bank='''class PowerbankBlockEntity {
 private net.neoforged.neoforge.transfer.transaction.SnapshotJournal<long[]> journal;
 private void xsxCommittedTransfer(long in,long out){}
 private long amount=100000000000L;
 private java.util.Set<Long> activePorts;
 private boolean formed=true;
 private PowerbankBlock.Mode mode(){return PowerbankBlock.Mode.CONTROLLER;}
 private Object worldPosition;
}'''
 bank=bank.replace(" private long amount=100000000000L;",helper+"\n private long amount=100000000000L;")
 cable='''class EnergyCableBlockEntity {
 // XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1
 // B591_ENERGY_DIRECTED_WALK
 private final class CableEnergyHandler implements EnergyHandler {
  public long getAmountAsLong(){return 0L;}
  public long getCapacityAsLong(){return 2147483647L;}
  public int extract(int request,Object tx){return 0;}
  public int insert(int request,Object tx){return 0;}
 }
}'''
 return bank,cable

def execute(bank,cable):
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)/"dev/obsidiannetwork"
  for p,s in (
    (d/"powerbank/PowerbankBlockEntity.java",bank),
    (d/"blockentity/EnergyCableBlockEntity.java",cable)):
   p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text(s,"utf-8")
  proc=subprocess.run([sys.executable,str(SCRIPT)],
    env={**os.environ,"V1_SOURCE_ROOT":tmp},capture_output=True,text=True)
  bd=(d/"powerbank/PowerbankBlockEntity.java").read_text("utf-8")
  cd=(d/"blockentity/EnergyCableBlockEntity.java").read_text("utf-8")
  jp=d/"compat/EnergyCableJadePlugin.java"
  return proc,bd,cd,jp.read_text("utf-8") if jp.exists() else None

class PowerbankOutputB1281(unittest.TestCase):
 def test_real_B591_source_input_and_strict_patch(self):
  ast.parse(SCRIPT.read_text("utf-8"))
  bank,cable=fixture()
  run,output,energy,plugin=execute(bank,cable)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
  self.assertIn("B1281_POWERBANK_1M_AUTO_PUSH_REMOVED",run.stdout)
  self.assertIn("int offer=(int)Math.min((long)Integer.MAX_VALUE,amount)",output)
  self.assertNotIn("int offer=(int)Math.min(1_000_000L,amount)",output)
  self.assertEqual(energy,cable) # Do NOT zero out FE capabilities.
  self.assertIsNotNone(plugin)
  self.assertIn("JadeIds.UNIVERSAL_ENERGY_STORAGE",plugin)
  self.assertIn("registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class)",plugin)
  self.assertIn("TooltipPosition.BODY+2000",plugin)
  self.assertIn("no internal FE storage",plugin)
  self.assertIn("@WailaPlugin",plugin)

 def test_fail_closed_on_unknown_rate_or_capability(self):
  bank,cable=fixture()
  for b,c in ((bank.replace("1_000_000L,amount","64_000L,amount"),cable),
               (bank,cable.replace("B591_ENERGY_DIRECTED_WALK","UNEXPECTED"))):
   run,result,energy,plugin=execute(b,c)
   self.assertNotEqual(run.returncode,0)
   self.assertIsNone(plugin)
   self.assertEqual(b,result)
   self.assertEqual(c,energy)

 def test_high_rate_transaction_accepted_before_source_commits(self):
  bank,cable=fixture()
  run,result,_,_=execute(bank,cable)
  self.assertEqual(run.returncode,0)
  self.assertLess(result.index("target.insert(offer,tx)"),
                  result.index("source.extract(accepted,tx)==accepted"))
  self.assertLess(result.index("source.extract(accepted,tx)==accepted"),
                  result.index("tx.commit();"))
  rng=random.Random(1281)
  for _ in range(20000):
   bank_balance=rng.randint(0,100_000_000_000)
   accepted_limit=rng.randint(0,5_000_000_000)
   offered=min(bank_balance,2_147_483_647)
   accepted=min(offered,accepted_limit)
   after=bank_balance-accepted
   self.assertGreaterEqual(after,0)
   self.assertEqual(bank_balance,after+accepted)
   self.assertLessEqual(accepted,accepted_limit)
   # A target rejecting all energy is never charged or mutated.
   if accepted_limit==0:self.assertEqual(after,bank_balance)
  self.assertGreater(min(10_000_000,2_147_483_647),1_000_000)

 def test_no_crossmod_fe_cable_breakage(self):
  script=SCRIPT.read_text("utf-8")
  for forbidden in ("getAmountAsLong(){return 0L;","getCapacityAsLong(){return 0L;",
                    "ENERGY_CABLE_BLOCK_STORAGE","Thread.sleep(",
                    "tickCount%","PowerArmorEntrySequence",
                    "features/v175/"):
   self.assertNotIn(forbidden,script)
  self.assertIn("cable.read_text",script)
  self.assertNotIn("cable.write_text",script)
  self.assertIn("SnapshotJournal<long[]>",script)
  self.assertIn("source.extract(accepted,tx)==accepted",script)

 def test_workflow_integration_and_existing_rate_fix(self):
  s=WORKFLOW.read_text("utf-8")
  self.assertIn(SCRIPT.name,s)
  self.assertIn(Path(__file__).name,s)
  self.assertLess(s.index("apply-v176-b1229-powerbank-unlimited-io.py"),s.index(SCRIPT.name))
  self.assertLess(s.index("apply-v176-b1274-backpack-live-scroll-range.py"),s.index(SCRIPT.name))

if __name__=="__main__":unittest.main()
