#!/usr/bin/env python3
"""Fail-closed source guards: user's exact reactor #3 and bank #4 selection."""
import ast
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"features/v174/apply-v174-reference-designs-553.py"
class DesignChoices(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=P.read_text(encoding="utf-8")
  ast.parse(cls.s)
 def test_design_selected_and_only_formed(self):
  s=self.s
  self.assertIn("B553_REACTOR_DESIGN_3",s)
  self.assertIn("B553_POWERBANK_DESIGN_4",s)
  self.assertIn('if "formed=false" in key:',s)
  self.assertIn('assert len(variants)==24',s)
  self.assertIn("design3",s)
  self.assertIn("design4",s)
 def test_real_y_bands_with_no_per_tick_render(self):
  s=self.s
  self.assertIn("B553_ON_FORM_VISUAL_BANDS",s)
  self.assertIn("p.getY()==low?1:p.getY()==high?2:0",s)
  self.assertIn("if(!queue.isEmpty()||high<=low)return;",s)
  self.assertIn("state.setValue(RIM,band)",s)
  self.assertNotIn("animateTick",s)
  self.assertNotIn("new BlockEntityRenderer",s)
 def test_bank_casing_lit_actually_changes(self):
  s=self.s
  self.assertIn("bank&&state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_CASING.get())",s)
  self.assertIn('suffix="_lit" if',s)
  self.assertIn("bank_face",s)
 def test_original_lit_and_unformed_still_supported(self):
  s=self.s
  self.assertIn('builder.add(FORMED,ACTIVE,LIT,RIM);',s)
  self.assertIn('for name in ("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass")',s)
if __name__=="__main__":
 unittest.main()
