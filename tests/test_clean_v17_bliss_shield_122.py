#!/usr/bin/env python3
"""Build122 source regression: cutout honeycomb avoids Iris/Bliss transparency."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shader-cutout-122.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class BlissSafeShield122(unittest.TestCase):
 def test_patch_syntax(self):ast.parse(PATCH)
 def test_render_target_and_binary_alpha(self):
  for marker in (
   "BUILD122_BLISS_SAFE_ARMOR_CUTOUT",
   "RenderTypes.armorCutoutNoCull(SKIN)",
   ".setColor(red,green,blue,255)",
   ".setLight(0x00E000E0)",
   "BUILD122_CUTOUT_BREATH",
   "opacity=255 if edge else 0",
   "all(a in (0,255) for row in pixels for a in row[4::4])",
   "state.isFallFlying",
   "src.count(\"submitPart(stack,collector,model.\")==6"):
   self.assertIn(marker,PATCH)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorSuitWorld.java",PATCH)
 def test_stays_after_build121_and_guarded(self):
  self.assertLess(WF.index("apply-power-armor-violet-hud-121.py"),
                  WF.index("apply-power-armor-shader-cutout-122.py"))
  self.assertIn("BUILD122_BLISS_SAFE_ARMOR_CUTOUT PASS",WF)
if __name__=="__main__":unittest.main()
