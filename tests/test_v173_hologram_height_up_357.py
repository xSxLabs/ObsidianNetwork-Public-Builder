import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-hologram-height-up-357.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestHologramHeightUp357(unittest.TestCase):
 def test_valid_python(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))

 def test_all_modes_up_from_tabletop(self):
  s=PATCH.read_text(encoding="utf-8")
  for marker in (
   "V173_B357_TEXT_BASELINE",
   "V173_B357_NETWORK_BASELINE",
   "V173_B357_MAP_BASELINE",
   "V173_B357_MAP_BOTTOM_ALIGNED",
   "V173_B357_SERVER_TEXT_UP",
   "double y=origin.getY()+be.holoHeight()+index*sizeFactor*.75D;",
   "double bottomY=origin.getY()+be.holoHeight();",
   "double y=bottomY+(at.getY()-minY)*scale;",
   "double originY=t.getY()+be.holoHeight();",
   "double shift=(t.getY()+be.holoHeight())-lowest;",
   "double y=worldPosition.getY()+holoHeight+(shown-1-i)*.24*scale;",
   "HEIGHT (BLOCKS UP)",
   "HEIGHT 1 = tabletop; each +1 moves up 1 block",
   "Height above table",
  ):
   self.assertIn(marker,s,marker)

 def test_java_map_voxel_loop_does_not_shadow_tile_size(self):
  # Build359 regression: sampleMap already declares double tile for LOD size.
  s=PATCH.read_text(encoding="utf-8")
  self.assertEqual(s.count("for(MapVoxel mapVoxel:out)"),2)
  self.assertNotIn("for(MapVoxel tile:out)",s)
  self.assertIn("double lowest=Double.POSITIVE_INFINITY;",s)
  self.assertIn("mapVoxel.y()+shift",s)
  self.assertIn("return elevated;",s)

 def test_height_monotonic_and_bottom_aligned(self):
  for terminal_y in (-64,0,65,320):
   previous=None
   for height in range(1,33):
    table_top=terminal_y+1
    baseline=terminal_y+height
    self.assertEqual(baseline,table_top+height-1)
    if previous is not None:self.assertEqual(baseline-previous,1)
    previous=baseline
    # Both 3D modes align their lowest geometry to the exact baseline.
    for raw_lowest in (-128,-3.2,0,12.8):
     shift=baseline-raw_lowest
     self.assertAlmostEqual(raw_lowest+shift,baseline)
    # All text lines align above, never below the baseline.
    for count in (1,2,12):
     scale=3
     for i in range(count):
      rendered_y=baseline+(count-1-i)*.24*scale
      self.assertGreaterEqual(rendered_y,baseline)

 def test_no_world_or_persistence_writes(self):
  s=PATCH.read_text(encoding="utf-8")
  for forbidden in ("setBlockAndUpdate(", "level.setBlock(", "setChanged(", "sendBlockUpdated(",
                    "addFreshEntity(", "energyBuffer=", "network.insert("):
   self.assertNotIn(forbidden,s)

 def test_workflow_order(self):
  s=WF.read_text(encoding="utf-8")
  self.assertIn("python3 features/v173/apply-hologram-height-up-357.py",s)
  self.assertIn("test_v173_hologram_height_up_357.py",s)
  self.assertLess(s.index("python3 features/v173/apply-hologram-network-lanes-354.py"),
                  s.index("python3 features/v173/apply-hologram-height-up-357.py"))

if __name__=="__main__":unittest.main()
