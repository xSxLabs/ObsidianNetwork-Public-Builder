#!/usr/bin/env python3
"""Static fail-closed gating plus seven-sink distribution and quantity model."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"patches/v173-stack-upgrades-global.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class StackUpgradeTests(unittest.TestCase):
 def test_source_parses(self): ast.parse(SRC)
 def test_both_cable_paths(self):
  for key in ("blockentity/LogisticsCableBlockEntity.java","conduit/ItemConduitTicker.java",
              "Math.min(16,stacks(in))","Math.min(16,standalone.stacks(src.side()))",
              "bundle.logisticsStack(","rr.put(slotKey,(start+k+1)%targets.size())",
              "xsxItemOutputCursor[side]","if(!progressed)break;"):
   self.assertIn(key,SRC,key)
 def test_importer_exporter_and_gui(self):
  for key in ("ImporterBlockEntity.java","ExporterBlockEntity.java",
              "be.runtime.runCycle","64*Math.max(1,Math.min(16,be.stackUpgrades))",
              "this.stackUpgrades < 16","return 16;","Math.min(16, v.getCount())",
              "s == 1 ? 16 : 4"):
   self.assertIn(key,SRC,key)
 def test_conservation_fallback(self):
  self.assertEqual(SRC.count("net.minecraft.world.Containers.dropItemStack("),2)
  for key in ("if(!rest.isEmpty())","if(!remainder.isEmpty())",
              "src.insertItem(ri,rest,false)","from.insertItem(ri,remainder,false)"):
   self.assertIn(key,SRC)
 def test_seven_sinks_fairness_model(self):
  slots=[0]*7
  cursor=0
  operations=16
  source=16*64
  for _ in range(operations):
   selected=cursor%7
   slots[selected]+=64
   source-=64
   cursor=(selected+1)%7
  self.assertEqual(sum(slots),1024)
  self.assertEqual(source,0)
  self.assertEqual(7,sum(x>0 for x in slots))
  self.assertEqual([3,3,2,2,2,2,2],[x//64 for x in slots])
 def test_limited_destination_conservation_model(self):
  src=16*64
  stored=[0]*7
  capacity=[64,0,32,128,0,256,64]
  next_sink=0
  for _ in range(16):
   accepted=0
   for k in range(7):
    i=(next_sink+k)%7
    accepted=min(64,src,capacity[i]-stored[i])
    if accepted:
     stored[i]+=accepted
     src-=accepted
     next_sink=(i+1)%7
     break
   if not accepted: break
  self.assertEqual(src+sum(stored),1024)
  self.assertTrue(all(0<=x<=c for x,c in zip(stored,capacity)))
 def test_workflow_order(self):
  self.assertIn("test_v173_stack_upgrades_global.py",WF)
  self.assertIn("python3 patches/v173-stack-upgrades-global.py",WF)
  self.assertLess(WF.index("python3 patches/item-conduit-duplicate-scan-elision.py"),
                  WF.index("python3 patches/v173-stack-upgrades-global.py"))
if __name__=="__main__":unittest.main()
