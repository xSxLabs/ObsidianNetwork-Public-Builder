"""Real Magnet UI: server-owned item filters and detached module controls."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/v176/apply-v176-backpack-magnet-gui-817.py").read_text("utf-8")
class Magnet817(unittest.TestCase):
 def test_source_is_real_bag_and_filter_is_ghost_item(self):
  for fragment in ("V176BackpackCells.magnet(", "V176BackpackCells.setMagnetFilter(",
                   "storage.source.save(next)", "player.getInventory().getItem(invIndex)"):
   self.assertIn(fragment,S)
  self.assertIn("filterIndex>=V176BackpackCells.FILTER_SLOTS",S)
 def test_54_ghost_filters_across_two_pages(self):
  for fragment in ("filterEditor", "filterPage*45+entry",
                   "networkbackpack setfilter", "networkbackpack clearfilter",
                   "networkbackpack filters"):
   self.assertIn(fragment,S)
 def test_magnet_controls(self):
  for fragment in ("networkbackpack magnet off", "networkbackpack magnet on",
                   "networkbackpack magnet blacklist","networkbackpack magnet whitelist"):
   self.assertIn(fragment,S)
 def test_no_crafting(self):
  self.assertNotIn("CraftingSlot",S)
  self.assertNotIn("craftingGrid",S)
 def test_order(self):
  w=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
  self.assertLess(w.index("python3 features/v176/apply-v176-backpack-list-816.py"),
                  w.index("python3 features/v176/apply-v176-backpack-magnet-gui-817.py"))
if __name__=="__main__":
 unittest.main()
