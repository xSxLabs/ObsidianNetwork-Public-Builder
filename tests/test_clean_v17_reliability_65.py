#!/usr/bin/env python3
"""Build65 regression invariants, synthesize generated-code patterns."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/v17/apply-power-armor-reliability-65.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Reliable65(unittest.TestCase):
 def test_valid_source_and_applied_after_64(self):
  ast.parse(S)
  self.assertIn("apply-power-armor-reliability-65.py",WF)
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-geckolib-world-63.py"),WF.index("python3 features/v17/apply-power-armor-reliability-65.py"))
 def test_restore_vanilla_real_world_entity_with_geo_visual(self):
  self.assertIn("ArmorStand stand=new ArmorStand(level,pos.getX()",S)
  self.assertIn("stand.setInvisible(false)",S)
  self.assertIn("stand.setInvisible(true);"+" not in w",S)
  self.assertIn("PowerArmorVisualEntity.java",S)
 def test_client_not_cancelled_and_server_validation(self):
  self.assertIn("if(event.getEntity() instanceof ServerPlayer player)",S)
  self.assertIn("stand.getBoundingBox().getCenter().subtract(eye).normalize().dot(look)>0.90D",S)
  self.assertIn("new PowerArmorEnterPayload(-1)",S)
  self.assertIn("mine(stand,player)&&full(stand)",S)
 def test_valid_armor_animation_and_diagnostics(self):
  self.assertIn("float spread=55F*open;",S)
  self.assertIn('?"animation.power_armor.open":"animation.power_armor.close"',S)
  self.assertIn('Commands.literal("status")',S)
  self.assertIn("owned_stands=",S)
if __name__=="__main__":unittest.main()
