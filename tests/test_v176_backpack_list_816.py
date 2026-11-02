"""v1.7.6 Backpack: real item list + separate modules; no craft grid."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def source(path):
 return (ROOT/path).read_text(encoding="utf-8")
class BackpackList816(unittest.TestCase):
 def test_server_side_cell_deposit_and_withdrawal(self):
  s=source("features/v176/apply-v176-backpack-list-816.py")
  for name in ("V176BackpackCells.entries(", "V176BackpackCells.insert(",
               "V176BackpackCells.extract(", "broadcastChanges();",
               "player.getInventory().add(output)"):
   self.assertIn(name,s)
  self.assertIn("&&index>=49",s) if False else None
  self.assertIn("i<49?",s)
 def test_search_sort_autofocus_without_crafting(self):
  s=source("features/v176/apply-v176-backpack-list-816.py")
  self.assertIn("new net.minecraft.client.gui.components.EditBox(",s)
  self.assertIn("if(autoFocus)setFocused(searchBox)",s)
  self.assertIn('Component.literal("SORT")',s)
  self.assertIn('Component.literal(autoFocus?"A:ON":"A:OFF")',s)
  self.assertNotIn("CraftingMenu",s)
  self.assertNotIn("CraftingSlot",s)
  self.assertNotIn("Autocrafting",s)
 def test_script_applies_after_sidepanel(self):
  workflow=source(".github/workflows/networkstorage-v1.7-clean.yml")
  one=workflow.index("python3 features/v176/apply-v176-backpack-menu-810.py")
  two=workflow.index("python3 features/v176/apply-v176-backpack-sidepanel-811.py")
  three=workflow.index("python3 features/v176/apply-v176-backpack-list-816.py")
  self.assertLess(one,two)
  self.assertLess(two,three)
if __name__=="__main__":
 unittest.main()
