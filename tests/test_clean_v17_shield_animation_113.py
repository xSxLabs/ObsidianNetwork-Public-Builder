#!/usr/bin/env python3
"""Build113: shield no longer horizontally mirrored; preserve Build112 orientation."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shield-animation-113.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Shield113(unittest.TestCase):
 def test_valid_python(self):ast.parse(PATCH)
 def test_change_only_horizontal_flip(self):
  for snippet in ('BUILD113_UNMIRRORED_ANIMATION',
                  'stack.scale(1.0F,-1.0F,1.0F);',
                  'stack.translate(0.0F,-1.501F,0.0F);',
                  'joint.translateAndRotate(stack);',
                  "s.count('submitPart(stack,collector,model.')==6",
                  'head>torso>boot>0.0'):
   self.assertIn(snippet,PATCH)
  self.assertNotIn('PowerArmorEnergyShield.java',PATCH)
  self.assertNotIn('PowerArmorRuntime.java',PATCH)
 def test_correct_order(self):
  self.assertIn('python3 features/v17/apply-power-armor-shield-animation-113.py',WF)
  self.assertLess(WF.index('apply-power-armor-shield-orientation-112.py'),WF.index('apply-power-armor-shield-animation-113.py'))
  self.assertIn("BUILD113_UNMIRRORED_ANIMATION",WF)
if __name__=="__main__":unittest.main()
