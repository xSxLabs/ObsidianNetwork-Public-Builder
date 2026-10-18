#!/usr/bin/env python3
"""Fail-closed validation of real terminal persistence GameTest staging."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-terminal-craft-slot-noop-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
BEFORE='''class Build103GameTests {
   void test(){
      if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);
      System.out.println("REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS");
   }
}
'''
MARKER="REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS"

def run(before):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/"dev/obsidiannetwork/build103/Build103GameTests.java"
        p.parent.mkdir(parents=True)
        p.write_text(before)
        r=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
        return r,p.read_text()

class TerminalPersistenceGameTest(unittest.TestCase):
    def test_injection_real_handler_count_components_empty(self):
        r,after=run(BEFORE)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(after.count(MARKER),1)
        for tok in ("new dev.obsidiannetwork.blockentity.TerminalInventoryBlockEntity(",
                    "ObsidianNetwork.CRAFTING_TERMINAL.get().defaultBlockState()",
                    "for(int round=0;round<500;round++)for(int slot=0;slot<9;slot++)",
                    "persistenceProbe.setCraftItem(slot,exact);",
                    "ItemStack.matches(original,persistenceProbe.getCraftItem(slot))",
                    "DataComponents.DAMAGE,9","DataComponents.DAMAGE,10",
                    "ItemStack.EMPTY","changed_count=true changed_components=true clear=true"):
            self.assertIn(tok,after)
        twice,unchanged=run(after)
        self.assertNotEqual(twice.returncode,0)
        self.assertEqual(unchanged,after)
    def test_fail_closed_when_earlier_probes_missing(self):
        for old,new in (
            ("REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS","stale"), 
            ("if(attached!=50)","if(attached!=40)"),
        ):
            modified=BEFORE.replace(old,new)
            self.assertNotEqual(modified,BEFORE)
            r,after=run(modified)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(after,modified)
    def test_ci_checks_postpatch_both_server_configurations(self):
        text=WORKFLOW.read_text()
        needle="python3 patches/inject-terminal-craft-slot-noop-gametest.py"
        self.assertEqual(text.count(needle),1)
        self.assertLess(text.index("python3 patches/inject-drive-50-menu-server-stress-gametest.py"),
                        text.index(needle))
        for filename in ("build103-postpatch-gametest.log","build103-curios-installed-gametest.log"):
            self.assertIn("grep -Fq '"+MARKER+"' /tmp/"+filename,text)

if __name__=="__main__":
    unittest.main()
