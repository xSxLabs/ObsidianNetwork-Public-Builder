#!/usr/bin/env python3
"""Strict staging of full-network Controller + Autocrafter real GUI stress."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"patches/inject-controller-autocrafter-50drive-gui-stress.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
MARKER="REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS"
FIXTURE='''class Build103GameTests {
   void test(){
       if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");
       if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);
       System.out.println("REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS");
       System.out.println("REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS");
       System.out.println("REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS");
   }
}
'''

def run(source):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/"dev/obsidiannetwork/build103/Build103GameTests.java"
        p.parent.mkdir(parents=True)
        p.write_text(source)
        r=subprocess.run([sys.executable,str(SCRIPT)],env={**os.environ,"V1_SOURCE_ROOT":tmp},
                         capture_output=True,text=True)
        return r,p.read_text()

class ControllerAutocrafterGuiStress(unittest.TestCase):
    def test_real_gui_injection_and_outcomes(self):
        r,source=run(FIXTURE)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(source.count(MARKER),1)
        for term in ("ObsidianNetwork.AUTOCRAFTER.get().defaultBlockState()",
                     "net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level)","new dev.obsidiannetwork.menu.PowerStatusMenu(",
                     "new dev.obsidiannetwork.menu.AutocrafterMenu(",
                     "menu.drives()!=50","menu.terminals()<1",
                     "menu.slots.get(0).getItem()",
                     "ItemStack.matches(first,again)",
                     "xsxControllerOpens!=180||xsxAutoOpens!=180",
                     "controller_p90_ns=", "autocrafter_p90_ns=", "not_server_MSPT=true",
                     "REAL_50_DRIVE_GUI_PHASE_BREAKDOWN_V1 PASS",
                     "xsxControllerCtorTrials", "xsxControllerStatusTrials",
                     "xsxAutocrafterCtorTrials", "xsxAutocrafterStatusTrials",
                     "controller_ctor_median_ns=", "controller_status_median_ns=",
                     "autocrafter_ctor_median_ns=", "autocrafter_status_median_ns=",
                     "uncontrolled=true"):
            self.assertIn(term,source,term)
        self.assertNotIn("h.makeMockServerPlayerInLevel()",source)
        again,identical=run(source)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(identical,source)
    def test_fail_closed_missing_fixture(self):
        for term in ("if(insertedCells!=800)","if(attached!=50)",
                     "REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS",
                     "REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS",
                     "REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS"):
            invalid=FIXTURE.replace(term,"INVALID_ANCHOR_REPLACEMENT")
            r,after=run(invalid)
            self.assertNotEqual(r.returncode,0,term)
            self.assertEqual(after,invalid)
    def test_workflow_only_postpatch_and_both_curios_configurations(self):
        text=WORKFLOW.read_text()
        script="python3 patches/inject-controller-autocrafter-50drive-gui-stress.py"
        self.assertEqual(text.count(script),1)
        self.assertLess(text.index("python3 patches/inject-terminal-real-quickmove-burst-gametest.py"),text.index(script))
        for name in ("build103-postpatch-gametest.log","build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '"+MARKER+"' /tmp/"+name,text)
            self.assertIn("grep -Fq 'REAL_50_DRIVE_GUI_PHASE_BREAKDOWN_V1 PASS' /tmp/"+name,text)
        self.assertIn("python3 performance/verify-gui-phase-breakdown.py",text)

if __name__=="__main__":
    unittest.main()
