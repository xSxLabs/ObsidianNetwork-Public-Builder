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
 def test_v174_filters_are_checked_before_execute_on_both_item_paths(self):
  tree=ast.parse(SRC)
  methods={n.targets[0].id:ast.literal_eval(n.value)
           for n in tree.body if isinstance(n,ast.Assign)
           and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
           and n.targets[0].id in ("standalone","network")}
  cable=methods["standalone"]
  conduit=methods["network"]
  self.assertEqual(cable.count("V174_FILTER_SUCTION_466"),1)
  self.assertEqual(conduit.count("V174_FILTER_MIXED_466"),1)
  self.assertIn("this.cableAllows(in,",cable)
  self.assertIn("filteredCable.cableAllows(src.side(),",conduit)
  self.assertLess(cable.index("this.cableAllows(in,"),cable.index("ItemStack taken=src.extractItem(si,accepted,false);"))
  self.assertLess(conduit.index("filteredCable.cableAllows(src.side(),"),conduit.index("ItemStack taken=from.extractItem(si,accepted,false);"))
  self.assertIn("Math.min(16,stacks(in))",cable)
  self.assertIn("Math.min(16,standalone.stacks(src.side()))",conduit)
  self.assertIn("Math.min(16,bundle.logisticsStack(",conduit)
  self.assertIn("if(sample.isEmpty())continue;",cable)
  self.assertIn("if(sample.isEmpty())continue;",conduit)
 def test_filter_model_allows_only_configured_item_with_no_loss(self):
  for accepted in (set(),{"minecraft:diamond"}):
   stock={"minecraft:diamond":5,"minecraft:emerald":3}
   moved={k:v for k,v in stock.items() if not accepted or k in accepted}
   remaining={k:v for k,v in stock.items() if accepted and k not in accepted}
   self.assertEqual({k:moved.get(k,0)+remaining.get(k,0) for k in stock},stock)
   self.assertEqual(moved,stock if not accepted else {"minecraft:diamond":5})
 def test_workflow_order(self):
  self.assertIn("test_v173_stack_upgrades_global.py",WF)
  self.assertIn("python3 patches/v173-stack-upgrades-global.py",WF)
  self.assertLess(WF.index("python3 patches/item-conduit-duplicate-scan-elision.py"),
                  WF.index("python3 patches/v173-stack-upgrades-global.py"))
if __name__=="__main__":unittest.main()
