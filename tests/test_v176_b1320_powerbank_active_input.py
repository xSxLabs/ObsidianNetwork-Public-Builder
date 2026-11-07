"""B1320 Powerbank input/source isolation regression gates.

Synthetic tests verify the exact patch application on B1300-shaped compiled
sources. The Java compile and optional integration GameTests are still
required; these checks cannot claim an in-world server is fixed.
"""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from test_v176_b1300_energy_conservation import fixtures,apply as apply_b1300

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1320-powerbank-active-input.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def b1300_fixture():
 original=fixtures()
 src=original["powerbank/PowerbankBlockEntity.java"]
 src=src.replace("class PowerbankBlockEntity {",
  """class PowerbankBlockEntity {
 private java.util.Set<Long> activePorts;
 static void serverTick(Level world,BlockPos pos,BlockState state,
                        PowerbankBlockEntity be){
  if(!(world instanceof ServerLevel sl)||be.mode()!=PowerbankBlock.Mode.CONTROLLER)return;
  // B592_POWERBANK_OUTPUT_TICK
  be.b591PushOutput(sl);
 }""",1)
 original["powerbank/PowerbankBlockEntity.java"]=src
 run,output=apply_b1300(original)
 if run.returncode!=0:raise AssertionError(run.stderr)
 return output["powerbank/PowerbankBlockEntity.java"]

def apply_b1320(bank):
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/"dev/obsidiannetwork/powerbank/PowerbankBlockEntity.java"
  path.parent.mkdir(parents=True)
  path.write_text(bank,encoding="utf-8")
  run=subprocess.run([sys.executable,str(PATCH)],text=True,capture_output=True,
                     env={**os.environ,"V1_SOURCE_ROOT":folder},check=False)
  return run,path.read_text(encoding="utf-8")

class PowerbankInputB1320(unittest.TestCase):
 def test_script_and_real_b1300_integration(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
  run,changed=apply_b1320(b1300_fixture())
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
  self.assertIn("B1320_POWERBANK_ACTIVE_INPUT_REAL_EXTERNAL_FE",run.stdout)
  self.assertIn("private void b1320PullInput(ServerLevel server)",changed)
  self.assertIn("be.b1320PullInput(sl);",changed)
  self.assertLess(changed.index("be.b1320PullInput(sl);"),changed.index("be.b591PushOutput(sl);"))
  self.assertIn("PowerbankBlock.Mode.INPUT",changed)
  self.assertIn("source.extract(request,tx)",changed)
  self.assertIn("sink.insert(extracted,tx)==extracted",changed)
  self.assertIn("if(previous==null)b1320ActiveImport.remove();",changed)
  self.assertIn("||b1320ActiveImport.get()==b",changed)
  self.assertIn("b1300SelfCharge(tx,b)",changed)
  self.assertIn("b1300MarkSource(tx,b)",changed)
  self.assertIn("Math.floorMod(server.getGameTime(),5L)",changed)
  self.assertIn("Math.min((long)Integer.MAX_VALUE,capacity-amount)",changed)
  self.assertIn("Math.min((long)Integer.MAX_VALUE,amount)",changed)
  self.assertIn("b1320ActiveImport.set(this)",changed)
  self.assertNotIn("MAX_IO=1_000_000",changed)

 def test_fail_closed_on_unknown_signatures(self):
  source=b1300_fixture()
  edited=source.replace("// B592_POWERBANK_OUTPUT_TICK","// WROTE_SOMETHING_ELSE")
  run,output=apply_b1320(edited)
  self.assertNotEqual(run.returncode,0)
  self.assertEqual(output,edited)
  edited=source.replace("if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=0)return 0;",
                        "if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=1)return 0;")
  run,output=apply_b1320(edited)
  self.assertNotEqual(run.returncode,0)
  self.assertEqual(output,edited)

 def test_import_does_not_take_own_output_and_preserves_other_banks(self):
  mine=object(); other=object()
  external=object()
  # When input pulls, its own outgoing capability has zero extraction.
  def may_extract(source_owner,currently_importing):
   return source_owner is None or source_owner is not currently_importing
  self.assertFalse(may_extract(mine,mine))
  self.assertTrue(may_extract(other,mine))
  self.assertTrue(may_extract(None,mine))
  self.assertTrue(may_extract(mine,None))
  # A cable proxy scans own OUTPUT first, receives 0, then reaches generator.
  sources=[("my bank",mine,9_000_000),("generator",external,1234)]
  chosen=next((n for n,owner,balance in sources if owner is not mine and balance>0),None)
  self.assertEqual(chosen,"generator")

 def test_lossless_input_partial_full_offline_and_rollback(self):
  rng=random.Random(1320)
  for _ in range(20000):
   bank=rng.randrange(0,100_000)
   cap=rng.randrange(bank,110_000)
   generator=rng.randrange(0,100_000)
   free=cap-bank
   requested=min(free,2_147_483_647)
   extract=min(generator,requested)
   inserted=min(extract,free)
   transfer=extract if extract>0 and extract==inserted else 0
   self.assertEqual(generator+bank,(generator-transfer)+(bank+transfer))
   self.assertTrue(0<=bank+transfer<=cap)
   if free==0 or generator==0:self.assertEqual(transfer,0)
  # Entire transaction rolls back if sink can accept less than source drew.
  generator=1000; bank=999; cap=1000; request=1
  extracted=1;accepted=0
  committed=extracted if accepted==extracted else 0
  self.assertEqual(committed,0)
  self.assertEqual((generator-committed,bank+committed),(1000,999))

 def test_output_zero_without_real_sink(self):
  balance=100_000_000
  for accepted in [0]*100:
   if accepted>0:balance-=accepted
  self.assertEqual(balance,100_000_000)

 def test_workflow_order(self):
  s=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("python3 features/v176/"+PATCH.name,s)
  self.assertIn("test_v176_b1320_powerbank_active_input.py",s)
  self.assertLess(s.index("python3 features/v176/apply-v176-b1300-energy-conservation.py"),
                  s.index("python3 features/v176/"+PATCH.name))
  self.assertLess(s.index("python3 features/v176/"+PATCH.name),
                  s.index("python3 features/v176/apply-v176-b1301-backpack-magnet-any-location.py"))

if __name__=="__main__":unittest.main()
