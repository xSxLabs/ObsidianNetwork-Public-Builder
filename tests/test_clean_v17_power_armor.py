#!/usr/bin/env python3
"""New v1.7 must be clean and user old equipment always backed up."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-stage1.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class CleanV17Armor(unittest.TestCase):
 def test_real_python_syntax(self):ast.parse(PATCH)
 def test_new_only_and_no_legacy_generator(self):
  self.assertIn("apply-power-armor-stage1.py",WF)
  self.assertNotIn("private/v1.7/",WF)
  self.assertIn("branches: [v1.7]",WF)
 def test_backup_before_wear_or_removal(self):
  self.assertLess(PATCH.index("loadouts.save(p,old)"),PATCH.index("station.clear();"))
  self.assertIn("saved backup",PATCH)
  self.assertIn('Commands.literal("recover")',PATCH)
  self.assertIn("if(!p.getItemBySlot(slot).isEmpty())return false;",PATCH)
  self.assertIn("ItemStack.OPTIONAL_CODEC.listOf()",PATCH)
 def test_energy_and_four_pieces(self):
  for piece in ("helmet","chestplate","leggings","boots"):
   self.assertIn('("'+piece+'",',PATCH)
  self.assertIn('ITEMS.registerItem("power_armor_{name}"',PATCH)
  self.assertIn("ENERGY_TOOL_FE.get(),0L",PATCH)
  self.assertIn("EnergyTool.consume(",PATCH)
  self.assertIn("ARMOR_STATION",PATCH)
if __name__=="__main__":unittest.main()
