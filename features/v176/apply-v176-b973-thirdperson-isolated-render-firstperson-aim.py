#!/usr/bin/env python3
"""B973: repair B972 recurrent attack crash and first-person mis-aim.

NeoForge 26.1 collector snapshots PoseStack per submitted feature. Never pass
a caller's live world/player matrix into our 3P attachment renderer. The
B971 try/finally only matched OUR outer push and still depended on a shared
PoseStack; B973 uses independent stacks.

First person: Y rotation of a Y-axis arm cannot move its endpoint sideways.
Submit shoulder, elbow-driven forearm, and mounted gun from ONE main-hand
callback. For the empty-hand attack animation, cancel only vanilla's matching
hand submission; vanilla hand and shoulder are unaffected while Attack is off.
The elbow/gun quaternion is derived from the actual elbow-to-crosshair ray,
not an unrelated independent gun yaw.
"""
import os
from pathlib import Path

ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel,old,new):
    file=ROOT/rel
    s=file.read_text(encoding="utf-8")
    n=s.count(old)
    assert n==1,("B973_SOURCE_DRIFT",rel,n,old[:140])
    file.write_text(s.replace(old,new,1),encoding="utf-8")

# A third-person gun is a renderer feature, never a modification to the
# LevelRenderer's shared PoseStack. Snapshot the world/player matrix into an
# isolated stack before applying any model part pivots.
layer="client/V176MicroMgLayer.java"
change(layer,
"""  pose.pushPose();
  try {
   V176MicroMgVisualClient.drawArm(pose,nodes,light,
       getParentModel().rightArm,tier,deployment);
  } finally {
   pose.popPose();
  }""",
"""  // Isolated PoseStack: a gun renderer cannot leak any push/pop to the
  // game's caller, even if another model implementation mutates its input.
  PoseStack xsxWeaponPose=new PoseStack();
  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  V176MicroMgVisualClient.drawArm(xsxWeaponPose,nodes,light,
       getParentModel().rightArm,tier,deployment);
  assert xsxWeaponPose.clear() : "B973 third-person weapon stack leaked";""")

# Apply the same isolation to the visible worn bag. Increase only worn size
# (never the placeable model or one of the 24 palettes).
bag="client/V176BackpackWornRenderer.java"
change(bag,
"""  var pose=event.getPoseStack();
  pose.pushPose();""",
"""  var xsxParent=event.getPoseStack();
  var pose=new com.mojang.blaze3d.vertex.PoseStack();
  pose.mulPose(new org.joml.Matrix4f(xsxParent.last().pose()));""")
change(bag,"  pose.scale(1.00F,1.00F,1.00F);",
           "  pose.scale(1.35F,1.35F,1.35F);")
change(bag,
"""  try {
   model.submit(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,0);
  } finally {
   pose.popPose();
  }""",
"""  model.submit(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,0);
  assert pose.clear() : "B973 backpack stack leaked";""")

# B878 forcibly marked the player as holding a SPYGLASS during third-person
# render. This is a third-party animation/mod compatibility hazard and is NOT
# the real B915/B961 arm-pose implementation. Keep the actual model mixins
# and weapon layer, but stop the misleading vanilla hand-pose override.
context="client/V176AttackPoseContext.java"
change(context,
"""  if(armed){
   // An actual vanilla pose fallback is needed for renderers that clone
   // the parent model without calling our setupAnim hook on the armor.
   // Our model mixins then refine this into an almost horizontal aim.
   state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS;
  }""",
"""  // The actual right-arm pose is produced by the player/armor model
  // hooks. Do not fake a spyglass held item in RenderPlayerEvent.Pre:
  // external animation mods must see the real vanilla hand pose.""")
assert "V176AttackPoseContext.aim(state)" in (ROOT/"mixin/V176AttackRightArmMixin.java").read_text()
assert "baseline*(1.0F-raised)-1.5707964F*raised" in (ROOT/"client/V176FinalArmPose.java").read_text()

gun="client/V176MicroMgVisualClient.java"
p=ROOT/gun
s=p.read_text(encoding="utf-8")
hand=" @SubscribeEvent public static void firstPerson(RenderHandEvent event){"
arm=" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){"
world=" @SubscribeEvent public static void worldSuit("
assert s.count(hand)==s.count(arm)==s.count(world)==1,"B973_HAND_ARM_RENDER_HANDLERS"
start=s.index(hand);stop=s.index(arm,start);end=s.index(world,stop)
oldhand=s[start:stop]
oldarm=s[stop:end]
assert "if(progress<=0.001F)return;" in oldhand
assert "submitModelPart(BARREL" in oldhand
assert "pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(42.0F*bend));" in oldarm
assert "XSX_UPPER_SLIM" in s and "XSX_LOWER_SLIM" in s
assert "event.setCanceled(true);" in oldarm

# Full replacement of only the FIRST-PERSON main-hand path: the old
# RenderHandEvent was drawing an orphan barrel while RenderArmEvent only
# altered the arm (and sometimes did not fire at all for an empty hand).
# The skin and gun now share one true elbow transform in one event.
newhand=r''' @SubscribeEvent public static void firstPerson(RenderHandEvent event){
  if(event.getHand()!=InteractionHand.MAIN_HAND)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.player.getMainArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  int equippedTier=tier(mc.player);
  if(equippedTier<1||equippedTier>24)return;
  boolean active=armedForAttack(mc.player);
  float progress=extension(mc.player.getId(),active);
  if(!active&&progress<=0.001F)return;
  // Never put an orphan gun beside an unmodified vanilla forearm. The
  // main-hand event exists with an EMPTY hand; RenderArmEvent may not.
  // Cancel only the main hand while this animation is deployed.
  event.setCanceled(true);
  PoseStack pose=new PoseStack();
  pose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  var nodes=event.getSubmitNodeCollector();
  int light=event.getPackedLight();
  boolean slim="SLIM".equals(mc.player.getSkin().model().name());
  boolean sleeve=mc.player.isModelPartShown(
      net.minecraft.world.entity.player.PlayerModelPart.RIGHT_SLEEVE);
  var skin=RenderTypes.entitySolid(mc.player.getSkin().body().texturePath());
  ModelPart upper=slim?XSX_UPPER_SLIM:XSX_UPPER;
  ModelPart lower=slim?XSX_LOWER_SLIM:XSX_LOWER;
  ModelPart upperSleeve=slim?XSX_SLEEVE_UPPER_SLIM:XSX_SLEEVE_UPPER;
  ModelPart lowerSleeve=slim?XSX_SLEEVE_LOWER_SLIM:XSX_SLEEVE_LOWER;

  // Camera-relative vanilla RIGHT shoulder. Mirroring both X and Y keeps
  // winding intact and the 64x64 vanilla skin on the correct right arm.
  // Upper arm is never rotated to aim; only the child at the elbow moves.
  final float shoulderX=.30F,shoulderY=-.15F,shoulderZ=-.70F;
  pose.translate(shoulderX,shoulderY,shoulderZ);
  pose.scale(-1.0F,-1.0F,1.0F);
  nodes.submitModelPart(upper,pose,skin,light,OverlayTexture.NO_OVERLAY,
      null,false,false,0xFFFFFFFF,null,0);
  if(sleeve)
   nodes.submitModelPart(upperSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);

  // Model axis: shoulder (-5,2,0), elbow (-5,6,0), +Y along forearm.
  // Rotate +Y toward a target ON THE CROSSHAIR RAY. In model coordinates
  // X/Y are mirrored by the camera model transform, so invert target X/Y
  // before constructing the quaternion.
  float bend=Math.min(1.0F,progress/(4.0F/12.0F));
  org.joml.Vector3f elbowToCrosshair=new org.joml.Vector3f(
      shoulderX+5.0F/16.0F,
      -shoulderY+6.0F/16.0F,
      -2.60F-shoulderZ).normalize();
  org.joml.Quaternionf aim=new org.joml.Quaternionf().rotationTo(
      new org.joml.Vector3f(0.0F,1.0F,0.0F),elbowToCrosshair);
  org.joml.Quaternionf interpolated=new org.joml.Quaternionf().slerp(aim,bend);
  pose.pushPose();
  try {
   pose.translate(-5.0F/16.0F,6.0F/16.0F,0.0F);
   pose.mulPose(interpolated);
   pose.translate(5.0F/16.0F,-6.0F/16.0F,0.0F);
   nodes.submitModelPart(lower,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
   if(sleeve)
    nodes.submitModelPart(lowerSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
        null,false,false,0xFFFFFFFF,null,0);
   // The gun shares the EXACT elbow aim quaternion. It is mounted to
   // the same forearm/upper-arm surface and cannot rotate independently.
   float gunOut=phase(progress,7.0F/12.0F,1.0F);
   if(gunOut>0.001F){
    pose.pushPose();
    try {
     pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);
     pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
     nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(equippedTier)),
        light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
    } finally {
     pose.popPose();
    }
   }
  } finally {
   pose.popPose();
  }
  assert pose.clear() : "B973 first-person isolated weapon stack leaked";
 }
'''
# In Attack Mode the main-hand callback owns ALL skin and gun geometry.
# No separate RenderArmEvent submission is allowed to draw them a second time.
newarm=r''' @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  // Legacy hook intentionally disabled: B973 submits upper arm, hinged
  // forearm and gun in one RenderHandEvent pass for empty or held hands.
  // Do not cancel or touch the vanilla pose here (also used in UI previews).
 }
'''
s=s[:start]+newhand+newarm+s[end:]
p.write_text(s,encoding="utf-8")

src=p.read_text(encoding="utf-8")
handbody=src[src.index(hand):src.index(arm)]
armbody=src[src.index(arm):src.index(world)]
assert handbody.count("submitModelPart(BARREL")==1, "B973_ONLY_ONE_FP_BARREL"
assert handbody.count("submitModelPart(lower,")==1, "B973_ONE_LOWER_ARM"
assert "event.setCanceled(true)" in handbody
assert "elbowToCrosshair" in handbody and "rotationTo(" in handbody
assert "pose.mulPose(interpolated)" in handbody
assert "submitModelPart(BARREL" not in armbody
assert "event.setCanceled" not in armbody
assert "pose.scale(1.35F,1.35F,1.35F)" in (ROOT/bag).read_text()
assert "xsxWeaponPose=new PoseStack()" in (ROOT/layer).read_text()
assert "state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS" not in (ROOT/context).read_text()
print("B973_ISOLATED_3P_POSE_NO_SPYGLASS_SINGLE_1P_ELBOW_GUN_AIM_BACKPACK_135_PASS")
