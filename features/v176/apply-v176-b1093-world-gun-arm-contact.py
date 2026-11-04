#!/usr/bin/env python3
"""B1093: mount the visible world-only Micro-MG directly on the actual right arm.

B1079 turned only the POST weapon pivot to the player's head yaw/pitch while
the rendered PlayerModel/armor right arm kept its own pose. This put the gun
beside the arm in third person. Both player and ArmorStand feed drawArm(),
which already calls the parent pivot's translateAndRotate; its muzzle rear
was also separated from the upper armor surface by the extra z offset.
Keep the 1P BARREL, FE, projectile, and world Cell pathways unchanged.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgVisualClient.java"
s=p.read_text(encoding="utf-8")
old="""    // Aim the actual right-arm pivot, not a world-space weapon copy.
    renderedArm.xRot=-1.535F+(float)Math.toRadians(player.getXRot());
    renderedArm.yRot=(float)Math.toRadians(net.minecraft.util.Mth.wrapDegrees(
        player.getYHeadRot()-player.yBodyRot));
    renderedArm.zRot=0.0F;"""
new="""    // B1093: match the ACTUALLY RENDERED right arm (including armor/sleeve).
    // Do not impose a second head-yaw/pitch pose on the POST-only gun.
    // The existing model animation/mixins own arm aiming; drawArm inherits
    // its true pivot for every attack and body rotation, without a detached gun."""
assert s.count(old)==1,("B1093_PLAYER_POST_GHOST_ARM_ROTATION",s.count(old))
assert s.count("renderedArm=event.getRenderer().getModel().rightArm")==1
assert s.count("drawArm(pose,event.getSubmitNodeCollector()")==1
s=s.replace(old,new,1)

# The world-only barrel's original B1019 z offset created an additional
# 0.224 model-pixel air gap. B1039 already moved its geometry out of the
# armor mesh: rear=-3.10 px. +0.006 block brings rear to -3.004 px, resting
# on the standard front armor surface (~-3 px) rather than floating.
old_offset="pose.translate(0.0F,-(1.0F-gunOut)*0.26F,-0.014F);"
new_offset="pose.translate(0.0F,-(1.0F-gunOut)*0.26F,0.006F); // B1093_WORLD_GUN_ARM_CONTACT"
assert s.count(old_offset)==1,("B1093_WORLD_GUN_OFFSET_DRIFT",s.count(old_offset))
s=s.replace(old_offset,new_offset,1)
assert s.count(".addBox(-0.46F,6.8F,-4.15F,0.92F,4.7F,1.05F)")==1
assert s.count("parent.translateAndRotate(pose);")==1
assert s.count("nodes.submitModelPart(XSX_WORLD_BARREL,pose")==1
assert s.count("nodes.submitModelPart(BARREL,pose")==1
assert s.count("drawArm(post,nodes,light,")==0  # stand path is in a separate class
s=s.replace("   float ox=renderedArm.xRot,oy=renderedArm.yRot,oz=renderedArm.zRot;","   float ox=renderedArm.xRot,oy=renderedArm.yRot,oz=renderedArm.zRot;",1)
p.write_text(s,encoding="utf-8")

stand=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgStandLayer.java"
t=stand.read_text(encoding="utf-8")
assert "RIGHT_ARM_PIVOT.xRot=(float)Math.toRadians(state.rightArmPose.x());" in t
assert "RIGHT_ARM_PIVOT.yRot=(float)Math.toRadians(state.rightArmPose.y());" in t
assert "RIGHT_ARM_PIVOT.zRot=(float)Math.toRadians(state.rightArmPose.z());" in t
assert "RIGHT_ARM_PIVOT,variant,1.0F" in t
assert "PartPose.offset(-5.0F,2.0F,0.0F)" in t
print("B1093_PLAYER_AND_STAND_WORLD_GUN_TRUE_RIGHT_ARM_PIVOT_CONTACT_PASS")
