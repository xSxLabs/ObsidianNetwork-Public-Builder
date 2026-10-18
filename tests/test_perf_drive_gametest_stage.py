#!/usr/bin/env python3
"""Fail-closed regression for baseline-vs-postpatch 16-slot Drive GameTest staging."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/networkstorage-v1.6.yml"
INJECT = ROOT / "patches/inject-drive-16-slot-postpatch-gametest.py"
DRIVE = ROOT / "patches/perf-drive-menu-serialization-hotpath.py"
MARKER = "DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS"
FIXTURE = "                " + "if(insertedCells!=800)throw new IllegalStateException(\"Expected 800 real cells\");" + "\n" + "                h.startSequence().thenExecuteAfter(50,()->{\n"

class DriveStagingTests(unittest.TestCase):
    def test_real_game_tests_are_after_fix_but_not_in_baseline(self):
        wf = WORKFLOW.read_text(encoding="utf-8")
        baseline = wf.index("(cd work && gradle --no-daemon --no-configuration-cache runGameTestServer")
        patch = wf.index("python3 patches/perf-drive-menu-serialization-hotpath.py")
        injected = wf.index("python3 patches/inject-drive-16-slot-postpatch-gametest.py")
        postpatch = wf.index(" > /tmp/build103-postpatch-gametest.log")
        self.assertLess(baseline, patch)
        self.assertLess(patch, injected)
        self.assertLess(injected, postpatch)
        restored = wf.index("cp /tmp/obsidian-perf-gametest/Build103GameTests.java "
                            "work/src/main/java/dev/obsidiannetwork/build103/")
        self.assertLess(patch, restored)
        self.assertLess(restored, injected)
        self.assertNotIn(MARKER, wf[:baseline])
        self.assertEqual(wf.count("python3 patches/inject-drive-16-slot-postpatch-gametest.py"), 1)
        for log in ("build103-postpatch-gametest.log", "build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '" + MARKER + "' /tmp/" + log, wf)
            self.assertIn("grep -Fq 'DRIVE_GUI_LOWER_EIGHT_CELL_ROUNDTRIP_V1 PASS' /tmp/" + log, wf)
        drive = DRIVE.read_text(encoding="utf-8")
        self.assertIn("return CELL_SLOTS;", drive)
        self.assertIn("StorageDriveRuntime.SLOTS - 1;", drive)
        self.assertIn("cellInventory.serialize(output.child(", drive)
        self.assertIn("cellInventory.deserialize(input.childOrEmpty(", drive)

    def test_inject_once_into_actual_fixture_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "dev/obsidiannetwork/build103/Build103GameTests.java"
            src.parent.mkdir(parents=True)
            src.write_text(FIXTURE, encoding="utf-8")
            env = {**os.environ, "V1_SOURCE_ROOT": td}
            cmd = [sys.executable, str(INJECT)]
            first = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            updated = src.read_text()
            self.assertEqual(updated.count(MARKER), 1)
            self.assertIn("backing.getContainerSize()!=16", updated)
            self.assertIn("for(int slot=0;slot<16;slot++)", updated)
            self.assertIn("for(int slot=8;slot<16;slot++)", updated)
            self.assertIn("backing.removeItemNoUpdate(slot)", updated)
            self.assertIn("backing.setItem(slot,withdrawn)", updated)
            self.assertIn("net.minecraft.world.item.ItemStack.matches(originalCell,restoredCell)", updated)
            self.assertIn("DRIVE_GUI_LOWER_EIGHT_CELL_ROUNDTRIP_V1 PASS", updated)
            again = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(src.read_text(), updated)

    def test_missing_fixture_never_changes_source(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "dev/obsidiannetwork/build103/Build103GameTests.java"
            src.parent.mkdir(parents=True)
            src.write_text("class Build103GameTests {}\n")
            env = {**os.environ, "V1_SOURCE_ROOT": td}
            result = subprocess.run([sys.executable, str(INJECT)], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(src.read_text(), "class Build103GameTests {}\n")

if __name__ == "__main__":
    unittest.main()
