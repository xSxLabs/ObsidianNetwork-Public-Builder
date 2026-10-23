#!/usr/bin/env python3
"""Build63 contracts for actual one-entity GeckoLib + suit entry + Apotheosis."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v17/apply-power-armor-geckolib-world-63.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class WorldEntity63(unittest.TestCase):
 def test_overlay_after_real_transfer_62(self):
  ast.parse(SRC)
  self.assertIn("python3 features/v17/apply-power-armor-geckolib-world-63.py",WF)
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-critical-62.py"),
                  WF.index("python3 features/v17/apply-power-armor-geckolib-world-63.py"))
 def test_one_persistent_geckolib_owner_and_real_click(self):
  for thing in ("extends ArmorStand implements GeoEntity",
   "PowerArmorSuitWorld.tryEnter(server,getId())",
   "public boolean isPickable(){return true;}",
   "public InteractionResult interact(Player player,InteractionHand hand,Vec3 location)",
   "Entity#interactAt was removed",
   "setNoGravity(true);",
   "PowerArmorStand stand=new PowerArmorStand(type,level)",
   "if(stand instanceof PowerArmorStand worldSuit)",
   "worldSuit.animate(entering);",
   "worldSuit.stopAnimation();"):
   self.assertIn(thing,SRC)
 def test_real_gear_and_geckolib_asset_reuse(self):
  self.assertIn("ARMOR_VISUAL_ENTITIES.registerEntityType",SRC)
  self.assertIn("new com.geckolib.model.DefaultedEntityGeoModel<>(",SRC)
  self.assertIn('"power_armor_visual_mk1"',SRC)
  self.assertIn('"power_armor_visual_mk2"',SRC)
  self.assertIn("registerControllers",SRC)
  self.assertIn("entityData.get(TRANSITION)",SRC)
  self.assertIn("if(transition==0)return PlayState.STOP;",SRC)
  self.assertIn("no second phantom render layer",SRC)
 def test_apotheosis_armor_slot_tag_compatibility(self):
  for name in ("head_armor","chest_armor","leg_armor","foot_armor"):
   self.assertIn('"'+name+'"',SRC)
  self.assertIn("power_armor_mk2_{part}",SRC)
  self.assertIn('if item not in doc["values"]',SRC)
if __name__=="__main__":unittest.main()
