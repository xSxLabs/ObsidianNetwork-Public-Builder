#!/usr/bin/env python3
"""B862 - make worn Micro-MG render gate agree with server module discovery.
Fall back to player Post rendering only when no correctly registered player
render layer submitted its barrel. Do NOT alter suit entry/exit or follow path.
Apply after B847 and after the B857 backpack-only patch.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(path,old,new):
    f=J/path
    s=f.read_text(encoding="utf-8")
    assert s.count(old)==1,("B862_ANCHOR_DRIFT",path,s.count(old),old[:120])
    f.write_text(s.replace(old,new,1),encoding="utf-8")

visual="client/V176MicroMgVisualClient.java"
change(visual,
''' public static boolean armedForAttack(Player player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  return tier(player)>0 && has(chest,"micro_mg") && has(chest,"micro_mg_on");
 }''',
''' /** Same full-set module admission as the SERVER's hasCard check: the card
  * might be installed in a different suit piece, not only the chestplate.
  */
 private static boolean weaponInstalled(Player player){
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)
   if(has(player.getItemBySlot(slot),"micro_mg"))return true;
  return false;
 }
 public static boolean armedForAttack(Player player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  return tier(player)>0 && weaponInstalled(player) && has(chest,"micro_mg_on");
 }''')
# First-person and post render gate MUST match the real authoritative mode.
change(visual,
'''  if(!has(chest,"micro_mg")||!has(chest,"micro_mg_on"))return;''',
'''  if(!armedForAttack(player))return;''')
change(visual,
'''  if(mc.player==null || !has(mc.player.getItemBySlot(EquipmentSlot.CHEST),"micro_mg")
      || !has(mc.player.getItemBySlot(EquipmentSlot.CHEST),"micro_mg_on"))return;''',
'''  if(mc.player==null || !armedForAttack(mc.player))return;''')
# Replace render-pass-disconnected fallback removal from B847.
# The existing layer owns normal rendering. For any player without a layer
# submission (e.g. external renderer replacing player layers), Post is a
# deterministic safety path, with model-space transform, not a gun at y=feet.
change(visual,
''' public static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,''',
''' private static final java.util.Map<Integer,Long> LAYER_SUBMITTED=new java.util.HashMap<>();
 public static void markLayerSubmitted(int entityId){
  var world=Minecraft.getInstance().level;
  if(world!=null)LAYER_SUBMITTED.put(entityId,world.getGameTime());
 }
 @SubscribeEvent public static void wornFallback(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  if(!Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE)))return;
  Integer tierFromState=state.getRenderData(V176AttackRenderState.TIER);
  if(tierFromState==null||tierFromState<1||tierFromState>24)return;
  int id=state.id,variant=tierFromState;
  long tick=mc.level.getGameTime();
  if(LAYER_SUBMITTED.getOrDefault(id,Long.MIN_VALUE)==tick)return;
  float progress=extension(id,true);
  if(progress<=0.001F)return;
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  // The Post hook is at the entity root. Enter the same 24px humanoid
  // model frame as the renderer before applying the actual right-arm pivot.
  pose.translate(0.0F,1.5F,0.0F);
  pose.scale(-1.0F,-1.0F,1.0F);
  var arm=event.getRenderer().getModel().rightArm;
  float ox=arm.xRot,oy=arm.yRot,oz=arm.zRot;
  arm.xRot=-1.535F;arm.yRot=0F;arm.zRot=0F;
  drawArm(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,arm,variant,progress);
  arm.xRot=ox;arm.yRot=oy;arm.zRot=oz;
  pose.popPose();
 }
 public static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,''')
# Existing layered submit must be a real per-frame registration, not relying
# on the prior Pre hook. Its weapon model is drawn from the player's arm.
layer="client/V176MicroMgLayer.java"
change(layer,
'''  if(deployment<=0.001F)return;
  // PoseStack is already in the player model coordinate frame.''',
'''  if(deployment<=0.001F)return;
  // Guard against another layer resetting arm poses after setupAnim.
  var arm=getParentModel().rightArm;
  arm.xRot=-1.535F;arm.yRot=0F;arm.zRot=0F;
  V176MicroMgVisualClient.markLayerSubmitted(state.id);
  // PoseStack is already in the player model coordinate frame.''')
# The Mixin body pose and render-layers share the SAME attack predicate.
player_mixin=J/"mixin/V176AttackPlayerModelMixin.java"
src=player_mixin.read_text(encoding="utf-8")
assert "V176AttackRenderState.ACTIVE" in src, "B862 player mixin must consume the shared B858 render-state gate"
# The real model final animation hook is where arm must be raised. B862
# must not silently substitute model-only geometry for the whole arm.
assert 'this.rightArm.xRot=-1.535F;' in src
print("B862_WORN_MICRO_MG_FULL_SET_GATE_LAYER_AND_PLAYER_POST_FALLBACK_READY")
