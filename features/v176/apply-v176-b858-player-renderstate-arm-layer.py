#!/usr/bin/env python3
"""B858 (STAGED, NO BUILD): one authoritative avatar render-state signal for
both the actual posed player arm and the right upper-arm barrel layer.
Modern NeoForge 26.1 render-state extraction runs before model/layer submission.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new,n=1):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 actual=s.count(old)
 assert actual==n,("B858_SOURCE_DRIFT",rel,actual,old[:110])
 p.write_text(s.replace(old,new,n),encoding="utf-8")

p=J/"client/V176AttackRenderState.java"
assert not p.exists(),("B858_DUPLICATE_RENDER_STATE",p)
p.write_text("""package dev.obsidiannetwork.client;

import net.minecraft.client.entity.ClientAvatarEntity;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.context.ContextKey;
import net.minecraft.world.entity.Avatar;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.renderstate.AvatarRenderStateModifier;
import net.neoforged.neoforge.client.renderstate.RegisterRenderStateModifiersEvent;

/** Extract weapon mode and equipped armor tier ONCE, during the real avatar
 * render-state extraction. No Minecraft.level.getEntity(state.id) guesswork
 * in model setup or in the arm-attached layer.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176AttackRenderState {
 private V176AttackRenderState(){}
 public static final ContextKey<Boolean> ACTIVE=new ContextKey<>(
    Identifier.fromNamespaceAndPath("obsidiannetwork","micro_mg_attack_active"));
 public static final ContextKey<Integer> TIER=new ContextKey<>(
    Identifier.fromNamespaceAndPath("obsidiannetwork","micro_mg_armor_tier"));

 @SubscribeEvent public static void register(RegisterRenderStateModifiersEvent event){
  event.registerAvatarEntityModifier(new AvatarRenderStateModifier(){
   @Override public <T extends Avatar & ClientAvatarEntity> void accept(T avatar,AvatarRenderState state){
    if(avatar instanceof Player player){
     int tier=V176MicroMgVisualClient.tier(player);
     state.setRenderData(TIER,tier);
     state.setRenderData(ACTIVE,tier>0&&V176MicroMgVisualClient.armedForAttack(player));
    }else{
     state.setRenderData(TIER,0);
     state.setRenderData(ACTIVE,false);
    }
   }
  });
 }
}
""",encoding="utf-8")

# The old mixin compiled but looked up a live entity during animation
# submission, not the snapshotted avatar render-state. The render state
# now directly carries the server-synced equipment mode.
patch("mixin/V176AttackPlayerModelMixin.java",
"""  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var entity=mc.level.getEntity(state.id);
  if(!(entity instanceof Player player) || !V176MicroMgVisualClient.armedForAttack(player))return;""",
"""  if(!Boolean.TRUE.equals(state.getRenderData(
      dev.obsidiannetwork.client.V176AttackRenderState.ACTIVE)))return;""")
patch("mixin/V176AttackRightArmMixin.java",
"""  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var entity=mc.level.getEntity(avatar.id);
  if(!(entity instanceof Player player) || !V176MicroMgVisualClient.armedForAttack(player))return;""",
"""  if(!Boolean.TRUE.equals(avatar.getRenderData(
      dev.obsidiannetwork.client.V176AttackRenderState.ACTIVE)))return;""")
# Attach the gun only to the actual right arm; take the *same* snapshot
# the model mixin reads. A missing lookup must never silence a visible arm.
patch("client/V176MicroMgLayer.java",
"""  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var e=mc.level.getEntity(state.id);
  if(!(e instanceof Player player))return;
  int tier=V176MicroMgVisualClient.tier(player);
  if(tier==0)return;
  boolean armed=V176MicroMgVisualClient.armedForAttack(player);
  float deployment=V176MicroMgVisualClient.extension(e.getId(),armed);""",
"""  Integer equippedTier=state.getRenderData(V176AttackRenderState.TIER);
  if(equippedTier==null||equippedTier<1||equippedTier>24)return;
  int tier=equippedTier;
  boolean armed=Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE));
  float deployment=V176MicroMgVisualClient.extension(state.id,armed);""")
patch("client/V176MicroMgLayer.java",
"""   for(var skin : event.getSkins()){
    var renderer=event.getPlayerRenderer(skin);
    if(renderer!=null)renderer.addLayer(new V176MicroMgLayer(renderer));
   }""",
"""   int added=0;
   for(var skin : event.getSkins()){
    var renderer=event.getPlayerRenderer(skin);
    if(renderer!=null){
     renderer.addLayer(new V176MicroMgLayer(renderer));
     added++;
    }
   }
   // Diagnostics for a future ingame run: zero means no weapon layer can draw.
   System.out.println("XSXLABS_B858_PLAYER_BARREL_LAYERS_REGISTERED="+added);
   if(added==0)System.err.println("XSXLABS_B858_ERROR_NO_PLAYER_RENDER_LAYERS");""")
# Assert same state/context is read by both animation and geometry.
for rel in ("mixin/V176AttackPlayerModelMixin.java","mixin/V176AttackRightArmMixin.java","client/V176MicroMgLayer.java"):
 s=(J/rel).read_text(encoding="utf-8")
 assert "V176AttackRenderState.ACTIVE" in s,(rel,"NO_RENDER_SIGNAL")
assert "getParentModel().rightArm,tier,deployment" in (J/"client/V176MicroMgLayer.java").read_text(encoding="utf-8")
print("B858_STAGED_AVATAR_RENDERSTATE_RIGHT_ARM_BARREL_SHARED_SIGNAL_PASS_BUILDLOCK")
