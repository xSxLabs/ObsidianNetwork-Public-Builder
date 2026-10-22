#!/usr/bin/env python3
"""Regression contract: 26.1 Armor Station GUI safety and slot geometry."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ArmorStationGui47(unittest.TestCase):
 def test_qualified_build_order_and_valid_python(self):
  ast.parse(PATCH)
  self.assertIn("python3 features/v17/apply-power-armor-freestanding.py",WF)
  self.assertIn("test_clean_v17_*.py",WF)
 def test_shift_click_validates_resolved_owned_stand_and_slot_range(self):
  tail=PATCH.split("# BUILD47_STATION_GUI_SAFETY",1)[1]
  self.assertIn("||slot<27||slot>=this.slots.size()",tail)
  self.assertIn("this.suit=resolve();",tail)
  self.assertIn("if(suit==null)return ItemStack.EMPTY;",tail)
  guarded=tail.index("||slot<27||slot>=this.slots.size()")
  self.assertLess(tail.index("this.suit=resolve();",guarded),
                  tail.index("var inventorySlot=this.slots.get(slot);",guarded))
 def test_preview_never_rebroadcasts_unchanged_stacks(self):
  tail=PATCH.split("# BUILD47_STATION_GUI_SAFETY",1)[1]
  self.assertIn("Arrays.fill(desired,ItemStack.EMPTY)",tail)
  self.assertIn("Math.min(15,visible.size())",tail)
  self.assertIn("!ItemStack.matches(preview.getItem(i),desired[i])",tail)
  self.assertIn("preview.setItem(i,desired[i])",tail)
 def test_player_inventory_overlay_matches_real_slots(self):
  tail=PATCH.split("# BUILD47_STATION_GUI_SAFETY",1)[1]
  self.assertIn("int invTop=this.getImageHeight()-66;",tail)
  self.assertIn("int sy=y+invTop+(index<27?row*18:58);",tail)
  height=114+3*18
  first=height-66
  self.assertEqual([first+row*18 for row in range(3)],[102,120,138])
  self.assertEqual(first+58,160)

if __name__=="__main__":
 unittest.main()
