#!/usr/bin/env python3
"""B1107 static fail-closed safety gate; actual MK1..MK24 run in GameTestServer."""
import ast
import runpy
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]
P=R/"features/v176/apply-v176-b1107-manual-entry-guard.py"
W=R/".github/workflows/networkstorage-v1.7-clean.yml"

class B1107ManualEntry(unittest.TestCase):
 def test_patch_compiles_and_has_pure_transformers(self):
  ast.parse(P.read_text(encoding="utf-8"))
  loaded=runpy.run_path(str(P))
  for function in ("world_patch","entry_patch","render_patch","test_patch"):
   self.assertTrue(callable(loaded.get(function)),function)

 def test_real_transition_and_atomic_rollback(self):
  s=P.read_text(encoding="utf-8")
  for text in (
    "entryStarted1107(ServerPlayer player,ArmorStand suit)",
    "PowerArmorSuitWorld.entryStarted1107(p,stand)",
    "if(!inside(p,stand))return;",
    "PowerArmorSuitWorld.tryEnter(p,stand.getId());",
    "if(!started){",
    "CLOSING.remove(id)",
    "recover1107(p,c.suit())",
    "recover1107(p,stand)",
    "stand.removeTag(OPEN_TAG);",
    "stand.removeTag(HIDE_TAG);",
    "stand.setInvisible(false);",
    "stand.noPhysics=opened.marker();",
    "restoreVisibility662(p);",
    "B1107_MANUAL_ENTRY_FAILED",
    "B1107_MANUAL_ENTRY_EXCEPTION",
    "B1109_ORPHANED_WORLD_SUIT_RESTORED",
    "!OPEN.containsKey(id)&&!CLOSING.containsKey(id)",
    "lost.noPhysics=false",
    "owned(suit,p)",
    "NeoForge.EVENT_BUS.post(",
    "B1108_REAL_EVENTBUS_FIXTURE_DRIFT",
    "B1107_REAL_SERVER_ENTRY_ANIMATION_STARTED",
    "B1107_ORIGINAL_WORLD_SUIT_VISIBLE_WHILE_ENTERING",
    "p.isInvisible() && v.isClosingFor659(p.getUUID())"
  ):
   self.assertIn(text,s,text)
  # Only PowerArmorSuitWorld is allowed to transfer the ORIGINAL item slots.
  entry=s.split("def entry_patch(s):",1)[1].split("def render_patch(s):",1)[0]
  self.assertIn('assert "stand.discard()" not in s and "new ArmorStand(" not in s',entry)
  self.assertNotIn("stand.discard();",entry)
  self.assertNotIn("player.setItemSlot(",entry)

 def test_real_build_enforces_24_tiers_and_freeze_gate(self):
  s=W.read_text(encoding="utf-8")
  for text in (
    "python3 features/v176/apply-v176-b1107-manual-entry-guard.py",
    "python3 tests/test_v176_b1107_entry_guard.py",
    "python3 tests/test_v176_b1104_freeze_entry.py",
    "python3 features/v176/apply-v176-b1103-all-mk-gametest.py",
    "contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')"
  ):
   self.assertIn(text,s,text)
  self.assertLess(s.index("python3 features/v176/apply-v176-b1103-all-mk-gametest.py"),
                  s.index("python3 features/v176/apply-v176-b1107-manual-entry-guard.py"))
  self.assertLess(s.index("python3 features/v176/apply-v176-b1107-manual-entry-guard.py"),
                  s.index("python3 tests/test_v176_b1104_freeze_entry.py"))

if __name__=="__main__":
 unittest.main()
