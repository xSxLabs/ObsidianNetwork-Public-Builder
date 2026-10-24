#!/usr/bin/env python3
"""Build111: Draconic-style silhouette must track the actual avatar model joints."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shaped-shield-111.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class ArmorShapedShield111(unittest.TestCase):
 def test_valid_source(self):ast.parse(PATCH)
 def test_one_real_bone_following_energy_membrane_per_part(self):
  for part in ("head","body","rightArm","leftArm","rightLeg","leftLeg"):
   self.assertIn("model."+part+",",PATCH)
  self.assertIn("joint.translateAndRotate(stack);",PATCH)
  self.assertIn("stack.pushPose();",PATCH)
  self.assertIn("stack.popPose();",PATCH)
  self.assertIn("getRenderer().getModel()",PATCH)
  self.assertIn("submitCustomGeometry(stack,SHIELD_RENDER",PATCH)
  self.assertIn("square(Math.cos(latitude),exponent)",PATCH)
  self.assertIn("PowerArmorRuntime.tier(armor,i)!=tier",PATCH)
  self.assertIn("EnergyTool.energy(armor)<20L",PATCH)
  self.assertIn('id.equals("energy_shield")',PATCH)
  self.assertIn("wearer.hurtTime",PATCH)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorRuntime.java",PATCH)
  self.assertNotIn("mc.level.addParticle(",PATCH)
 def test_overlay_order_and_in_game_guard(self):
  self.assertLess(WF.index("apply-power-armor-shield-shell-106.py"),WF.index("apply-power-armor-shaped-shield-111.py"))
  self.assertIn("BUILD111_ARMOR_SHAPED_SHIELD",WF)
if __name__=="__main__":unittest.main()
