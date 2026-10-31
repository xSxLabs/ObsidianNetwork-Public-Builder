#!/usr/bin/env python3
"""B552 independent gates for half-scale HUD and non-ticking joined machine skins."""
import ast
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"features/v174/apply-v174-ingame-552.py"
class B552VisualFixes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=P.read_text(encoding="utf-8")
  ast.parse(cls.s)
 def test_real_half_size_and_lower_both_meters(self):
  s=self.s
  self.assertIn("g.pose().scale(.5f,.5f);",s)
  self.assertEqual(s.count("g.pose().scale(.5f,.5f);"),3)
  self.assertIn("B552_HUD_FE_LOWER",s)
  self.assertIn("B552_HUD_PASTE_LOWER",s)
  self.assertIn("getGuiScaledHeight()-14",s)
  self.assertIn("getGuiScaledHeight()-28",s)
  self.assertIn("int width=60",s)
  self.assertIn("int pasteWidth=60",s)
 def test_solid_collar_six_faces_no_energy_changes(self):
  s=self.s
  self.assertIn("XSX_ENERGY_INPUT_COLLAR",s)
  self.assertIn("minecraft:block/cube_all",s)
  self.assertIn("B552_SOLID_CABLE_COLORED_INPUT_COLLAR",s)
  self.assertIn('renderer="client/EnergyCableInputRenderer.java"',s)
  self.assertIn("source_png",s)
  self.assertIn("B552_NO_REAL_ENERGY_CABLE_PALETTE",s)
  self.assertEqual(s.count("10/16f,10/16f"),4)
  self.assertIn("noLootTable()",s)
  self.assertNotIn("setTicker",s)
  self.assertNotIn("tx.commit()",s)
 def test_assembled_faces_only_and_no_new_ticks(self):
  s=self.s
  for tex in ("reactor_casing_formed","powerbank_casing_formed_lit",
              "reactor_casing_formed_top","powerbank_casing_formed_lit_top"):
   self.assertIn(tex,s)
  self.assertIn("B552_FORMED_VARIANTS",s)
  self.assertIn("len(variants)==8",s)
  self.assertNotIn("getGameTime",s)
  self.assertNotIn("level.getBlockState",s)
if __name__=="__main__":
 unittest.main()
