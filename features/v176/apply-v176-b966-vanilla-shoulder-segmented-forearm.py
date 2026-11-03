#!/usr/bin/env python3
"""B966: preserve Build 961 third-person animation, build a first-person
elbow-only pivot (upper arm stays in vanilla position), enlarge worn backpack.
Runs after B957/B964. Any unexpected generated-source drift is fatal.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B966_SOURCE_DRIFT",rel,s.count(old),old[:85])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

gun=J/"client/V176MicroMgVisualClient.java"
s=gun.read_text(encoding="utf-8")
# Do not move the camera's vanilla right arm/hand sideways. The B933 global
# hand transform was the source of moving the entire arm to the left.
old="  event.getPoseStack().translate(-0.21F,0.04F,-0.02F);"
assert s.count(old)==1,("B966_HAND_PARENT_DRIFT",s.count(old))
s=s.replace(old,"  // Vanilla hand/shoulder transform left in its original position.",1)
# The only fallback for held items must not rotate the whole camera/arm.
old="  pose.translate(0.43F,-0.30F,-0.53F);\n  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(32.0F));"
assert s.count(old)==1,("B966_HAND_GUN_DRIFT",s.count(old))
s=s.replace(old,"  pose.translate(0.43F,-0.30F,-0.53F);",1)
# Empty-hand Attack Mode is rendered in the right arm event, in one exact
# forearm frame. Prevent RenderHandEvent from submitting a duplicate barrel.
old="  if(progress<=0.001F)return;\n  // RenderHandEvent executes BEFORE vanilla hand drawing:"
assert s.count(old)==1,("B966_HAND_EMPTY_DRIFT",s.count(old))
s=s.replace(old,"  if(progress<=0.001F||event.getItemStack().isEmpty())return;\n  // RenderHandEvent executes BEFORE vanilla hand drawing:",1)
start=" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){"
end=" @SubscribeEvent public static void worldSuit("
assert s.count(start)==1 and s.count(end)==1,("B966_ARM_HANDLER_DRIFT",s.count(start),s.count(end))
a=s.index(start);b=s.index(end,a)
previous=s[a:b]
assert "pose.translate(-0.16F,0.14F,-0.27F);" in previous, "B966_ARM_OLD_TRANSLATION_MISSING"
assert "rotationDegrees(-78.0F)" in previous and "rotationDegrees(32.0F)" in previous, "B966_OLD_GLOBAL_ARM_ROTATION_MISSING"
replacement=r''' // A vanilla arm is one solid cuboid; a PoseStack rotation of the vanilla
 // event rotates the WHOLE arm, including shoulder. We instead submit two
 // separately skinned sections, preserving the untouched shoulder and upper
 // 6 pixels, and rotate only the lower 6 pixels around the elbow.
 private static ModelPart xsxArmSection(boolean slim,boolean lower,boolean sleeve){
  MeshDefinition mesh=new MeshDefinition();
  float width=slim?3.0F:4.0F;
  float x=slim?-2.5F:-3.0F;
  float y=lower?4.0F:-2.0F;
  int u=40,v=sleeve?32:16;
  // 64x64 vanilla skin UV layout for the right arm/right sleeve.
  if(lower)v+=6;
  mesh.getRoot().addOrReplaceChild("xsx_arm",
      CubeListBuilder.create().texOffs(u,v).addBox(x,y,-2.0F,width,6.0F,4.0F,
          new net.minecraft.client.model.geom.builders.CubeDeformation(sleeve?0.23F:0.0F)),
      PartPose.offset(-5.0F,2.0F,0.0F));
  return LayerDefinition.create(mesh,64,64).bakeRoot().getChild("xsx_arm");
 }
 private static final ModelPart XSX_UPPER=xsxArmSection(false,false,false);
 private static final ModelPart XSX_LOWER=xsxArmSection(false,true,false);
 private static final ModelPart XSX_UPPER_SLIM=xsxArmSection(true,false,false);
 private static final ModelPart XSX_LOWER_SLIM=xsxArmSection(true,true,false);
 private static final ModelPart XSX_SLEEVE_UPPER=xsxArmSection(false,false,true);
 private static final ModelPart XSX_SLEEVE_LOWER=xsxArmSection(false,true,true);
 private static final ModelPart XSX_SLEEVE_UPPER_SLIM=xsxArmSection(true,false,true);
 private static final ModelPart XSX_SLEEVE_LOWER_SLIM=xsxArmSection(true,true,true);

 @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  var player=event.getPlayer();
  int equippedTier=tier(player);
  if(equippedTier<1||equippedTier>24)return;
  boolean active=armedForAttack(player);
  float progress=extension(player.getId(),active);
  if(!active&&progress<=0.001F)return;
  // Only replace the right arm while Attack Mode extends/retracts. The
  // third-person PlayerModel, armor layers, recall, and idle pose are untouched.
  event.setCanceled(true);
  PoseStack pose=event.getPoseStack();
  var nodes=event.getSubmitNodeCollector();
  int light=event.getPackedLight();
  boolean slim="SLIM".equals(player.getSkin().model().name());
  boolean sleeve=player.isModelPartShown(
      net.minecraft.world.entity.player.PlayerModelPart.RIGHT_SLEEVE);
  var skin=RenderTypes.entitySolid(player.getSkin().body().texturePath());
  ModelPart upper=slim?XSX_UPPER_SLIM:XSX_UPPER;
  ModelPart lower=slim?XSX_LOWER_SLIM:XSX_LOWER;
  ModelPart upperSleeve=slim?XSX_SLEEVE_UPPER_SLIM:XSX_SLEEVE_UPPER;
  ModelPart lowerSleeve=slim?XSX_SLEEVE_LOWER_SLIM:XSX_SLEEVE_LOWER;
  // Render the shoulder and upper arm at unmodified vanilla location.
  nodes.submitModelPart(upper,pose,skin,light,OverlayTexture.NO_OVERLAY,
      null,false,false,0xFFFFFFFF,null,0);
  if(sleeve)
   nodes.submitModelPart(upperSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
  // Pivot at right elbow, not at the camera or shoulder. Only forearm and
  // upper-arm-mounted barrel inherit these two rotations.
  float bend=Math.min(1.0F,progress/(4.0F/12.0F));
  pose.pushPose();
  pose.translate(-6.0F/16.0F,6.0F/16.0F,0.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-78.0F*bend));
  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(32.0F*bend));
  pose.translate(6.0F/16.0F,-6.0F/16.0F,0.0F);
  nodes.submitModelPart(lower,pose,skin,light,OverlayTexture.NO_OVERLAY,
      null,false,false,0xFFFFFFFF,null,0);
  if(sleeve)
   nodes.submitModelPart(lowerSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
  float gunOut=phase(progress,7.0F/12.0F,1.0F);
  if(gunOut>0.001F){
   pose.pushPose();
   pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);
   pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
   nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(equippedTier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  pose.popPose();
 }
'''
s=s[:a]+replacement+s[b:]
gun.write_text(s,encoding="utf-8")
# A visible backpack must be proportional to the armored torso; the old
# .66 scale is tiny. Keep the already corrected shoulder-height pivot.
edit("client/V176BackpackWornRenderer.java",
     "  pose.scale(.66F,.66F,.66F);",
     "  pose.scale(1.00F,1.00F,1.00F);")
# Build 961 3P pose is the reference. This patch is forbidden from touching
# its source, Mixins, shared player-state, or turret/world model callback.
arm_pose=J/"client/V176FinalArmPose.java"
assert "baseline*(1.0F-raised)-1.5707964F*raised" in arm_pose.read_text(), "B966_B961_3P_POSE_REGRESSED"
assert "stand.entityTags().contains(\"xsxlabs_v176_turret\")" in s, "B966_B961_TURRET_RENDER_GATE_REGRESSED"
assert "event.setCanceled(true);" in s
assert "pose.scale(1.00F,1.00F,1.00F);" in (J/"client/V176BackpackWornRenderer.java").read_text()
assert s.count("xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event)")==1
assert "pose.translate(-0.16F,0.14F,-0.27F);" not in s
print("B966_BUILD961_THIRD_PERSON_PRESERVED_VANILLA_SHOULDER_SEGMENTED_FOREARM_ATTACHED_GUN_BIG_BACKPACK_PASS")
