#!/usr/bin/env python3
"""B675: server-authorized FE Micro-MG bullet, client held-click replacement.
Minecraft 26.1, no arrows/fireballs/hitscan. Runs after B674.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B675_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,body):
 p=J/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_B675_DUPLICATE_CLASS",rel)
 p.write_text(body,encoding="utf-8")

change("ObsidianNetwork.java",
 '''   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorStand>> POWER_ARMOR_WORLD_MK1 =''',
 '''   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.V176MicroMgProjectile>> MICRO_MG_PROJECTILE =
      ARMOR_VISUAL_ENTITIES.registerEntityType("micro_mg_projectile",
         dev.obsidiannetwork.powerarmor.V176MicroMgProjectile::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(0.16F,0.16F).clientTrackingRange(8).updateInterval(1));
   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorStand>> POWER_ARMOR_WORLD_MK1 =''')
change("powerarmor/PowerArmorCommands.java",
 '   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException()))));',
 '   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException())))\n'
 '   .then(Commands.literal("fire").executes(c->V176MicroMgFire.fire(c.getSource().getPlayerOrException()))));')
add("powerarmor/V176MicroMgProjectile.java",'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.BlockHitResult;

/** Small synchronized physical bullet, 2 HP / hit, finite lifetime. */
public final class V176MicroMgProjectile extends ThrowableItemProjectile {
 public V176MicroMgProjectile(EntityType<? extends V176MicroMgProjectile> type,Level world){
  super(type,world);
 }
 @Override protected Item getDefaultItem(){return Items.IRON_NUGGET;}
 @Override protected double getDefaultGravity(){return 0.0D;}
 @Override protected void onHitEntity(EntityHitResult hit){
  super.onHitEntity(hit);
  if(level() instanceof ServerLevel server){
   Entity target=hit.getEntity(), owner=getOwner();
   if(target instanceof LivingEntity living && owner!=target
      &&!(target instanceof Player && !(owner instanceof Player))){
    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);
   }
   discard();
  }
 }
 @Override protected void onHitBlock(BlockHitResult hit){
  super.onHitBlock(hit);
  if(!level().isClientSide())discard();
 }
 @Override public void tick(){
  super.tick();
  if(!level().isClientSide()&&tickCount>12)discard(); // never unbounded
 }
}
''')
add("powerarmor/V176MicroMgFire.java",'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** A HUD toggle never authorizes damage: re-check module, FE and 5-tick cooldown. */
public final class V176MicroMgFire {
 private V176MicroMgFire(){}
 private static final Map<UUID,Long> LAST=new HashMap<>();
 public static int fire(ServerPlayer p){
  if(!V176AttackModeServer.on(p))return 0;
  ServerLevel world=(ServerLevel)p.level();
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  long now=world.getGameTime();
  long previous=LAST.getOrDefault(p.getUUID(),-1L);
  if(!V176MicroMgRules.canManualFire(PowerArmorRuntime.full(p),
       PowerArmorRuntime.hasCard(p,"micro_mg"),true,
       EnergyTool.energy(chest),now,previous))return 0;
  Vec3 dir=p.getLookAngle().normalize();
  Vec3 right=new Vec3(-dir.z,0,dir.x);
  if(right.lengthSqr()<1.0E-6)right=new Vec3(1,0,0);
  right=right.normalize();
  double side=((now/5L)&1L)==0L?0.27D:-0.27D;
  Vec3 origin=p.getEyePosition().add(dir.scale(0.55D))
             .add(right.scale(side)).add(0,-0.30D,0);
  var shot=new V176MicroMgProjectile(
     dev.obsidiannetwork.ObsidianNetwork.MICRO_MG_PROJECTILE.get(),world);
  shot.setOwner(p);
  shot.setPos(origin.x,origin.y,origin.z);
  shot.shoot(dir.x,dir.y,dir.z,3.0F,0.8F);
  String upgrades=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  V176LootingEvents.mark(shot,V176LootingSupport.level(upgrades));
  if(!world.addFreshEntity(shot))return 0;
  if(!EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)){
   shot.discard();return 0;
  }
  LAST.put(p.getUUID(),now);
  world.sendParticles(ParticleTypes.END_ROD,origin.x,origin.y,origin.z,
     2,0.035,0.035,0.035,0.015);
  world.playSound(null,p.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
     SoundSource.PLAYERS,0.45F,1.75F);
  return 1;
 }
}
''')
add("client/V176MicroMgFireClient.java",'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.InputEvent;
import org.lwjgl.glfw.GLFW;

/** Consume normal attack, poll held mouse, server decides whether bullet exists. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176MicroMgFireClient {
 private V176MicroMgFireClient(){}
 private static long next=-1L;
 private static boolean ready(){
  Minecraft mc=Minecraft.getInstance();
  return mc.player!=null&&mc.level!=null&&mc.screen==null
      &&V176AttackModeClient.active();
 }
 @SubscribeEvent public static void preventClick(InputEvent.MouseButton.Pre e){
  if(e.getButton()==GLFW.GLFW_MOUSE_BUTTON_LEFT&&ready())e.setCanceled(true);
 }
 @SubscribeEvent public static void preventAttack(InputEvent.InteractionKeyMappingTriggered e){
  if(e.isAttack()&&ready()){e.setSwingHand(false);e.setCanceled(true);}
 }
 @SubscribeEvent public static void held(ClientTickEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  if(!ready()){next=-1L;return;}
  mc.options.keyAttack.setDown(false); // no block mining / vanilla melee while armed
  if(!mc.mouseHandler.isMouseGrabbed())return; // ignore action wheel's released cursor
  if(GLFW.glfwGetMouseButton(mc.getWindow().handle(),GLFW.GLFW_MOUSE_BUTTON_LEFT)!=GLFW.GLFW_PRESS)
   return;
  long tick=mc.level.getGameTime();
  if(next>=0L && tick<next)return;
  next=tick+V176MicroMgFireClient.cooldown();
  if(mc.player.connection!=null)mc.player.connection.sendCommand("powerarmor fire");
 }
 private static int cooldown(){return 5;}
}
''')
add("client/V176MicroMgBulletRenderer.java",'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.ObsidianNetwork;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Real tracked entity with tiny metallic sprite, never arrow/fireball. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176MicroMgBulletRenderer {
 private V176MicroMgBulletRenderer(){}
 @SubscribeEvent public static void register(EntityRenderersEvent.RegisterRenderers event){
  event.registerEntityRenderer(ObsidianNetwork.MICRO_MG_PROJECTILE.get(),
    ctx->new net.minecraft.client.renderer.entity.ThrownItemRenderer<>(ctx,0.35F,true));
 }
}
''')
print("V176_B675_PHYSICAL_FE_BULLET_MANUAL_LEFTCLICK_PASS")
