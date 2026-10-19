#!/usr/bin/env python3
"""Strict CI-only 15-tick Crafting Terminal result-slot shift-click test."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-terminal-shift-craft-15tick-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
MARKER="REAL_50_DRIVE_TERMINAL_SHIFT_CRAFT_15_TICKS_V1 PASS"
FIXTURE='''class Build103GameTests {
 void fiftyDrive(){
   if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);
   System.out.println("REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS");
   System.out.println("REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS");
   System.out.println("REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS");
   var pos=xsxlabsBurstTerminalPos;
 }
}'''
def apply(source):
    with tempfile.TemporaryDirectory() as root:
        p=Path(root)/"dev/obsidiannetwork/build103/Build103GameTests.java"
        p.parent.mkdir(parents=True)
        p.write_text(source)
        r=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                         env={**os.environ,"V1_SOURCE_ROOT":root})
        return r,p.read_text()

class FifteenTickShiftCraft(unittest.TestCase):
    def test_true_result_slot_and_recipe_count_coverage(self):
        r,source=apply(FIXTURE)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(source.count(MARKER),1)
        for term in ("new dev.obsidiannetwork.menu.StorageTerminalMenu(",
                     "net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level)", "Items.OAK_LOG,16",
                     "Items.OAK_PLANKS", "preview.getCount()!=4",
                     "xsxCraftMenu.clicked(0,0,",
                     "ContainerInput.QUICK_MOVE,xsxCraftPlayer)",
                     "if(planks!=64)", "xsxLogsConsumed[0]!=240",
                     "xsxPlanksReceived[0]!=960", "xsxCraftSequence.thenExecuteAfter(1",
                     "rt.tick();","not_server_MSPT=true",
                     "REAL_50_DRIVE_TERMINAL_SAME_TICK_BURST_V1 PASS",
                     "for(int burst=0;burst<24;burst++)",
                     "xsxBurstClicks[0]!=360", "xsxBurstUnspent[0]!=120",
                     "unspent.getCount()!=8", "no_duplicate_output=true",
                     "REAL_50_DRIVE_MIXED_CRAFT_GUI_15_TICKS_V1 PASS",
                     "xsxMixedControllerOpens[0]!=30||xsxMixedAutoOpens[0]!=30",
                     "for(int mix=0;mix<2;mix++)",
                     "mixedController.drives()!=50",
                     "mixedController.autocrafters()<1",
                     "new dev.obsidiannetwork.menu.AutocrafterMenu(",
                     "ItemStack.matches(a,b)",
                     "gui_p95_ns=", "xsxMixedGuiNs[14]"):
            self.assertIn(term,source,term)
        self.assertNotIn("h.makeMockServerPlayerInLevel()",source)
        repeat,identical=apply(source)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual(identical,source)
    def test_fail_closed_without_earlier_real_game_gates(self):
        for term in ("if(attached!=50)",
                     "REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS",
                     "REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS",
                     "REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS",
                     "xsxlabsBurstTerminalPos"):
            invalid=FIXTURE.replace(term,"TEST_ANCHOR_REMOVED")
            r,after=apply(invalid)
            self.assertNotEqual(r.returncode,0,term)
            self.assertEqual(after,invalid)
    def test_workflow_postpatch_and_curios_required(self):
        s=WORKFLOW.read_text()
        command="python3 patches/inject-terminal-shift-craft-15tick-gametest.py"
        self.assertEqual(s.count(command),1)
        self.assertLess(s.index("python3 patches/inject-controller-autocrafter-50drive-gui-stress.py"),
                        s.index(command))
        for name in ("build103-postpatch-gametest.log","build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '"+MARKER+"' /tmp/"+name,s)
            self.assertIn("grep -Fq 'REAL_50_DRIVE_TERMINAL_SAME_TICK_BURST_V1 PASS' /tmp/"+name,s)
            self.assertIn("grep -Fq 'REAL_50_DRIVE_MIXED_CRAFT_GUI_15_TICKS_V1 PASS' /tmp/"+name,s)

if __name__=="__main__":
    unittest.main()
