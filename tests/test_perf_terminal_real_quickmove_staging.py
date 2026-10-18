#!/usr/bin/env python3
"""Stage 720 real Menu.quickMoveStack clicks and exact per-click conservation."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-terminal-real-quickmove-burst-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
FIXTURE='''class Build103GameTests {
   void test(){
       if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");
       System.out.println("DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS");
       if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);
       System.out.println("REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS");
       System.out.println("REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS");
   }
}
'''
MARKER="REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS"
def run(source):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/"dev/obsidiannetwork/build103/Build103GameTests.java"
        p.parent.mkdir(parents=True)
        p.write_text(source)
        r=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
        return r,p.read_text()

class RealTerminalQuickMoveTests(unittest.TestCase):
    def test_real_connected_terminal_player_quickmove_and_conservation(self):
        r,after=run(FIXTURE)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(after.count(MARKER),1)
        for term in ("ObsidianNetwork.CRAFTING_TERMINAL.get().defaultBlockState()",
                     "WorldTopologyBridge.runtimeForTerminal(",
                     "h.makeMockServerPlayerInLevel()",
                     "new dev.obsidiannetwork.menu.StorageTerminalMenu(",
                     "xsxMenu.quickMoveStack(xsxBurstPlayer,37)",
                     "if(moved.isEmpty()||moved.getCount()!=64||!xsxPlayerInv.getItem(0).isEmpty())",
                     "inStorage!=xsxBefore+64",
                     "rt.storage().extract(xsxBurstKey,64L)!=64L",
                     "xsxOperations!=720", "exact_items=46080", "rt.tick();", "MinecraftItemStackCodec(", "Items.COBBLESTONE,64)).key()", "not_server_MSPT=true"):
            self.assertIn(term,after,term)
        rr,unchanged=run(after)
        self.assertNotEqual(rr.returncode,0)
        self.assertEqual(unchanged,after)
    def test_fail_closed_when_earlier_gates_missing(self):
        for term in ("if(insertedCells!=800)","if(attached!=50)",
                     "DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS",
                     "REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS",
                     "REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS"):
            modified=FIXTURE.replace(term,"INVALID_ANCHOR_REPLACEMENT")
            r,after=run(modified)
            self.assertNotEqual(r.returncode,0,term)
            self.assertEqual(after,modified)
    def test_staged_only_postpatch_and_checks_all_server_variants(self):
        s=WORKFLOW.read_text()
        command="python3 patches/inject-terminal-real-quickmove-burst-gametest.py"
        self.assertEqual(s.count(command),1)
        self.assertLess(s.index("python3 patches/inject-terminal-craft-slot-noop-gametest.py"),s.index(command))
        for log in ("build103-postpatch-gametest.log","build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '"+MARKER+"' /tmp/"+log,s)
        self.assertNotIn("REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS",s[:s.index(command)])

if __name__=="__main__":
    unittest.main()
