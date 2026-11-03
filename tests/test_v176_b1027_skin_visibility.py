#!/usr/bin/env python3
"""Source contracts for v1.7.6 B1027 player-skin visibility gate."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1027-hide-skin-worn.py"

class SkinVisibility(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.src=PATCH.read_text(encoding="utf-8")
 def test_patch_parses_and_is_client_only(self):
  ast.parse(self.src,str(PATCH))
  self.assertIn('data["client"].append("V176WornSkinRenderTypeMixin")',self.src)
  self.assertIn('@Mixin(LivingEntityRenderer.class)',self.src)
  self.assertIn('state instanceof AvatarRenderState avatar',self.src)
 def test_skin_pass_only_and_auto_restore(self):
  for marker in ('V176AttackRenderState.TIER','tier!=null&&tier>=1&&tier<=24',
     'cir.setReturnValue(null)', 'state.setRenderData(TIER,0);',
     'int tier=V176MicroMgVisualClient.tier(player);'):
   self.assertIn(marker,self.src)
  self.assertNotIn('player.setInvisible(',self.src)
  self.assertNotIn('model.rightArm.visible=false',self.src)
  self.assertNotIn('event.setCanceled(true); // player',self.src)
 def test_first_person_bare_arm_not_weapon(self):
  self.assertIn('RenderArmEvent',self.src)
  self.assertIn('V176MicroMgVisualClient.tier(player)>0',self.src)
  self.assertIn('event.setCanceled(true);',self.src)
  self.assertNotIn('RenderHandEvent event',self.src)
  self.assertNotIn('V176MicroMgLayer.java',self.src)

if __name__=="__main__":
 unittest.main()
