#!/usr/bin/env python3
"""Build120: fix Build119 HUD patch indentation + inherit vanilla flight pose."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FLIGHT=(ROOT/"features/v17/apply-power-armor-shield-flight-pose-120.py").read_text(encoding="utf-8")
HUD=(ROOT/"features/v17/apply-power-armor-compact-hud-119.py").read_text(encoding="utf-8")
ORIGINAL=(ROOT/"features/v17/apply-power-armor-build98.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class ShieldFlight120(unittest.TestCase):
 def test_python(self):ast.parse(FLIGHT);ast.parse(HUD)
 def test_glide_follows_avatar_model_root(self):
  for v in ("BUILD120_ELYTRA_SHIELD_POSE","state.isFallFlying",
            "state.fallFlyingScale()",
            "Axis.XP.rotationDegrees(glide*(-90.0F-state.xRot))",
            "state.shouldApplyFlyingYRot",
            "Axis.YP.rotation(state.flyingYRot)",
            "state.isVisuallySwimming",
            "s.count(\"submitPart(stack,collector,model.\")==6"):
   self.assertIn(v,FLIGHT,v)
  self.assertNotIn("PowerArmorEnergyShield.java",FLIGHT)
  self.assertNotIn("PowerArmorSuitWorld.java",FLIGHT)
 def test_hud_matches_generated_build98(self):
  start=HUD.index("old='''")+7
  end=HUD.index("'''\\nnew=",start) if "'''\\nnew=" in HUD else HUD.index("'''\nnew=",start)
  fragment=HUD[start:end]
  self.assertIn(fragment,ORIGINAL)
  self.assertIn("getGuiScaledWidth()/2-91",fragment)
  self.assertIn("getGuiScaledHeight()-70",fragment)
 def test_workflow(self):
  self.assertIn("apply-power-armor-compact-hud-119.py",WF)
  self.assertIn("apply-power-armor-shield-flight-pose-120.py",WF)
  self.assertLess(WF.index("apply-power-armor-compact-hud-119.py"),WF.index("apply-power-armor-shield-flight-pose-120.py"))
  self.assertIn("BUILD120_ELYTRA_SHIELD_POSE PASS",WF)
if __name__=="__main__":unittest.main()
