#!/usr/bin/env python3
"""Static source contracts; real GUI/rendering still need Minecraft ingame test."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1028-mg-turret-cells-balance.py"
class B1028Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=PATCH.read_text(encoding="utf-8")
 def test_script_parses(self):ast.parse(self.s,str(PATCH))
 def test_first_person_and_world_matrices(self):
  for x in ("xsxTurretPose.translate(0.0F,1.5F,0.0F);",
            "xsxTurretPose.scale(-1.0F,-1.0F,1.0F);",
            "event.setCanceled(true);","nodes.submitModelPart(BARREL,pose",
            "getParentModel().rightArm"):
   self.assertIn(x,self.s)
 def test_turret_follows_and_aims(self):
  for x in ("walkingPose(suit,walking,turret&&hasModule(suit)",
            "suit.setYRot(xsxYaw)","suit.setYBodyRot(xsxYaw)",
            "suit.setYHeadRot(xsxYaw)","suit.setRightArmPose",
            "V176MicroMgRules.canTurretFire"):
   self.assertIn(x,self.s)
 def test_cell_transfer_is_physical_and_balanced(self):
  for x in ("for(int pad=0;pad<8;pad++)",
            "instanceof dev.obsidiannetwork.item.StorageCellItem",
            "instanceof dev.obsidiannetwork.item.EquipmentCellItem",
            "if(slotId>=0&&slotId<8)",
            "backing.setItem(target,one);","carried.shrink(1);",
            "runtimeForDrive(level,next)","own==identity",
            "WorldTopologyBridge.xsxCellTerminalDrives"):
   self.assertIn(x,self.s)
 def test_damage_and_recipe(self):
  self.assertIn("DAMAGE_HP=4.0f;",self.s)
  self.assertIn("FE_PER_SHOT=3000L",self.s)
  self.assertIn('"minecraft:netherite_block"',self.s)
  self.assertIn('"minecraft:nether_star"',self.s)
if __name__=="__main__":unittest.main()
