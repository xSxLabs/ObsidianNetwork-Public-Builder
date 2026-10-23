#!/usr/bin/env python3
"""Fail-closed source contract for Build 69 headless Power Armor GameTest."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v17/inject-power-armor-roundtrip-gametest-69.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class LiveRoundtrip69(unittest.TestCase):
 def test_overlay_valid_and_game_test_only(self):
  src=PATCH.read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("POWER_ARMOR_REAL_ROUNDTRIP_V69",src)
  self.assertIn("PowerArmorSuitWorld.exit(player)==1",src)
  self.assertIn("PowerArmorSuitWorld.tryEnter(player,stand.getId())",src)
  self.assertIn("PlayerTickEvent.Post(player)",src)
  self.assertIn("previous_armor_restored=true",src)
  self.assertIn("FakePlayerFactory.get(level,profile)",src)

 def test_runner_in_two_curios_modes_and_before_jar_cleanup(self):
  source="python3 features/v17/inject-power-armor-roundtrip-gametest-69.py"
  self.assertIn(source,WORKFLOW)
  self.assertLess(WORKFLOW.index(source),WORKFLOW.index("runGameTestServer --stacktrace",WORKFLOW.index(source)))
  self.assertIn("grep -Fq 'POWER_ARMOR_REAL_ROUNDTRIP_V69 PASS tier=MK1'",WORKFLOW)
  self.assertIn("grep -Fq 'POWER_ARMOR_REAL_ROUNDTRIP_V69 PASS tier=MK2'",WORKFLOW)
  self.assertLess(WORKFLOW.index(source),WORKFLOW.index("rm -rf work/src/main/java/dev/obsidiannetwork/build103",WORKFLOW.index(source)))

if __name__=="__main__": unittest.main()
