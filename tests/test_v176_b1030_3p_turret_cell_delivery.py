#!/usr/bin/env python3
"""B1030 regression contracts. Static only; Minecraft ingame test still needed."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v176/apply-v176-b1030-3p-turret-cell-delivery.py").read_text()
class Contracts(unittest.TestCase):
 def test_syntax(self):ast.parse(SRC)
 def test_player_world_one_submitter(self):
  self.assertIn("single reliable 3P gun submitter",SRC)
  self.assertIn(" @Override public void submit(",SRC)
  self.assertIn(" @SubscribeEvent public static void wornFallback(",SRC)
  self.assertIn("xsxGunPose.translate(0.0F,1.5F,0.0F)",SRC)
  self.assertIn("drawArm(xsxGunPose",SRC)
  self.assertIn("armedForAttack(player)",SRC)
 def test_turret_no_invisible_guard_and_right_arm(self):
  for marker in ("XSX_STAND_RENDER_ID","state.entityType!=EntityType.ARMOR_STAND",
   "suit.getRightArmPose().x()","xsxSuitPose.scale(-1.0F,-1.0F,1.0F)",
   "drawArm(xsxSuitPose","stand.isInvisible()"):
   self.assertIn(marker,SRC)
 def test_only_matching_drives(self):
  for marker in ("WorldTopologyBridge.runtimeForAccessory",
   "WorldTopologyBridge.runtimeForTerminal",
   "WorldTopologyBridge.runtimeForDrive",
   "WorldTopologyBridge.runtimeForController",
   "nextNet!=identity","backing.setItem(target,one);",
   "carried.shrink(1);","Cell in verbundenem Drive installiert"):
   self.assertIn(marker,SRC)
if __name__=="__main__":unittest.main()
