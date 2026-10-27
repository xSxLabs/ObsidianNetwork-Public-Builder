#!/usr/bin/env python3
"""Fail-closed reconstruction regression for the v1.7.3 Printer item fix."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-printer-canonical-materials.py"
JAVA="dev/obsidiannetwork/blockentity/NetworkDeviceBlockEntity.java"
BASE='''class NetworkDeviceBlockEntity {
 private void printer() {
  ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(material.getItem()).toString());
  long extracted=net.storage().extract(key,1L);
  if(extracted!=1L){
   missing=material.copyWithCount(1);
   setStatus("MISSING: 1 x "+material.getHoverName().getString());return;
  }
  missing=ItemStack.EMPTY;
  if(!targetState.getFluidState().isEmpty()){
     net.storage().insert(key,1L);
     setStatus("UNSUPPORTED FLUID BLOCKSTATE "+name);return;
    }
  boolean placed=world.setBlock(dest,targetState,3);
  if(!placed){
   net.storage().insert(key,1L);
   setStatus("PROTECTED/BLOCKED AT "+dest.toShortString());return;
  }
  if(!spendFE(250L))throw new IllegalStateException("FE preflight violated");
 }
}
'''

def apply(content,repeat=False):
 with tempfile.TemporaryDirectory() as temp:
  f=Path(temp)/JAVA
  f.parent.mkdir(parents=True,exist_ok=True)
  f.write_text(content,encoding="utf-8")
  env={**os.environ,"V1_SOURCE_ROOT":temp}
  run=lambda:subprocess.run([sys.executable,str(PATCH)],env=env,
                             capture_output=True,text=True,timeout=20)
  first=run()
  second=run() if repeat and first.returncode==0 else None
  return first,f.read_text(encoding="utf-8"),second

class PrinterCanonicalRegression(unittest.TestCase):
 def test_prioritize_exact_components_and_use_legacy_only_as_fallback(self):
  result,src,_=apply(BASE)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertIn("V173_PRINTER_CANONICAL_MATERIALS_PASS",result.stdout)
  self.assertIn("world.registryAccess()).describe(material.copyWithCount(1))",src)
  self.assertIn("net.storage().extract(canonicalKey,1L)",src)
  self.assertIn("if(extracted==0L && !legacyKey.equals(canonicalKey))",src)
  self.assertIn("net.storage().extract(legacyKey,1L)",src)
  self.assertLess(src.index("net.storage().extract(canonicalKey,1L)"),
                  src.index("net.storage().extract(legacyKey,1L)"))
  self.assertNotIn("net.storage().extract(key,1L)",src)

 def test_refund_same_key_or_fail_explicitly(self):
  result,src,_=apply(BASE)
  self.assertEqual(result.returncode,0,result.stderr)
  for token in (
   "net.descriptors().registerKnown(canonicalKey,descriptor.canonicalPayload())",
   "net.storage().insertExact(canonicalKey,descriptor.canonicalPayload(),1L)",
   "net.storage().insert(legacyKey,1L)",
   "V173_PRINTER_FLUID_CONSERVATION",
   "if(fluidRefund!=1L)",
   "Network Printer fluid-state refund failed",
   "if(restored!=1L)",
   'throw new IllegalStateException("Network Printer material refund failed:',
   "boolean placed=world.setBlock(dest,targetState,3)",
   "missing=material.copyWithCount(1)",
   "spendFE(250L)",
  ):
   self.assertIn(token,src)
  self.assertNotIn("net.storage().insert(key,1L)",src)

 def test_atomic_on_drift_and_no_double_application(self):
  for changed in (
   BASE.replace("net.storage().extract(key,1L)","net.storage().extract(key,2L)"),
   BASE.replace("net.storage().insert(key,1L)","net.storage().insert(key,2L)"),
   BASE.replace("UNSUPPORTED FLUID BLOCKSTATE","FLUID STATE NOT SUPPORTED"),
   BASE.replace("missing=material.copyWithCount(1)","missing=ItemStack.EMPTY")
  ):
   run,actual,_=apply(changed)
   self.assertNotEqual(run.returncode,0)
   self.assertEqual(actual,changed)
  first,_,second=apply(BASE,repeat=True)
  self.assertEqual(first.returncode,0,first.stderr)
  self.assertNotEqual(second.returncode,0)

 def test_workflow_regression_order(self):
  workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
  marker="python3 features/v173/apply-printer-canonical-materials.py"
  self.assertEqual(workflow.count(marker),1)
  self.assertIn("test_v173_printer_canonical_materials.py",workflow)
  self.assertLess(workflow.index("python3 features/v173/apply-blueprint-placement-controls.py"),
                  workflow.index(marker))
  self.assertLess(workflow.index(marker),
                  workflow.index("python3 patches/inject-v173-planter-real-gametest.py"))

if __name__=="__main__":
 unittest.main()
