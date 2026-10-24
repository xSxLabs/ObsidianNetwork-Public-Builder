#!/usr/bin/env python3
"""Build114: armor forcefield must turn with PLAYER, not cardinal-fixed world."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shield-player-facing-114.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class FollowBodyFacing114(unittest.TestCase):
 def test_valid_patch(self):ast.parse(PATCH)
 def test_avatar_yaw_and_exact_cardinals(self):
  for text in (
   "com.mojang.math.Axis;",
   "stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));",
   'stack.scale(1.0F,-1.0F,1.0F);',
   'stack.translate(0.0F,-1.501F,0.0F);',
   'model_front(180)==(0,-1)',
   'model_front(0)==(0,1)',
   'model_front(-90)==(1,0)',
   'model_front(90)==(-1,0)',
   's.count("submitPart(stack,collector,model.")==6',
   'joint.translateAndRotate(stack);',
  ):self.assertIn(text,PATCH,text)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorRuntime.java",PATCH)
 def test_correct_ci_overlay_order(self):
  self.assertIn("python3 features/v17/apply-power-armor-shield-player-facing-114.py",WF)
  self.assertLess(WF.index("apply-power-armor-shield-animation-113.py"),
                  WF.index("apply-power-armor-shield-player-facing-114.py"))
  self.assertIn("BUILD114_BODY_FACING_LOCK PASS",WF)

if __name__=="__main__":unittest.main()
