#!/usr/bin/env python3
"""v1.7.3 map: depth, radius, height, bounded unloaded-chunk safety regression."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v173/apply-map-volumetric-327.py").read_text(encoding="utf8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf8")
class VolumetricMap327(unittest.TestCase):
 def test_script_parses(self):
  ast.parse(SRC)
 def test_full_3d_blocks_not_just_heightfield(self):
  for token in ("V173_VOLUME_MAP_327","maxDepth=48","for(int depth=2;",
                "BlockState real=mc.level.getBlockState(at)","boolean exposed=false",
                "net.minecraft.core.Direction.values()","2D*perBlock",
                "real.getFluidState().isEmpty()?real"):
   self.assertIn(token,SRC,token)
 def test_radius_controls_footprint_height_controls_only_offset(self):
  for token in ("radiusChunks*16","footprint=2.5D+radiusChunks*1.25D",
                "originY=t.getY()-be.holoHeight()+.5D",
                "perBlock=footprint/side"):
   self.assertIn(token,SRC,token)
  self.assertNotIn("be.holoHeight()/(high-low",SRC)
 def test_client_performance_and_unloaded_guard(self):
  for token in ("maxVoxels=4600,maxDepth=48","(side+39)/40",
                "if(!mc.level.hasChunkAt(column))continue",
                "mc.level.hasChunkAt(neighbor)","out.size()<maxVoxels"):
   self.assertIn(token,SRC,token)
 def test_ci_wiring_after_314(self):
  a="python3 features/v173/apply-ingame-roundup-314.py"
  b="python3 features/v173/apply-map-volumetric-327.py"
  self.assertIn(a,WF);self.assertIn(b,WF)
  self.assertLess(WF.index(a),WF.index(b))
  self.assertIn("test_v173_map_volumetric_327.py",WF)
if __name__=="__main__":unittest.main()
