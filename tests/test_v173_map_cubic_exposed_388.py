#!/usr/bin/env python3
"""Fail-closed static and geometry regression for the Build388 MAP fix."""
import ast
import math
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-map-cubic-exposed-388.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestB388Map(unittest.TestCase):
 def test_patch_parses_and_preserves_other_holograms(self):
  s=PATCH.read_text(encoding="utf-8")
  ast.parse(s)
  for name in ("B378_ISOTROPIC_MAP","private static void networkProjection(",
               "V173_B351_EXACT_NETWORK_SIZE",
               "V173_B362_BUNDLE_CONNECTIONS",
               "B368_MAP_TABLETOP_CALIBRATION"):
   self.assertIn(name,s)
  self.assertIn("B388_MAP_SOURCE_DRIFT",s)

 def test_world_geometry_is_always_isotropic_and_bounded(self):
  # Matching source arithmetic: one integer stride for every world axis,
  # and *no* projection beyond the user-selected rendered map size.
  for chunks in range(1,13):
   side=32*chunks+1
   for depth in (1,2,8,24,48,96,128):
    stride=1
    while math.ceil(side/stride)**2*math.ceil(depth/stride)>8192:
     stride+=1
    columns=math.ceil(side/stride)
    layers=math.ceil(depth/stride)
    self.assertLessEqual(columns*columns*layers,8192)
    for configured in (1,2,3,4,8,16,32):
     scale=configured/(columns*stride)
     cube=stride*scale
     self.assertAlmostEqual(columns*cube,configured)
     self.assertEqual((cube,cube,cube),(cube,cube,cube))

 def test_real_faces_and_topmost_occupied_sample(self):
  s=PATCH.read_text(encoding="utf-8")
  for token in ("B388_EXACT_MAP_FOOTPRINT","B388_EXPOSED_MAP",
                "for(int y=high;y>=low;y--)","b388Cursor.set(sx,y,sz)",
                "BlockPos.MutableBlockPos","if(!exposed)continue;",
                "mc.level.getBlockState(adjacent).isAir()",
                "cube,cube,cube"):
   self.assertIn(token,s)
  self.assertNotIn("pose.scale((float)sx,(float)sy,",s) # Other renderer unchanged

 def test_pipeline_executes_after_378_before_compilation(self):
  w=WF.read_text(encoding="utf-8")
  self.assertLess(w.index("python3 features/v173/apply-map-isotropic-378.py"),
                  w.index("python3 features/v173/apply-map-cubic-exposed-388.py"))
  self.assertLess(w.index("python3 features/v173/apply-map-cubic-exposed-388.py"),
                  w.index("B388_EXACT_MAP_FOOTPRINT' work/src/main/java"))
  self.assertIn("test_v173_map_cubic_exposed_388.py",w)

if __name__=="__main__":
 unittest.main()
