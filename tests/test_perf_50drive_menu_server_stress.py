#!/usr/bin/env python3
"""Fail-closed CI-only GameTest injection for 50 real Drive menu backings."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-drive-50-menu-server-stress-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
MARKER="REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS"
BEFORE="""class Build103GameTests {
    void fiftyDriveProbe(){
      if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");
      System.out.println("DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS");
      System.out.println("DRIVE_GUI_LOWER_EIGHT_CELL_ROUNDTRIP_V1 PASS");
      if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);
      if(rt.storage().cells().size()!=800)throw new IllegalStateException();
    }
}
"""

def run(source):
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/"dev/obsidiannetwork/build103/Build103GameTests.java"
        path.parent.mkdir(parents=True)
        path.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],
            env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
        return result,path.read_text()

class FiftyDriveMenuGameTest(unittest.TestCase):
    def test_single_injection_and_all_16_real_cell_reads(self):
        ast.parse(PATCH.read_text())
        result,after=run(BEFORE)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(after.count(MARKER),1)
        for token in ("Class.forName(\"dev.obsidiannetwork.menu.DriveMenu$DriveContainer\")",
                      "backing.getContainerSize()!=16","var first=backing.getItem(slot)",
                      "var again=backing.getItem(slot)",
                      "net.minecraft.world.item.ItemStack.matches(first,again)",
                      "if(be.occupiedSlots()!=16)","menuOpens!=450||menuReads!=14400",
                      "p90_ns=","not_server_MSPT=true"):
            self.assertIn(token,after)
        twice,unchanged=run(after)
        self.assertNotEqual(twice.returncode,0)
        self.assertEqual(after,unchanged)
    def test_untrusted_fixture_drift_writes_nothing(self):
        for old,new in (
            ("if(attached!=50)","if(attached!=8)"),
            ("Expected 800 real cells","Expected 400 real cells"),
            ("DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS","old 8-slot marker"),
            ("DRIVE_GUI_LOWER_EIGHT_CELL_ROUNDTRIP_V1 PASS","removed"),
            ("rt.storage().cells().size()!=800","rt.storage().cells().size()!=400")
        ):
            modified=BEFORE.replace(old,new)
            self.assertNotEqual(modified,BEFORE)
            result,after=run(modified)
            self.assertNotEqual(result.returncode,0,old)
            self.assertEqual(modified,after,old)
    def test_workflow_only_runs_on_optimized_java_before_gametest(self):
        text=WORKFLOW.read_text()
        self.assertEqual(text.count("python3 patches/inject-drive-50-menu-server-stress-gametest.py"),1)
        earlier=text.index("python3 patches/perf-drive-menu-serialization-hotpath.py")
        drive=text.index("python3 patches/inject-drive-16-slot-postpatch-gametest.py")
        stress=text.index("python3 patches/inject-drive-50-menu-server-stress-gametest.py")
        runtime=text.index("(cd work && gradle --no-daemon --no-configuration-cache runGameTestServer",drive)
        self.assertLess(earlier,drive)
        self.assertLess(drive,stress)
        self.assertLess(stress,runtime)
        self.assertNotIn(MARKER,text[:earlier])
        for log in ("build103-postpatch-gametest.log","build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '"+MARKER+"' /tmp/"+log,text)

if __name__=="__main__":
    unittest.main()
