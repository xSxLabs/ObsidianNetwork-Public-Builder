#!/usr/bin/env python3
"""B659: client-safe exit concealment and 40-tick entry handoff.
Apply after B658. Never touch saved armor, Recall, skin assets or equipment.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new,n=1):
 p=J/rel;s=p.read_text(encoding="utf8")
 assert s.count(old)==n,("B659_ANCHOR",rel,old,s.count(old))
 p.write_text(s.replace(old,new,n),encoding="utf8")
world="powerarmor/PowerArmorSuitWorld.java"
# 2s actual close clip -> 40 server ticks, not the old 80-tick wait.
# All exit and Recall timings are unchanged.
patch(world,"new Animation(stand,80,entering,",
      "new Animation(stand,entering?40:80,entering,",3)
patch(world,"int t=81-animation.ticks();",
      "int t=(animation.entering()?41:81)-animation.ticks();")
visual="powerarmor/PowerArmorVisualEntity.java"
marker=" public boolean isOpeningFor654(java.util.UUID uuid){"
patch(visual,marker,
''' public boolean isExitOpening659(java.util.UUID uuid){
  return entityData.get(V175_PHASE)==7
      &&entityData.get(EXIT_OWNER_654).equals(uuid.toString());
 }
 public boolean isClosingFor659(java.util.UUID uuid){
  return entityData.get(V175_PHASE)==9
      &&entityData.get(EXIT_OWNER_654).equals(uuid.toString());
 }
'''+marker)
patch(visual,
 'tickCount>83&&!entityTags().contains("xsxlabs_b655_entry_hold_visual")',
 'tickCount>(entityData.get(V175_PHASE)==9?43:83)&&!entityTags().contains("xsxlabs_b655_entry_hold_visual")')
# Phase 9 remains locked until the real equipment is visible on THIS client,
# not while a stale decorative entity lasts an extra two seconds.
patch("client/PowerArmorExitInputLock654.java",
 "v->v.isOpeningFor654(p.getUUID())",
 "v->v.isOpeningFor654(p.getUUID()) && (!v.isClosingFor659(p.getUUID()) || !dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(p))")
render=J/"client/PowerArmorExitRender659.java"
assert not render.exists(),"B659 duplicate render guard"
render.write_text(r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity;
import net.minecraft.client.entity.ClientAvatarEntity;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.context.ContextKey;
import net.minecraft.world.entity.Avatar;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;
import net.neoforged.neoforge.client.renderstate.AvatarRenderStateModifier;
import net.neoforged.neoforge.client.renderstate.RegisterRenderStateModifiersEvent;

/** B659: server invisibility alone still lets the worn armor layers render.
 * Cancel the whole player avatar (skin + armor) while THIS player's synced
 * exit opening is active. Do not cancel the GeckoLib moving armor shell.
 * Phase 9 entry is never hidden by this guard.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorExitRender659 {
 private PowerArmorExitRender659(){}
 private static final ContextKey<Boolean> HIDE=new ContextKey<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","b659_exit_hide_player"));
 @SubscribeEvent public static void register(RegisterRenderStateModifiersEvent event){
  event.registerAvatarEntityModifier(new AvatarRenderStateModifier(){
   @Override public <T extends Avatar & ClientAvatarEntity> void accept(T avatar,AvatarRenderState state){
    boolean hide=false;
    if(avatar instanceof AbstractClientPlayer p && p.level()!=null){
     hide=!p.level().getEntitiesOfClass(PowerArmorVisualEntity.class,
         p.getBoundingBox().inflate(1.6D),
         v->v.isExitOpening659(p.getUUID())).isEmpty();
    }
    state.setRenderData(HIDE,hide);
   }
  });
 }
 @SubscribeEvent public static void render(RenderPlayerEvent.Pre<?> e){
  if(e.getRenderState().getRenderDataOrDefault(HIDE,false))e.setCanceled(true);
 }
}
''',encoding="utf8")
assert 'p.setInvisible(true); // invisible ONLY until hatch has fully opened' in (J/"powerarmor/PowerArmorExitSequence650.java").read_text(encoding="utf8")
assert "PowerArmorSuitWorld.exit(p)" in (J/"powerarmor/PowerArmorExitSequence650.java").read_text(encoding="utf8")
print("B659_EXIT_RENDER_HIDE_AND_ENTRY_40T_GATE PASS")
