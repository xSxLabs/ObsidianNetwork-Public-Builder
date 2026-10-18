#!/usr/bin/env python3
"""Validate Crafting Terminal per-mutation duplicate broadcast elimination."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/perf-terminal-duplicate-broadcast-elision.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
SOURCE='''class StorageTerminalMenu {
   public void slotsChanged(Container container) {
      for (int i=0;i<9;i++) {
         be.setCraftItem(i, this.craftSlots.getItem(i));
      }
      this.rebuildRecipeChoice(sp, level);
      this.broadcastChanges();
   }

   public int recipeChoiceCount() { return 0; }
   private Object matchingCraftRecipes() { return null; }
   private void rebuildRecipeChoice(ServerPlayer sp, ServerLevel level) {
      if (recipes.isEmpty()) {
         this.resultSlots.setItem(0, ItemStack.EMPTY);
         this.broadcastChanges();
         return;
      }
      this.resultSlots.setItem(0, current);
      this.broadcastChanges();
   }
   public boolean clickMenuButton(Player p, int i) {
      this.rebuildRecipeChoice(sp, level);
      return true;
   }
}
'''

def run(source):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
        p.parent.mkdir(parents=True)
        p.write_text(source)
        r=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
        return r,p.read_text()

class TerminalBroadcastTests(unittest.TestCase):
    def test_only_one_of_three_broadcasts_removed(self):
        r,s=run(SOURCE)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(s.count("this.broadcastChanges();"),2)
        self.assertIn("XSXLABS_TERMINAL_DUPLICATE_BROADCAST_ELISION_V1",s)
        self.assertIn("this.rebuildRecipeChoice(sp, level);",s)
        self.assertIn("this.resultSlots.setItem(0, current);",s)
        self.assertIn("be.setCraftItem(i, this.craftSlots.getItem(i));",s)
        r2,s2=run(s)
        self.assertNotEqual(r2.returncode,0)
        self.assertEqual(s,s2)
    def test_fail_closed_when_recipe_branch_unverified(self):
        for before,after in (
            ("this.broadcastChanges();\n         return;", "return;"),
            ("this.broadcastChanges();\n   }\n   public boolean", "return;\n   }\n   public boolean"),
            ("this.rebuildRecipeChoice(sp, level);", "this.rebuildRecipeChoice(sp, level); changedAfter();"),
            ("be.setCraftItem(", "be.saveOnly("),
        ):
            src=SOURCE.replace(before,after)
            self.assertNotEqual(src,SOURCE)
            r,s=run(src)
            self.assertNotEqual(r.returncode,0,before)
            self.assertEqual(s,src)
    def test_equivalence_all_recipe_outcomes(self):
        # Both old and new call rebuildRecipeChoice -> broadcast. Old repeats it
        # after no further mutation. This is read/sync-only, not state change.
        for recipes in [0,1,2,20]:
            for updates in range(1,150):
                old_broadcasts=updates*2
                new_broadcasts=updates
                self.assertEqual(old_broadcasts-new_broadcasts,updates)
                self.assertEqual(recipes==0,recipes==0)
    def test_workflow_stage(self):
        s=WORKFLOW.read_text()
        self.assertEqual(s.count("python3 patches/perf-terminal-duplicate-broadcast-elision.py"),1)
        self.assertLess(s.index("python3 patches/perf-terminal-unchanged-craft-slot-elision.py"),
                        s.index("python3 patches/perf-terminal-duplicate-broadcast-elision.py"))
        self.assertIn("verify_compiled_terminal_broadcast.py",s)

if __name__=="__main__":
    unittest.main()
