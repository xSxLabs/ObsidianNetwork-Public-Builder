#!/usr/bin/env python3
"""Build103 contract checks: all 96 suit pieces need a genuine FE cell."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v17/apply-power-armor-expensive-recipes-103.py"
SOURCE=PATCH.read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ExpensivePowerArmorRecipes(unittest.TestCase):
 def test_valid_patch(self):
  ast.parse(SOURCE,filename=str(PATCH))
 def test_energy_cell_is_real_mod_item_and_every_piece_needs_it(self):
  for key in (
   'CELL="obsidiannetwork:basic_energy_cell"',
   '"pattern":["ANA","BCB","DEF"]',
   '"N":CELL',
   'assert len(armor_signatures)==96',
   'sum(obj["key"].get(ch)==CELL for row in obj["pattern"] for ch in row)==1',
   '"minecraft:diamond_block"',
   '"minecraft:netherite_ingot"',
   '"minecraft:"+netherite_item',
   'len(set(dye_pairs.values()))==24',
  ):self.assertIn(key,SOURCE)
 def test_all_upgrade_recipes_more_expensive(self):
  for key in (
   'write_recipe("power_armor_upgrade"',
   '"pattern":["IRI","NCN","IRI"]',
   '"minecraft:copper_block"',
   '"pattern":["ABA","CDC","AEA"]',
   '"minecraft:nether_star" if rare',
   '"minecraft:iron_block"',
   '"minecraft:diamond_block"',
   'assert len(card_signatures)==24',
   '("mending","unbreaking")',
  ):self.assertIn(key,SOURCE)
 def test_workflow_and_legacy(self):
  self.assertLess(WF.index("apply-power-armor-build98.py"),
                  WF.index("apply-power-armor-expensive-recipes-103.py"))
  self.assertIn("BUILD104_96_ARMOR_24_UPGRADE_RECIPES PASS",WF)
  self.assertNotIn('write("PowerArmorSuitWorld.java"',SOURCE)
  self.assertNotIn('ModDataComponents.POWER_ARMOR_UPGRADES',SOURCE)

if __name__=="__main__":unittest.main()
