#!/usr/bin/env python3
"""Fail-closed v1.7.3 GameTest staging regression for live Printer."""
import ast,os,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/inject-v173-printer-real-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
JAVA="dev/obsidiannetwork/build103/Build103GameTests.java"
ANCHOR='                  // V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST: no mock cells.'

class PrinterGameTestGate(unittest.TestCase):
 def test_injection_and_double_use_guard(self):
  ast.parse(PATCH.read_text())
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/JAVA
   f.parent.mkdir(parents=True,exist_ok=True)
   f.write_text("class Fixture {\n"+ANCHOR+"\n}\n")
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   def apply():return subprocess.run([sys.executable,str(PATCH)],env=env,
                                  capture_output=True,text=True,timeout=20)
   result=apply()
   self.assertEqual(result.returncode,0,result.stderr)
   actual=f.read_text()
   for marker in ("V173_PRINTER_REAL_CANONICAL_MATERIALS_GAME_TEST PASS",
                  "NETWORK_PRINTER.get().defaultBlockState()",
                  "WorldTopologyBridge.runtimeForAccessory",
                  "Items.PURPUR_BLOCK", "xsxPrinterExact.key()",
                  "xsxPrinterLegacy", "xsxPrint.invoke(xsxPrinter,level,rt)",
                  "xsxEnergyField.getLong(xsxPrinter)!=500L",
                  "NETWORK_SCHEMATIC_QUILL.get()", "cells=800", "clean_fixture=true"):
    self.assertIn(marker,actual)
   second=apply()
   self.assertNotEqual(second.returncode,0)
   self.assertEqual(actual,f.read_text())

 def test_atomic_failure_on_source_drift(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/JAVA
   f.parent.mkdir(parents=True,exist_ok=True)
   f.write_text("class Fixture {}\n")
   run=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},
                      capture_output=True,text=True)
   self.assertNotEqual(run.returncode,0)
   self.assertEqual(f.read_text(),"class Fixture {}\n")

 def test_injected_after_planter_and_hard_gated(self):
  work=WORKFLOW.read_text()
  self.assertIn("python3 patches/inject-v173-printer-real-gametest.py",work)
  self.assertIn("test_v173_printer_real_gametest.py",work)
  self.assertIn("grep -Fq 'V173_PRINTER_REAL_CANONICAL_MATERIALS_GAME_TEST PASS' /tmp/build103-postpatch-gametest.log",work)
  self.assertLess(work.index("python3 patches/inject-v173-planter-real-gametest.py"),
                  work.index("python3 patches/inject-v173-printer-real-gametest.py"))

if __name__=="__main__":unittest.main()
