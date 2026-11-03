#!/usr/bin/env python3
"""B1032 static contracts; compiled Java and user ingame verification required."""
import ast,unittest
from pathlib import Path
SRC=(Path(__file__).resolve().parents[1]/"features/v176/apply-v176-b1032-layered-guns-physical-drive-cells.py").read_text()
class B1032(unittest.TestCase):
 def test_python_patch_syntax(self):ast.parse(SRC)
 def test_player_inherits_body_yaw(self):
  for marker in ("V176MicroMgLayer.java"," @Override public void submit(",
     "pose.last().pose()","getParentModel().rightArm",
     "V176MicroMgVisualClient.drawArm(xsxWeaponPose",
     "Intentional no-op. V176MicroMgLayer.submit"):
   self.assertIn(marker,SRC)
 def test_turret_uses_native_equipment_and_rotation(self):
  for marker in ("V176MicroMgStandLayer.java",
     "RenderLayer<ArmorStandRenderState,ArmorStandModel>",
     "state.chestEquipment","state.headEquipment","state.rightArmPose.x()",
     "getParentModel().rightArm,variant,1.0F",
     "getRenderer(EntityType.ARMOR_STAND)",
     "XSXLABS_B1032_TURRET_LAYER_REGISTERED"):
   self.assertIn(marker,SRC)
 def test_cells_accept_only_same_network_with_real_drive_write(self):
  for marker in ("if(nextNet!=null&&nextNet!=identity)continue;",
     "currentNet!=identity","physicalDrives(world,terminal,identity)",
     "WorldTopologyBridge.xsxCellTerminalDrives",
     "backing.setItem(target,one);","carried.shrink(1);",
     "XSXLABS_B1032_CELL_INPUT"):
   self.assertIn(marker,SRC)
if __name__=="__main__":unittest.main()
