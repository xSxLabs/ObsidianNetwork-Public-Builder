#!/usr/bin/env python3
"""B878 source-only regression fix: correct local barrel axis, enforce a real
player AND armor pose, and render first-person MG from RenderHandEvent.
Apply after B862 and B863. No build marker.
"""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==1,("B878_DRIFT",rel,s.count(old),old[:100])
    p.write_text(s.replace(old,new,1),encoding="utf-8")

context=J/"client/V176AttackPoseContext.java"
assert not context.exists(),("B878_DUPLICATE_POSE_CONTEXT",str(context))
context.write_text("""package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;

/**
 * The armor is another HumanoidModel rendered during the player pass.
 * Its state is not guaranteed to be an AvatarRenderState. Keep the
 * active player pose available through all armor submissions, not only
 * the PlayerModel and later Micro-MG layer.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176AttackPoseContext {
 private V176AttackPoseContext(){}
 private static final ThreadLocal<Boolean> PLAYER_RENDER_ARMED=
       ThreadLocal.withInitial(()->false);
 private static Boolean lastLocalAim=null;

 @SubscribeEvent public static void before(RenderPlayerEvent.Pre<?> event){
  AvatarRenderState state=event.getRenderState();
  boolean armed=Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE));
  Minecraft mc=Minecraft.getInstance();
  if(mc.level!=null){
   var entity=mc.level.getEntity(state.id);
   if(entity instanceof Player player)
    armed=V176MicroMgVisualClient.armedForAttack(player);
  }
  PLAYER_RENDER_ARMED.set(armed);
  if(armed){
   // An actual vanilla pose fallback is needed for renderers that clone
   // the parent model without calling our setupAnim hook on the armor.
   // Our model mixins then refine this into an almost horizontal aim.
   state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS;
  }
  if(mc.player!=null&&state.id==mc.player.getId()
      &&(lastLocalAim==null||lastLocalAim.booleanValue()!=armed)){
   lastLocalAim=armed;
   System.out.println("XSXLABS_B878_PLAYER_RENDER_PRE_AIM="+armed);
  }
 }
 @SubscribeEvent public static void after(RenderPlayerEvent.Post<?> event){
  PLAYER_RENDER_ARMED.remove();
 }

 public static boolean aim(HumanoidRenderState state){
  if(state instanceof AvatarRenderState avatar){
   if(Boolean.TRUE.equals(avatar.getRenderData(V176AttackRenderState.ACTIVE)))
    return true;
   Minecraft mc=Minecraft.getInstance();
   if(mc.level!=null){
    var entity=mc.level.getEntity(avatar.id);
    if(entity instanceof Player player &&
       V176MicroMgVisualClient.armedForAttack(player))
     return true;
   }
  }
  return PLAYER_RENDER_ARMED.get();
 }
}
""",encoding="utf-8")

# Two independent setupAnim injections cover both the avatar itself AND the
# separate power armor models; the pre-event rightArmPose is a third safeguard.
change("mixin/V176AttackPlayerModelMixin.java",
'''  if(!Boolean.TRUE.equals(state.getRenderData(
      dev.obsidiannetwork.client.V176AttackRenderState.ACTIVE)))return;''',
'''  if(!dev.obsidiannetwork.client.V176AttackPoseContext.aim(state))return;''')
change("mixin/V176AttackRightArmMixin.java",
'''  if(!Boolean.TRUE.equals(avatar.getRenderData(
      dev.obsidiannetwork.client.V176AttackRenderState.ACTIVE)))return;''',
'''  if(!dev.obsidiannetwork.client.V176AttackPoseContext.aim(state))return;''')
# The generic humanoid injection also runs on armor rigs whose render state
# is NOT AvatarRenderState. Never reject those before consulting the context.
change("mixin/V176AttackRightArmMixin.java",
'''  if(!(state instanceof AvatarRenderState avatar))return;''',
'''  // The active player render scope also applies to HumanoidModel armor layers.''')

visual="client/V176MicroMgVisualClient.java"
# The worn gun was drawn along local -Z, although the right arm extends along
# POSITIVE local Y. When raised, positive Y points forward; -Z points UP.
# This is the physical reason the barrel appears behind/above the shoulder.
change(visual,
'''      .texOffs(0,0).addBox(-1.0F,5.5F,-9.0F,2.0F,2.0F,7.0F)
      .texOffs(0,10).addBox(-1.25F,5.25F,-9.5F,2.5F,2.5F,1.5F)
      .texOffs(0,16).addBox(-1.5F,5.0F,-4.0F,3.0F,3.0F,3.0F),''',
'''      // Slim barrel runs ALONG the local arm from shoulder to muzzle.
      // No big square muzzle cap or black block on the front.
      .texOffs(0,0).addBox(-0.9F,5.0F,-3.5F,1.8F,13.0F,1.8F)
      // Small upper-arm mounting rail, ending before the elbow.
      .texOffs(0,15).addBox(-1.6F,2.5F,-3.25F,3.2F,6.0F,0.8F),''')
# To follow the extending upper arm the deployment offset MUST be in its local
# Y direction (along the barrel), not in the model's unrotated Z axis.
change(visual,
'''  pose.translate(0.0F,0.0F,(1.0F-extension)*0.40F);''',
'''  pose.translate(0.0F,-(1.0F-extension)*0.30F,0.0F);''')
change(visual,
'''import net.neoforged.neoforge.client.event.RenderArmEvent;''',
'''import net.neoforged.neoforge.client.event.RenderHandEvent;
import net.minecraft.world.InteractionHand;''')
p=J/visual
s=p.read_text(encoding="utf-8")
start=" @SubscribeEvent public static void firstPerson(RenderArmEvent event){"
end=" @SubscribeEvent public static void worldSuit("
assert s.count(start)==1 and s.count(end)==1 and s.index(start)<s.index(end),("B878_FIRST_PERSON_METHOD_DRIFT",s.count(start),s.count(end))
replacement=""" @SubscribeEvent public static void firstPerson(RenderHandEvent event){
  // RenderArmEvent only fires when vanilla renders the naked arm, not when
  // an item is held. RenderHandEvent fires for the real MAIN_HAND pipeline.
  if(event.getHand()!=InteractionHand.MAIN_HAND)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||!armedForAttack(mc.player))return;
  int equippedTier=tier(mc.player);
  if(equippedTier<1||equippedTier>24)return;
  float progress=extension(mc.player.getId(),true);
  if(progress<=0.001F)return;
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  // Camera-relative right upper arm. Positive model Y must point forwards.
  pose.translate(0.39F,-0.34F,-0.45F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-90.0F));
  pose.translate(0.0F,-(1.0F-progress)*0.30F,0.0F);
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(equippedTier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
"""
s=s[:s.index(start)]+replacement+s[s.index(end):]
p.write_text(s,encoding="utf-8")

mix=(J/"mixin/V176AttackRightArmMixin.java").read_text(encoding="utf-8")
avatar=(J/"mixin/V176AttackPlayerModelMixin.java").read_text(encoding="utf-8")
visualsrc=p.read_text(encoding="utf-8")
assert "V176AttackPoseContext.aim(state)" in mix and "V176AttackPoseContext.aim(state)" in avatar
assert "RenderHandEvent" in visualsrc and "RenderArmEvent event" not in visualsrc
assert "addBox(-0.9F,5.0F,-3.5F,1.8F,13.0F,1.8F)" in visualsrc
assert "markLayerSubmitted" in (J/"client/V176MicroMgLayer.java").read_text(encoding="utf-8")
print("B878_REAL_WORN_ARM_ARMOR_MODELS_CAMERA_HAND_ALIGNED_BARREL_NO_BLACK_MUZZLE_READY")
