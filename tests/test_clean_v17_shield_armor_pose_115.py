#!/usr/bin/env python3
"""Build115: armor-matched bone transforms and slow energy membrane flow."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-pose-locked-shield-115.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ArmorPose115(unittest.TestCase):
 def test_patch_python(self):ast.parse(PATCH)
 def test_exact_avatar_joint_space_and_pulse(self):
  for marker in (
    "BUILD115_ARMOR_POSE_LOCK",
    "stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));",
    "stack.scale(-1.0F,-1.0F,1.0F);",
    "stack.translate(0.0F,-1.501F,0.0F);",
    "s.count('submitPart(stack,collector,model.')==6",
    "joint.translateAndRotate(stack);",
    "phase*phase*(3F-2F*phase)",
    "Math.sin(time*.042D)",
    "Math.min(247,(int)(41F+58F*breathe+157F*impact))",
    ".setColor(92,194,255,alpha)",
    "s.count(\"stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));\")==1",
  ):
   self.assertIn(marker,PATCH,marker)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorRuntime.java",PATCH)
 def test_workflow(self):
  self.assertLess(WF.index("apply-power-armor-shield-player-facing-114.py"),
                  WF.index("apply-power-armor-pose-locked-shield-115.py"))
  self.assertIn("BUILD115_ARMOR_POSE_LOCK PASS",WF)
if __name__=="__main__":unittest.main()
