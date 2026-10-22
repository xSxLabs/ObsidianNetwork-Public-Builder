#!/usr/bin/env python3
"""Build 49: five-card stacks, damage cost and horizontal station states."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FREE=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text(encoding="utf-8")
CARDS=(ROOT/"features/v17/apply-power-armor-cards.py").read_text(encoding="utf-8")

class Build49(unittest.TestCase):
 def test_valid_generators(self):
  ast.parse(FREE)
  ast.parse(CARDS)
 def test_one_socket_five_level_upgrade(self):
  part=FREE.split("# BUILD49_GROUPED_FIVE_AND_FACING:",1)[1]
  self.assertIn('"feather_falling" -> 5;',part)
  self.assertIn('java.util.Collections.frequency(values,id)',part)
  self.assertIn('seen.add(id)',part)
  self.assertIn('Math.min(stack.getCount(),maxCardCount(card.upgradeId)-duplicates)',part)
  self.assertIn('stack.shrink(take)',part)
  self.assertIn('if(take<=0)return ItemStack.EMPTY',part)
  self.assertIn('values.remove(i)',FREE)
  self.assertIn('case "mending","unbreaking" -> 0',FREE)
 def test_disabled_old_discs_and_energy_shield(self):
  part=FREE.split("# BUILD49_GROUPED_FIVE_AND_FACING:",1)[1]
  self.assertIn('for obsolete in ("MENDING","UNBREAKING")',part)
  self.assertIn('Math.min(5,protection)*0.08f',part)
  self.assertIn('Math.min(5,fire)*0.16f',part)
  self.assertIn('Math.min(5,feather)*0.24f',part)
  self.assertIn('Math.min(0.80f,reduction)',part)
  self.assertIn('EnergyTool.consume(',CARDS)
 def test_four_placed_orientations(self):
  part=FREE.split("# BUILD49_GROUPED_FIVE_AND_FACING:",1)[1]
  self.assertIn('HORIZONTAL_FACING',part)
  self.assertIn('getHorizontalDirection().getOpposite()',part)
  self.assertIn('states["variants"]=faced',part)
  self.assertIn('assert len(faced)==32',part)
  self.assertIn('for facing,yrot in',part)

if __name__=="__main__":
 unittest.main()
