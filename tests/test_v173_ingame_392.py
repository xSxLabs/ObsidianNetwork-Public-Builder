#!/usr/bin/env python3
"""B392 regression suite: full-height map, reliable Blueprint ghost and Printer."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FEATURES=ROOT/"features/v173"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
class TestIngame392(unittest.TestCase):
 def test_patches_parse_and_abort_on_source_drift(self):
  for name in ("apply-map-full-height-392.py","apply-blueprint-visible-392.py",
               "apply-printer-speed-skip-air-392.py"):
   src=(FEATURES/name).read_text(encoding="utf-8")
   ast.parse(src)
   self.assertIn("assert ",src)
 def test_vertical_world_bounds_and_square_voxels(self):
  s=(FEATURES/"apply-map-full-height-392.py").read_text()
  self.assertIn("final int topY=mc.level.getMaxY()-1;",s)
  self.assertIn("final int worldHeight=topY-bottomY+1;",s)
  self.assertIn("int high=Math.min(topY,low+stride-1);",s)
  self.assertIn("cube,cube,cube",s)
  self.assertIn("depthInput.visible=false;depthInput.active=false;",s)
 def test_blueprint_preview_not_restricted_to_16(self):
  s=(FEATURES/"apply-blueprint-visible-392.py").read_text()
  self.assertIn("B392_BLUEPRINT_ANY_SIZE",s)
  self.assertIn("NetworkBlueprintItem.MAX_BLOCKS",s)
  self.assertIn("b392Surface",s)
  self.assertIn("B392_BLUEPRINT_FIRST_FRAME",s)
  self.assertIn("state=Blocks.RED_STAINED_GLASS.defaultBlockState();",s)
 def test_air_skip_and_missing_once_and_speed(self):
  s=(FEATURES/"apply-printer-speed-skip-air-392.py").read_text()
  for token in ("B392_AIR_ZERO_COST","while(index<plan.size()",
                "index>=b378BlueprintBlocks().size()","missing=ItemStack.EMPTY;index++;",
                "int actions=1+be.b392SpeedCount();","for(int i=0;i<actions;i++)",
                "b392SkipButton.visible=","slotId!=3","out.store(\"speedUpgrades\""):
   self.assertIn(token,s)
  def step(plan,index,missing,skip=False):
   if skip and missing:
    index+=1;missing=False
   while index<len(plan) and plan[index]=="minecraft:air":index+=1
   return index,missing
  items=["minecraft:air"]*100+["minecraft:stone"]+["minecraft:air"]*100+["minecraft:dirt"]
  self.assertEqual(step(items,0,False),(100,False))
  self.assertEqual(step(items,100,True,True),(201,False))
 def test_build_order_and_gates(self):
  s=WF.read_text(encoding="utf-8")
  for t in ("test_v173_ingame_392.py","apply-map-full-height-392.py",
            "apply-blueprint-visible-392.py","apply-printer-speed-skip-air-392.py",
            "B392_MAP_CEILING","B392_BLUEPRINT_CACHE","B392_SKIP_ONCE"):
   self.assertIn(t,s)
  self.assertLess(s.index("apply-blueprint-printer-state-cache-391.py"),
                  s.index("apply-map-full-height-392.py"))
if __name__=="__main__": unittest.main()
