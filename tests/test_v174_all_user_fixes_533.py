#!/usr/bin/env python3
"""B533 prebuild source gates, including safety and historical model regression."""
from pathlib import Path
import ast
import unittest
ROOT=Path(__file__).resolve().parents[1]
class FullIngameFixTest(unittest.TestCase):
 def test_patches_parse_and_keep_all_fixes(self):
  mechanic=(ROOT/"features/v174/apply-v174-final-fixes-533.py").read_text()
  assets=(ROOT/"features/v174/apply-v174-assets-533.py").read_text()
  for source in (mechanic,assets):ast.parse(source)
  for marker in (
   "B533_NUTRIPASTE_ARMOR_ROW","B533_HELMET_PASTE_TOOLTIP",
   "B533_NUTRINATOR_TANK_LIVE_FILL","B533_NETWORK_TANK_HELMET_FILL",
   "B533_NETWORK_TANK_HELMET_SLOT","B533_NETWORK_TANK_AUTOFILL_TICK",
   "B533_ACTUAL_ENERGY_CABLE_CAP_TEXTURE"):
   self.assertIn(marker,mechanic,marker)
  for marker in ("B533_BROWN_NUTRIPASTE_FLUID","powerbank_casing_formed_lit",
                 "nutripaste_flowing","nutripaste_still","reactor_casing_formed"):
   self.assertIn(marker,assets,marker)
 def test_tank_is_conservation_gated(self):
  source=(ROOT/"features/v174/apply-v174-final-fixes-533.py").read_text()
  self.assertIn("NutriPaste.add(stack,drained.getAmount())",source)
  self.assertIn("fluid.drain(offer",source)
  self.assertIn("if(inserted<drained.getAmount())",source)
  self.assertIn('out.store("xsxTankHelmet"',source)
  self.assertIn('in.read("xsxTankHelmet"',source)
 def test_dynamic_model_variant_combination(self):
  source=(ROOT/"features/v174/apply-v174-assets-533.py").read_text()
  self.assertIn('len(d["variants"])==8',source)
  self.assertIn('f"formed=true,active={active},lit=true"',source)
if __name__=="__main__":unittest.main()
