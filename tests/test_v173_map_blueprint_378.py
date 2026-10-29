#!/usr/bin/env python3
"""B378 regression guards for MAP projection and large Blueprints."""
import ast
import math
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"features/v173/apply-map-isotropic-378.py"
LIMITS=ROOT/"features/v173/apply-blueprint-limits-378.py"
CODEC=ROOT/"features/v173/apply-blueprint-compression-378.py"
CACHE=ROOT/"features/v173/apply-blueprint-cache-378.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestB378(unittest.TestCase):
 def test_python_syntax(self):
  for p in (MAP,LIMITS,CODEC,CACHE):
   ast.parse(p.read_text(encoding="utf-8"))
 def test_true_xyz_cubes_across_all_radius_depth(self):
  s=MAP.read_text(encoding="utf-8")
  for tag in ("B378_ISOTROPIC_MAP","final double cube=stride*scale;",
              "cube,cube,cube","be.holoMapSize()",
              "private static void networkProjection(",
              "B368_MAP_TABLETOP_CALIBRATION"):
   self.assertIn(tag,s)
  for radius_chunks in range(1,13):
   side=32*radius_chunks+1
   for height in (1,8,32,48,128):
    stride=1
    while math.ceil(side/stride)**2*math.ceil(height/stride)>4096:
     stride+=1
    self.assertLessEqual(math.ceil(side/stride)**2*math.ceil(height/stride),4096)
    for rendered_width in (1,2,4,16,32):
     edge=stride*(rendered_width/side)
     self.assertGreater(edge,0)
     self.assertEqual((edge,edge,edge),(edge,edge,edge))
 def test_map_size_is_independent_and_persisted(self):
  s=MAP.read_text(encoding="utf-8")
  for phrase in ("holoMapSize","holo_map_size","B378_MAP_SIZE_GUI",
                 'if("map".equals(mode))holoMapSize',
                 'mapSize.visible=map',
                 'val(mapSize,4,1,32)'):
   self.assertIn(phrase,s)
 def test_blueprint_over16_with_server_safety_limits(self):
  s=LIMITS.read_text(encoding="utf-8")
  for phrase in ("MAX_SIZE=Integer.MAX_VALUE","MAX_BLOCKS",
                 "xsxlabs.blueprint.maxBlocks",
                 "long volume=(long)sx*sy*sz",
                 "NetworkBlueprintPreviewClient.java",
                 "BlueprintPlacementPayload.java"):
   self.assertIn(phrase,s)
  self.assertIn("Blueprint too large for available server memory",s)
  self.assertIn("volume<=0L||volume>NetworkBlueprintItem.MAX_BLOCKS",s)
 def test_item_storage_and_preview_memory(self):
  s=CODEC.read_text(encoding="utf-8")
  self.assertIn("GZIPInputStream",s)
  self.assertIn("GZIPOutputStream",s)
  self.assertIn("if(!raw.startsWith",s) # old items remain readable
  s=CACHE.read_text(encoding="utf-8")
  self.assertIn("b378BlueprintBlocks",s)
  self.assertIn("b378PreviewBlocks",s)
  self.assertIn("ItemStack.isSameItemSameComponents",s)
 def test_ci_registers_all_changes(self):
  w=WF.read_text(encoding="utf-8")
  for name in ("apply-map-isotropic-378.py","apply-blueprint-limits-378.py",
               "apply-blueprint-compression-378.py","apply-blueprint-cache-378.py",
               "test_v173_map_blueprint_378.py"):
   self.assertIn(name,w)

if __name__=="__main__":
 unittest.main()
