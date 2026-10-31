#!/usr/bin/env python3
"""B558 fail-closed performance and reference-visual patch preflight."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v174/apply-v174-reference-accuracy-558.py"
class VisualRegression(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=SCRIPT.read_text(encoding="utf-8")
  ast.parse(cls.s)
 def test_exact_user_design_selection(self):
  s=self.s
  for x in ("reactor_panel","reactor_corner","bank_panel","bank_corner",
            "powerbank_glass_formed_lit_detail","B558_REACTOR_MIXED_PANELS",
            "B558_EXACT_REFERENCE_FAMILIES_REACTOR_3_POWERBANK_4"):
   self.assertIn(x,s)
  self.assertIn("for detail in range(3)",s)
 def test_no_new_server_work_per_tick(self):
  s=self.s
  self.assertIn("B558_ONLY_ON_ASSEMBLY",s)
  self.assertIn("Math.floorMod(p.getX()*11+p.getZ()*7,3)",s)
  self.assertIn("Math.floorMod((p.getX()-minX)+(p.getZ()-minZ),3)",s)
  self.assertNotIn("animateTick",s)
  self.assertNotIn("new BlockEntityRenderer",s)
  self.assertNotIn("getGameTime",s)
  self.assertNotIn("source.extract",s)
 def test_model_compatibility(self):
  s=self.s
  self.assertIn("assert len(data[\"variants\"])==48",s)
  self.assertIn("assert len(new)==144",s)
  self.assertIn("B558_UNASSEMBLED_SKIN_CHANGED",s)
if __name__=="__main__":
 unittest.main()
