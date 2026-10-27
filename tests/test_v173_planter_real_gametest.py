#!/usr/bin/env python3
"""Fail-closed regression for real-cell Planter migration GameTest injection."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-v173-planter-real-gametest.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ANCHOR='var stone=dev.obsidiannetwork.core.ItemKey.simple("minecraft:stone");'
JAVA="dev/obsidiannetwork/build103/Build103GameTests.java"

class RealPlanterMigrationGate(unittest.TestCase):
 def test_injection_survives_fixture_and_rejects_double_use(self):
  ast.parse(PATCH.read_text())
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/JAVA
   p.parent.mkdir(parents=True)
   p.write_text("class Fixture {\n"+ANCHOR+"\n}\n")
   env={**os.environ,"V1_SOURCE_ROOT":folder}
   first=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(first.returncode,0,first.stderr)
   content=p.read_text()
   for needle in ("V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST PASS",
                  "Items.OAK_LOG","Items.CARROT","Items.WHEAT",
                  "LegacyPlanterKeyMigration.tick(level,rt)",
                  "xsxAfterTick!=8L","cells().stream().mapToLong",
                  "Items.DIAMOND_SWORD","no_loss_or_duplication=true"):
    self.assertIn(needle,content)
   second=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(second.returncode,0)
   self.assertEqual(p.read_text(),content)

 def test_source_drift_never_mutates_fixture(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/JAVA
   p.parent.mkdir(parents=True)
   altered="class Fixture { }"
   p.write_text(altered)
   failure=subprocess.run([sys.executable,str(PATCH)],
        env={**os.environ,"V1_SOURCE_ROOT":folder},
        capture_output=True,text=True)
   self.assertNotEqual(failure.returncode,0)
   self.assertEqual(p.read_text(),altered)

 def test_ci_runs_after_all_feature_patches_and_requires_real_pass(self):
  self.assertIn("python3 patches/inject-v173-planter-real-gametest.py",WORKFLOW)
  self.assertIn("test_v173_planter_real_gametest.py",WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v173/apply-blueprint-placement-controls.py"),
                  WORKFLOW.index("python3 patches/inject-v173-planter-real-gametest.py"))
  self.assertIn("grep -Fq 'V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST PASS' /tmp/build103-postpatch-gametest.log",WORKFLOW)

if __name__=="__main__":
 unittest.main()
