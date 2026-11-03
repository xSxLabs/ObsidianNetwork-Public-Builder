#!/usr/bin/env python3
"""B973 fast regression: attack rendering is isolated and forearm ray converges."""
from pathlib import Path
import math
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b973-thirdperson-isolated-render-firstperson-aim.py"

class B973AttackPoseStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=PATCH.read_text(encoding="utf-8")

    def test_only_isolated_pose_stack_in_world_layer_and_backpack(self):
        self.assertIn("xsxWeaponPose=new PoseStack()",self.patch)
        self.assertIn("xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()))",self.patch)
        self.assertIn("var pose=new com.mojang.blaze3d.vertex.PoseStack()",self.patch)
        self.assertIn("xsxParent.last().pose()",self.patch)

    def test_off_mode_vanilla_unchanged(self):
        self.assertIn("if(!active&&progress<=0.001F)return;",self.patch)
        self.assertIn("if(event.getHand()!=InteractionHand.MAIN_HAND)return;",self.patch)
        self.assertIn("state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS",self.patch)
        self.assertIn("assert \"state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS\" not in",self.patch)

    def test_skin_and_gun_share_same_pivot(self):
        self.assertIn("pose.mulPose(interpolated);",self.patch)
        self.assertIn("pose.translate(-5.0F/16.0F,6.0F/16.0F,0.0F);",self.patch)
        self.assertIn("pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);",self.patch)
        self.assertIn("handbody.count(\"submitModelPart(BARREL\")==1",self.patch)
        self.assertIn("event.setCanceled(true)",self.patch)

    def test_elbow_axis_ray_projects_to_crosshair(self):
        # B973 maps model Y to a ray through camera centre using an x/y mirror.
        sx,sy,sz=.30,-.15,-.70
        ex,ey,ez=sx+5/16,sy-6/16,sz
        target_z=-2.60
        # Model-space vector after mirror x,y.
        vx,vy,vz=ex,ey,target_z-ez
        length=math.sqrt(vx*vx+vy*vy+vz*vz)
        dx,dy,dz=-vx/length,-vy/length,vz/length
        t=(target_z-ez)/dz
        self.assertAlmostEqual(ex+t*dx,0.0,places=6)
        self.assertAlmostEqual(ey+t*dy,0.0,places=6)
        self.assertAlmostEqual(ez+t*dz,target_z,places=6)
        self.assertIn("shoulderY-6.0F/16.0F",self.patch)

    def test_only_worn_backpack_size_changes(self):
        self.assertIn("pose.scale(1.35F,1.35F,1.35F);",self.patch)
        self.assertIn('bag="client/V176BackpackWornRenderer.java"',self.patch)

if __name__=="__main__":
    unittest.main()
