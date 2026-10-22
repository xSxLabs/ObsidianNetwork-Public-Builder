#!/usr/bin/env python3
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-cards.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class CleanV17Cards(unittest.TestCase):
 def test_valid_python(self):ast.parse(PATCH)
 def test_modules_and_safety(self):
  self.assertIn('protection',PATCH)
  self.assertIn('water_breathing',PATCH)
  self.assertIn('fire_protection',PATCH)
  self.assertIn('night_vision',PATCH)
  self.assertIn('POWER_ARMOR_UPGRADES',PATCH)
  self.assertIn('OWNED_FLIGHT',PATCH)
  self.assertIn('POWER_CARD_',PATCH)
  self.assertIn('PowerArmorExitKeyClient',PATCH)
 def test_unique_crafting_inputs_and_safe_return(self):
  self.assertIn("assert set(ingredients)==set(cards)",PATCH)
  self.assertIn("ingredients[card]",PATCH)
  self.assertIn("inventory full; upgrade retained.",PATCH)
  self.assertLess(PATCH.index("p.getInventory().add(new ItemStack(cardItem))"),PATCH.index("left.remove(i)"))
 def test_workflow(self):
  self.assertIn("python3 features/v17/apply-power-armor-cards.py",WF)
  self.assertLess(WF.index("apply-power-armor-stage1.py"),WF.index("apply-power-armor-cards.py"))
if __name__=="__main__":unittest.main()
