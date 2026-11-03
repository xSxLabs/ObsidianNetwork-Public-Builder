#!/usr/bin/env python3
"""Fast preflight safety contracts for B980 current user issues.
The real Java compilation and 26.1 server tests follow in GitHub Actions.
This test never claims the client world-suit render crash is ingame-fixed.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b980-turret-and-cell-terminal-ingame.py"

class B980Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=PATCH.read_text(encoding="utf-8")

 def test_authoritative_adjacent_topology_and_network_filtered_drives(self):
  s=self.s
  for x in (
   "xsxCellTerminalNetwork(ServerLevel level, BlockPos pos)",
   "runtimeForTerminal(level,neighbor)",
   "runtimeForDrive(level,neighbor)",
   "runtimeForController(level,neighbor)",
   "runtimeForAccessory(level,neighbor)",
   "xsxCellTerminalDrives(",
   "runtimeForDrive(level,pos)==network",
   "level.hasChunkAt(pos)",
   "WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal)",
   "WorldTopologyBridge.xsxCellTerminalDrives(world,network)",
  ):self.assertIn(x,s)

 def test_no_duplicate_cells_and_live_backing(self):
  s=self.s
  self.assertIn('assert cellmenu.index("backing.setItem(targetSlot,one);")<cellmenu.index("carried.shrink(transferred);")',s)
  self.assertIn("backing.setItem(targetSlot,one);",s)
  self.assertIn("if(!ItemStack.matches(inserted,one))",s)

 def test_temporary_diagnostics_and_independent_turret_pose(self):
  s=self.s
  for x in ("XSXLABS_TEMP_B980_TURRET_RENDER",
            "xsxTurretPose=new PoseStack()",
            "new org.joml.Matrix4f(event.getPoseStack().last().pose())",
            'xsxLogTurretPose(stand.getId(),tier,amount,"ENTER")',
            'xsxLogTurretPose(stand.getId(),tier,amount,"EXIT")',
            "xsxWeaponPose=new PoseStack()",
            "frame%100==0",
            "remove after user verifies"):
   self.assertIn(x,s)
  self.assertIn('scope="if(amount>0F && event.getRenderer().getModel() instanceof HumanoidModel<?> model)"',s)
  self.assertIn('method=method.replace(scope,scope+"{",1)',s)

 def test_fp_only_armor_forearm_and_proven_pivot(self):
  s=self.s
  for x in (
   "XSX_POWER_LOWER=xsxPowerForearm()",
   "textures/entity/equipment/humanoid/",
   "nodes.submitModelPart(XSX_POWER_LOWER,pose,armorAtlas",
   "nodes.submitModelPart(upper,pose,skin",
   'assert "nodes.submitModelPart(upper,pose" not in hand',
   "pose.mulPose(interpolated)",
   "nodes.submitModelPart(BARREL,pose"):
   self.assertIn(x,s)

 def test_world_only_slim_barrel_not_1p_modified(self):
  s=self.s
  self.assertIn("XSX_WORLD_BARREL=xsxWorldBarrel()",s)
  self.assertIn("draw=draw.replace(\"nodes.submitModelPart(BARREL,pose\"",s)
  self.assertIn("s=s[:draw_start]+draw+s[draw_end:]",s)
  self.assertIn("pose.translate(0.0F,0.0F,-0.075F)",s)

 def test_purple_crafting_casing_no_cull_and_backpack_lower_bigger(self):
  s=self.s
  self.assertIn('craft=A/"models/block/crafting_terminal.json"',s)
  self.assertIn("ns_violet_glow",s)
  self.assertIn("ns_data_glow_strong",s)
  self.assertIn('model["ambientocclusion"]=False',s)
  self.assertIn('value.pop("cullface",None)',s)
  self.assertIn("pose.scale(1.47F,1.47F,1.47F)",s)
  self.assertIn("1.23F",s)

if __name__=="__main__":unittest.main()
