#!/usr/bin/env python3
"""Build112: render transform regression and strict no-server/FE changes."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shield-orientation-112.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class Orientation112(unittest.TestCase):
 def test_valid_python(self):
  ast.parse(PATCH)
 def test_flip_full_coordinate_frame_not_just_vertex(self):
  for v in ('stack.pushPose();','stack.scale(-1.0F,-1.0F,1.0F);',
            'stack.translate(0.0F,-1.501F,0.0F);','stack.popPose();',
            'source.count("submitPart(stack,collector,model.")==6',
            'head=1.501-(-3.9)/16','torso=1.501-(5.9)/16',
            'boots=1.501-(12+5.8)/16','2.0>head>torso>boots>0.0'):
   self.assertIn(v,PATCH)
  # Do not "correct" inverted head by flipping only Y at the vertices:
  self.assertNotIn('vy=-vy',PATCH)
  self.assertNotIn('PowerArmorEnergyShield.java',PATCH)
  self.assertNotIn('PowerArmorRuntime.java',PATCH)
 def test_build_order(self):
  self.assertIn('python3 features/v17/apply-power-armor-shield-orientation-112.py',WF)
  self.assertLess(WF.index('apply-power-armor-shaped-shield-111.py'),WF.index('apply-power-armor-shield-orientation-112.py'))
  self.assertIn('BUILD112_MODEL_COORDS_PASS',WF)
if __name__=="__main__":unittest.main()
