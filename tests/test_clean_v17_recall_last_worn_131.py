#!/usr/bin/env python3
"""Build 131: last-worn recall, grouped controls, hand-instant stations."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v172/apply-power-armor-recall-last-worn-131.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class LastWorn131(unittest.TestCase):
 def test_python_syntax(self):ast.parse(PATCH)
 def test_preference_persistence_without_old_index_migration(self):
  for s in ("BUILD131_LAST_WORN_PERSISTED","power_armor_last_worn",
            "PowerArmorRecallPreference::all","public UUID preferred(UUID owner)",
            "public void remember(UUID owner,UUID suit)"):self.assertIn(s,PATCH)
  self.assertNotIn('edit("powerarmor/PowerArmorRecallIndex.java"',PATCH)
 def test_recall_last_worn_only(self):
  for s in ("BUILD131_PREFER_LAST_WORN","if(matches.size()==1)",
            "last.toString()","if(loc==null)",
            "multiple suits found but no last-worn suit saved",
            "PowerArmorRecall.rememberLastWorn(player,stand);"):self.assertIn(s,PATCH)
 def test_exit_commit_required(self):
  self.assertIn("BUILD131_VERIFIED_EXIT_FAVORITE",PATCH)
  self.assertIn('assert "if(!valid)" in body',PATCH)
  self.assertIn("expected one successful exit return",PATCH)
  self.assertIn("PowerArmorRecall.rememberLastWorn(player,stand);",PATCH)
 def test_rebindable_grouped_controls(self):
  for s in ("ObsidianKeyCategory","e.registerCategory(CATEGORY)",
            "powerarmor/PowerArmorExitKeyClient.java",
            "powerarmor/PowerArmorRecallKeyClient.java",
            "key.category.obsidiannetwork.controls"):self.assertIn(s,PATCH)
 def test_safe_instant_hand_break(self):
  self.assertIn(".strength(4.0F,3600000.0F)",PATCH)
  self.assertIn(".strength(0.0F,3600000.0F)",PATCH)
  self.assertNotIn("protectLoadedStand",PATCH)
 def test_pipeline_order(self):
  self.assertIn("branches: [v1.7, v1.7.2]",WF)
  self.assertLess(WF.index("python3 features/v172/apply-power-armor-recall.py"),
                  WF.index("python3 features/v172/apply-power-armor-recall-last-worn-131.py"))
  self.assertIn("BUILD131_LAST_WORN_RECALL PASS",WF)
if __name__=="__main__":unittest.main()
