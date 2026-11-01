#!/usr/bin/env python3
"""B745 regression: patch the real pre-B745 anchors in a synthetic Java file."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-upper-arm-deployment-745.py"

def phase(progress,begin,end):
 return max(0.0,min(1.0,(progress-begin)/(end-begin)))

class UpperArmDeploy745(unittest.TestCase):
 def test_right_upper_arm_geometry_and_sequence(self):
  source=PATCH.read_text(encoding="utf-8")
  tree=ast.parse(source)
  edits=[node.value for node in tree.body
   if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
   and isinstance(node.value.func,ast.Name) and node.value.func.id=="edit"]
  self.assertEqual(len(edits),11,"Unexpected changed B745 patch contracts")
  olds=[ast.literal_eval(node.args[0]) for node in edits]
  self.assertEqual(len(olds),len(set(olds)),"Overlapping anchor strings")
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/"dev/obsidiannetwork/client"
   root.mkdir(parents=True)
   target=root/"V176MicroMgVisualClient.java"
   target.write_text("\n".join(olds),encoding="utf-8")
   env={**os.environ,"V1_SOURCE_ROOT":td}
   run=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   patched=target.read_text(encoding="utf-8")
   self.assertIn("V176_B745",run.stdout)
   self.assertIn(".addBox(-0.55F,3.3F,-3.40F",patched)
   self.assertIn(".addBox(-1.25F,3.1F,-3.05F",patched)
   self.assertNotIn(".addBox(-0.65F,6.0F,-3.55F",patched)
   self.assertNotIn(".addBox(-1.35F,6.0F,-3.05F",patched)
   self.assertIn("phase(extension,4.0F/12.0F,7.0F/12.0F)",patched)
   self.assertIn("phase(extension,7.0F/12.0F,1.0F)",patched)
   self.assertIn("amount,false",patched)
   self.assertIn("amount,true",patched)
   self.assertNotIn("model.leftArm",patched)
   self.assertNotIn("forearm surface",patched)
   # Fail closed on a second accidental patch invocation.
   repeat=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(repeat.returncode,0)

 def test_12_tick_arm_hatch_barrel_order_and_reverse(self):
  for tick in range(13):
   progress=tick/12
   arm=phase(progress,0,4/12)
   hatch=phase(progress,4/12,7/12)
   gun=phase(progress,7/12,1)
   if tick<=4:self.assertEqual(hatch,0)
   if tick<=7:self.assertEqual(gun,0)
   if gun>0:self.assertEqual(arm,1)
   if gun>0:self.assertEqual(hatch,1)
  self.assertEqual(phase(1,7/12,1),1)
  # Reversing progress retracts the muzzle before the lid shuts, then lowers arm.
  self.assertEqual(phase(7/12,7/12,1),0)
  self.assertEqual(phase(4/12,4/12,7/12),0)
  self.assertEqual(phase(0,0,4/12),0)

if __name__=="__main__":unittest.main()
