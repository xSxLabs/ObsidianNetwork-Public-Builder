import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-vision-holo-polish-351.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestVisionHoloPolish351(unittest.TestCase):
 def test_syntax(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
 def test_network_projection_size_scales_both_directions(self):
  s=PATCH.read_text(encoding="utf-8")
  for marker in (
    'V173_B351_EXACT_NETWORK_SIZE',
    'double scale=(double)Math.max(1,be.holoWidth())/',
    'Math.max(1D,Math.max(dx,Math.max(dy,dz)))',
    'render.write_text(s.replace(old,new,1)',
  ):
   self.assertIn(marker,s)
  self.assertNotIn('Math.min(1D,be.holoWidth()',s.split("new='''")[1])
  for extent in (1,2,4,8,16,32):
   for size in (1,5,8,16,32):
    scale=size/extent
    self.assertAlmostEqual(scale*extent,size)
  self.assertGreater(16/2,1.0)
 def test_wheel_is_only_vision_toggle_and_reports_both_states(self):
  s=PATCH.read_text(encoding="utf-8")
  for marker in ('V173_B351_VISION_FEEDBACK','toggleFromWheel()',
                 'Network Vision: ON','Network Vision: OFF',
                 'sendOverlayMessage','if(!ready())',
                 'Network Vision: upgrade not installed'):
   self.assertIn(marker,s)
  self.assertNotIn('GLFW_KEY_',s)
 def test_readonly(self):
  s=PATCH.read_text(encoding="utf-8")
  for forbidden in ('setBlockAndUpdate(', 'addFreshEntity(', 'sendBlockUpdated(', 'NetworkRuntime.insert(', 'EnergyTool.receive('):
   self.assertNotIn(forbidden,s)
 def test_workflow(self):
  s=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn('python3 features/v173/apply-vision-holo-polish-351.py',s)
  self.assertIn('test_v173_vision_holo_polish_351.py',s)
  self.assertLess(s.index('python3 features/v173/apply-hologram-network-3d-348.py'),
                  s.index('python3 features/v173/apply-vision-holo-polish-351.py'))

if __name__=="__main__": unittest.main()
