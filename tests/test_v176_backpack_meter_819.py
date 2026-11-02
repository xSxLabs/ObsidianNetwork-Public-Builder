"""B819 keeps side-panel capacity/usage tied to real item contents."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Meter819(unittest.TestCase):
 def test_3_real_cells_no_extra_capacity(self):
  s=(ROOT/"features/v176/apply-v176-backpack-meter-819.py").read_text("utf-8")
  self.assertIn("for(int slot=1;slot<=3;slot++)",s)
  self.assertIn("cell.readStore(stack).used()",s)
  self.assertIn("cell.tier().capacity()",s)
  self.assertIn("now-xsxMeterTick>=10L",s)
 def test_magnet_state_visible(self):
  s=(ROOT/"features/v176/apply-v176-backpack-meter-819.py").read_text("utf-8")
  for expected in ("MAGNET: NONE","MAGNET: ON","MAGNET: OFF","WHITELIST","BLACKLIST"):
   self.assertIn(expected,s)
 def test_no_extra_crafting_ui(self):
  s=(ROOT/"features/v176/apply-v176-backpack-meter-819.py").read_text("utf-8")
  self.assertNotIn("CraftingMenu",s)
  self.assertNotIn("CraftingSlot",s)
if __name__=="__main__":
 unittest.main()
