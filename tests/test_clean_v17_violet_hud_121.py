#!/usr/bin/env python3
"""Build121: violet unframed FE meter next to hunger with proper low-power colors."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-violet-hud-121.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class VioletHUD121(unittest.TestCase):
 def test_python_syntax(self):ast.parse(PATCH)
 def test_exact_requested_hud_only(self):
  for marker in (
   "BUILD121_UNFRAMED_VIOLET_FE_HUD",
   "getGuiScaledWidth()/2+10",
   "getGuiScaledHeight()-52",
   "0xffbf80ff",
   "0xffffdc45",
   "0xffff4545",
   "fraction<0.10D",
   "fraction<0.25D",
   "0x66372a48",
   "jetThrusters(ClientTickEvent.Post event)",
  ):
   self.assertIn(marker,PATCH,marker)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorSuitWorld.java",PATCH)
  self.assertNotIn("PowerArmorShieldClient.java",PATCH)
 def test_workflow_order(self):
  self.assertLess(WF.index("apply-power-armor-shield-flight-pose-120.py"),
                  WF.index("apply-power-armor-violet-hud-121.py"))
  self.assertIn("BUILD121_UNFRAMED_VIOLET_FE_HUD PASS",WF)
if __name__=="__main__":unittest.main()
