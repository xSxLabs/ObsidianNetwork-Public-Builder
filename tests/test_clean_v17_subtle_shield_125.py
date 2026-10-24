#!/usr/bin/env python3
"""Build125 regression: retain shader cutout and dim the energy field."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-subtle-shield-125.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class SubtleShield125(unittest.TestCase):
 def test_patch_parses(self):ast.parse(PATCH)
 def test_shader_pipeline_and_damage_remain(self):
  for phrase in ("BUILD125_SUBTLE_IDLE_AND_HIT_FLASH",
   "BUILD122_BLISS_SAFE_ARMOR_CUTOUT",
   "RenderTypes.armorCutoutNoCull(SKIN)",
   "RenderTypes.entityTranslucent(SKIN)",
   "float easedGlow=energyGlow*energyGlow;",
   "int blue=(int)(42F+213F*easedGlow);",
   ".setColor(red,green,blue,255)",
   "distance<=.45",
   ".045<coverage<.065",
   "BUILD125_SUBTLE_SHIELD PASS",
   "state.isFallFlying",
   "src.count(\"submitPart(stack,collector,model.\")==6"):
   self.assertIn(phrase,PATCH,phrase)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorBuild98Client.java",PATCH)
 def test_workflow_order(self):
  self.assertLess(WF.index("apply-power-armor-multiplayer-jets-124.py"),
                  WF.index("apply-power-armor-subtle-shield-125.py"))
  self.assertIn('BUILD125_SUBTLE_SHIELD PASS',WF)
if __name__=="__main__":unittest.main()
