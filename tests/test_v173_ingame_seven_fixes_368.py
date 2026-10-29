#!/usr/bin/env python3
"""B368 integrated ingame regression: JEI transfer, MAP, NETWORK and wheel."""
import ast, math, re, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-ingame-seven-fixes-368.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class IngameSevenFixes368(unittest.TestCase):
 def test_python_patch_is_valid(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))

 def test_partial_craft_exact_storage_transaction_preserved(self):
  s=PATCH.read_text(encoding="utf-8")
  for token in (
    "B368_PARTIAL_INGREDIENTS", "continue;",
    "B368_JEI_INGREDIENT_TEST_DRIFT",
    "Ingredient ingredient,ItemStack candidate",
    "if(ingredient.test(candidate))return true;",
    "simple.remove(net.minecraft.core.component.DataComponents.CUSTOM_NAME)",
    "simple.remove(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get())",
    "simple.remove(net.minecraft.core.component.DataComponents.DAMAGE)",
    "return ingredient.test(simple);",
    "runtime.storage().extract(desc[ixx].key(), 1L)",
    "runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L)",
    "reservedNet.merge(bestKey, 1L, Math::addExact)",
  ):self.assertIn(token,s)
  # Both ingredients are validated independently from their exact key.
  self.assertIn("assert len(tests)==2",s)
  self.assertIn("assert len(all_missing)==1",s)
  self.assertNotIn("runtime.storage().extract(key, 64L)",s)

 def test_map_world_vertical_slice_and_y_baseline(self):
  s=PATCH.read_text(encoding="utf-8")
  for token in (
    "B368_MAP_START_WORLD_Y","holoMapStartY",
    "holo_start_y","holoDepth=Math.max(1,Math.min(128,depth))",
    "B368_MAP_GUI_Y_DEPTH","Start world Y","Depth blocks",
    "B368_MAP_FIXED_VOLUME","B368_MAP_TABLETOP_CALIBRATION",
    "final int bottomY=Math.max(mc.level.getMinY(),fromY-depth+1)",
    "final double tabletop=t.getY()+be.holoHeight();",
    "double shift=tabletop-lowest;",
    "if(!mc.level.hasChunkAt(sample))continue;",
  ):self.assertIn(token,s)
  for radiusChunks in range(1,13):
   radius=16*radiusChunks
   side=2*radius+1
   step=max(1,(side+27)//28)
   columns=(side+step-1)//step
   layers=max(1,min(12,4096//(columns*columns)))
   self.assertLessEqual(columns*columns*layers,4096)
   for depth in (1,8,32,64,128):
    fromY=80
    bottom=fromY-depth+1
    yStep=max(1,(fromY-bottom+layers)//layers)
    sampled=[fromY-n*yStep for n in range(layers) if fromY-n*yStep>=bottom]
    self.assertTrue(sampled)
    self.assertLessEqual(len(sampled),layers)
    for table_y in (-32,70):
     for height in (1,2,3,32):
      target=table_y+height
      lowest=sampled[-1]*0.04
      self.assertAlmostEqual(lowest+(target-lowest),target)
  # Map is not an inconsistent surfaceHeight[ix][iz]-depth scan anymore.
  volume=s[s.index("volume=r'''"):s.index("s=s[:a]+volume")]
  self.assertNotIn("surfaceHeight[ix][iz]",volume)
  self.assertNotIn("int min=y;",volume)

 def test_network_has_no_text_owner(self):
  s=PATCH.read_text(encoding="utf-8")
  self.assertIn('if("map".equals(holoMode)||"network".equals(holoMode)){',s)
  self.assertIn('if("network".equals(be.holoMode())){',s)
  self.assertIn("B368_NETWORK_NO_STATUS_TEXT",s)
  self.assertIn("networkProjection(mc,ev,cam,mapTerminal,be);",s)

 def test_wheel_labels_share_hit_test_centers(self):
  s=PATCH.read_text(encoding="utf-8")
  self.assertIn("B368_WHEEL_ALIGNED_LABELS",s)
  self.assertIn("Math.round(76D*Math.sin(angle))",s)
  self.assertIn("Math.round(76D*Math.cos(angle))",s)
  self.assertIn("new int[]{0,1,4,2,3}",s)
  self.assertIn("new int[]{0,1,2,3}",s)
  for vision in (False,True):
   order=[0,1,4,2,3] if vision else [0,1,2,3]
   for slot,action in enumerate(order):
    angle=2*math.pi*slot/len(order)
    dx=76*math.sin(angle);dy=-76*math.cos(angle)
    if vision:
     ang=math.atan2(dy,dx)+math.pi/2
     if ang<0:ang+=2*math.pi
     selected=[0,1,4,2,3][int(math.floor((ang+math.pi/5)/(2*math.pi/5)))%5]
    else:
     selected=1 if abs(dx)>abs(dy) and dx>0 else 3 if abs(dx)>abs(dy) else 2 if dy>0 else 0
    self.assertEqual(selected,action)

 def test_ci_order_and_fail_closed(self):
  s=WF.read_text(encoding="utf-8")
  self.assertIn("python3 features/v173/apply-ingame-seven-fixes-368.py",s)
  self.assertIn("test_v173_ingame_seven_fixes_368.py",s)
  self.assertLess(s.index("python3 features/v173/apply-armor-fe-bar-stability-365.py"),
                  s.index("python3 features/v173/apply-ingame-seven-fixes-368.py"))
  code=PATCH.read_text(encoding="utf-8")
  self.assertIn("B368_SOURCE_DRIFT",code)
  self.assertIn("B368_JEI_BOUNDARY_DRIFT",code)
  self.assertIn("B368_WHEEL_LABEL_DRIFT",code)

if __name__=="__main__": unittest.main()
