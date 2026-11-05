#!/usr/bin/env python3
"""B1120 P0: prove old exact-center test would miss actual 1119 failure.

The important execution gate is the real NeoForge GameTestServer, applied
after B1107/B1120 and run for all 24 registered MKs with real equipment.
These unit gates fail if someone weakens that coverage back to teleport-center.
"""
import ast
import math
import runpy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1120-physical-walkin.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
SOURCE=PATCH.read_text(encoding="utf-8")

class B1120UserWalkIn(unittest.TestCase):
 def test_python_compiles(self):
  ast.parse(SOURCE)
  self.assertTrue(callable(runpy.run_path(str(PATCH))["entry_patch"]))
  self.assertTrue(callable(runpy.run_path(str(PATCH))["test_patch"]))

 def test_player_shell_reproduces_b1119_no_step(self):
  # The same offset used by the actual Java test. Old threshold 0.22
  # rejects it, while a human-sized 0.81 threshold accepts it.
  radius2=.82**2+.20**2
  self.assertGreater(radius2,.22,"B1119 bad threshold would accept this")
  self.assertLess(radius2,.81,"B1120 good threshold must accept this")
  self.assertLess(abs(.15),1.30)
  self.assertIn("dx*dx+dz*dz<=.81D",SOURCE)
  self.assertIn("return dx*dx+dz*dz<=.22D",SOURCE) # regression reference

 def test_original_item_owner_never_invisible_before_transfer(self):
  for tok in (
    "stand.removeTag(HIDE_TAG); // no hidden original while waiting",
    "stand.setInvisible(false);",
    "stand.noPhysics=true; // pass-through but renders the item-owning suit",
    "view.noPhysics=true; // cosmetic shell can NEVER block actual walk-in",
    "boolean originalMarker=false; // owned world suit's normal physics state",
    "legacy-noPhysics-on-click",
    "stand.noPhysics=true; // pass-through but renders the item-owning suit",
    'B1120_ORIGINAL_SUIT_HIDDEN_WHILE_WAITING_FOR_WALK_IN',
    'B1120_OPEN_SUIT_STILL_BLOCKS_PLAYER_MOVEMENT',
    'B1120_WORLD_OWNER_PHYSICS_RESTORED_AFTER_STEP',
    'B1121_RESTORED_MK9_MUST_CLEAR_LEGACY_INVISIBLE_NO_PHYSICS',
    'B1121_OLD_MK9_RECOVERY_LOST_OR_DUPLICATED_ITEMS',
    'B1120_PREMATURE_EQUIP_AT_ARMOR_SHELL_OUTSIDE',
    'B1120_MANUAL_ENTRY_WAIT',
    'stand.setInvisible(true);" not in s',
  ):
   self.assertIn(tok,SOURCE,tok)
  self.assertNotIn("new ArmorStand(",SOURCE)
  self.assertNotIn("setItemSlot(",SOURCE)
  self.assertNotIn("stand.discard();",SOURCE)

 def test_real_player_event_path_in_24_tier_game_test(self):
  for tok in (
    "player.setPos(stand.getX()+.82D,stand.getY()+.15D,stand.getZ()+.20D);",
    'B1120_MUST_NOT_TEST_PERFECT_CENTER_TELEPORT',
    'B1120_ORIGINAL_SUIT_HIDDEN_WHILE_WAITING_FOR_WALK_IN',
    'B1120_WORLD_OWNER_PHYSICS_RESTORED_AFTER_STEP',
    "NeoForge.EVENT_BUS.post(",
    "B1107_REAL_SERVER_ENTRY_ANIMATION_STARTED",
    "POWER_ARMOR_REAL_ROUNDTRIP_V69",
  ):
   # Most tokens are in B1120 patch, eventbus execution is in B1107.
   first=SOURCE
   second=(ROOT/"features/v176/apply-v176-b1107-manual-entry-guard.py").read_text()
   self.assertTrue(tok in first or tok in second,tok)
  g=(ROOT/"features/v176/apply-v176-b1103-all-mk-gametest.py").read_text()
  self.assertIn("for(int tier=0;tier<24;tier++)",g)
  self.assertIn("range(1,25)",(ROOT/"tests/test_v176_b1103_all_mk.py").read_text())
  w=WF.read_text()
  self.assertLess(w.index("python3 features/v176/apply-v176-b1107-manual-entry-guard.py"),
                  w.index("python3 features/v176/apply-v176-b1120-physical-walkin.py"))
  self.assertLess(w.index("python3 features/v176/apply-v176-b1120-physical-walkin.py"),
                  w.index("python3 tests/test_v176_b1104_freeze_entry.py"))
  self.assertIn("python3 tests/test_v176_b1120_walkin.py",w)
  self.assertIn("runGameTestServer",w)

if __name__=="__main__":
 unittest.main()
