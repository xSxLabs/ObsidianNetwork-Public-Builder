#!/usr/bin/env python3
"""B676: two exclusive persisted companion modes: Follow and Follow+Turret.
Owner-only, module-gated turret, server collision and FE guards. After B675.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B676_SOURCE_DRIFT",rel,s.count(old),old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,src):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_B676_DUPLICATE",rel)
 p.write_text(src,encoding="utf-8")

edit("powerarmor/PowerArmorCommands.java",
 '   .then(Commands.literal("fire").executes(c->V176MicroMgFire.fire(c.getSource().getPlayerOrException()))));',
 '''   .then(Commands.literal("fire").executes(c->V176MicroMgFire.fire(c.getSource().getPlayerOrException())))
   .then(Commands.literal("follow").executes(c->V176CompanionMode.toggle(c.getSource().getPlayerOrException(),false)))
   .then(Commands.literal("turret").executes(c->V176CompanionMode.toggle(c.getSource().getPlayerOrException(),true))));''')
edit("client/NetworkActionWheelClient.java",
 ' private static int[] wheelActions(boolean vision,boolean attack){',
 ''' private static int[] wheelActions(boolean vision,boolean attack){
  int[] companion=V176CompanionClient.actions(vision);
  if(companion!=null)return companion;''')
edit("client/NetworkActionWheelClient.java",
 'case 5->V176AttackModeClient.toggleFromWheel();',
 '''case 5->V176AttackModeClient.toggleFromWheel();
     case 6->V176CompanionClient.toggleFollow();
     case 7->V176CompanionClient.toggleTurret();''')
edit("client/NetworkActionWheelClient.java",
 'String name=i==4?"VISION":i==5?("ATTACK "+(V176AttackModeClient.active()?"ON":"OFF")):ACTIONS[i];',
 'String name=i==4?"VISION":i==5?("ATTACK "+(V176AttackModeClient.active()?"ON":"OFF")):i==6?"FOLLOW":i==7?"TURRET":ACTIONS[i];')
add("client/V176CompanionClient.java",'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.phys.AABB;
import java.util.Arrays;

/** Wheel shows only modes available on a nearby complete standing suit. */
public final class V176CompanionClient {
 private V176CompanionClient(){}
 private static ArmorStand nearby(){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.level==null)return null;
  if(PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0)!=0)return null;
  var stands=mc.level.getEntitiesOfClass(ArmorStand.class,
    new AABB(mc.player.blockPosition()).inflate(16.0D),s->{
      int tier=PowerArmorRuntime.tier(s.getItemBySlot(EquipmentSlot.HEAD),0);
      if(tier==0)return false;
      for(int i=1;i<4;i++)if(PowerArmorRuntime.tier(
         s.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)return false;
      String owner="xsxlabs_power_armor_owner_"+mc.player.getUUID();
      for(String tag:s.entityTags())
       if(tag.startsWith("xsxlabs_power_armor_owner_")&&!tag.equals(owner))return false;
      return true;
    });
  return stands.size()==1?stands.get(0):null;
 }
 public static int[] actions(boolean vision){
  ArmorStand suit=nearby();
  if(suit==null)return null;
  String upgrades=suit.getItemBySlot(EquipmentSlot.CHEST)
     .get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  boolean mg=upgrades!=null&&Arrays.asList(upgrades.split(",")).contains("micro_mg");
  if(vision)return mg?new int[]{0,1,4,6,7,2,3}:new int[]{0,1,4,6,2,3};
  return mg?new int[]{0,1,6,7,2,3}:new int[]{0,1,6,2,3};
 }
 public static void toggleFollow(){
  var mc=Minecraft.getInstance();
  if(nearby()!=null&&mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand("powerarmor follow");
 }
 public static void toggleTurret(){
  var mc=Minecraft.getInstance();
  ArmorStand stand=nearby();
  if(stand==null||mc.player==null||mc.player.connection==null)return;
  String raw=stand.getItemBySlot(EquipmentSlot.CHEST).get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(raw!=null&&Arrays.asList(raw.split(",")).contains("micro_mg"))
   mc.player.connection.sendCommand("powerarmor turret");
 }
}
''')
add("powerarmor/V176CompanionMode.java",'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.level.ClipContext;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Map;
import java.util.WeakHashMap;

/** 2 world suit modes, NEVER a static turret; no extra stationary wheel choice. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176CompanionMode {
 private V176CompanionMode(){}
 private static final String FOLLOW="xsxlabs_v176_follow";
 private static final String TURRET="xsxlabs_v176_turret";
 private static final String STAND="xsxlabs_power_armor_suit_v17";
 private static final String OWNER="xsxlabs_power_armor_owner_";
 private static final Map<ArmorStand,Long> LAST_SHOT=new WeakHashMap<>();
 private static boolean hasModule(ArmorStand suit){
  String raw=suit.getItemBySlot(EquipmentSlot.CHEST)
    .get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return raw!=null&&Arrays.asList(raw.split(",")).contains("micro_mg");
 }
 private static ArmorStand find(ServerPlayer player,double radius){
  AABB box=player.getBoundingBox().inflate(radius);
  var found=player.level().getEntitiesOfClass(ArmorStand.class,box,
    e->e.isAlive()&&e.entityTags().contains(STAND)
      &&e.entityTags().contains(OWNER+player.getUUID())
      &&PowerArmorSuitWorld.full(e));
  return found.stream().min(Comparator.comparingDouble(player::distanceToSqr)).orElse(null);
 }
 private static void display(ServerPlayer p,String message){
  p.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(message)));
 }
 public static int toggle(ServerPlayer player,boolean turret){
  ArmorStand suit=find(player,20.0D);
  if(suit==null||suit.isInvisible())return 0;
  if(turret&&!hasModule(suit))return 0;
  String requested=turret?TURRET:FOLLOW;
  boolean was=suit.entityTags().contains(requested);
  suit.removeTag(FOLLOW);suit.removeTag(TURRET);
  if(!was)suit.addTag(requested);
  display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));
  return 1;
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)||player.tickCount%5!=0)return;
  ArmorStand suit=find(player,72.0D);
  if(suit==null||suit.isInvisible())return;
  boolean turret=suit.entityTags().contains(TURRET);
  if(!turret&&!suit.entityTags().contains(FOLLOW))return;
  ServerLevel world=player.level();
  double dist=suit.distanceToSqr(player);
  if(dist>14D*14D){
   Vec3 look=player.getLookAngle();
   Vec3 spot=player.position().subtract(new Vec3(look.x,0,look.z).normalize().scale(2.0D));
   BlockPos base=BlockPos.containing(spot);
   Vec3 delta=spot.subtract(suit.position());
   if(world.isLoaded(base)&&world.isEmptyBlock(base)&&world.isEmptyBlock(base.above())
     &&world.noCollision(suit,suit.getBoundingBox().move(delta)))
    suit.setPos(spot.x,spot.y,spot.z);
  }else if(dist>3.5D*3.5D){
   Vec3 vector=player.position().subtract(suit.position());
   Vec3 step=new Vec3(vector.x,0,vector.z);
   if(step.lengthSqr()>0.02D){
    step=step.normalize().scale(0.75D);
    BlockPos target=BlockPos.containing(suit.position().add(step));
    if(world.isLoaded(target)&&world.noCollision(suit,suit.getBoundingBox().move(step)))
     suit.setPos(suit.getX()+step.x,suit.getY(),suit.getZ()+step.z);
   }
  }
  if(!turret||!hasModule(suit))return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);
  long now=world.getGameTime(),last=LAST_SHOT.getOrDefault(suit,-1L);
  if(!V176MicroMgRules.canSpawn(EnergyTool.energy(chest),now,last))return;
  Vec3 start=suit.position().add(0,1.45D,0);
  var enemies=world.getEntitiesOfClass(Monster.class,suit.getBoundingBox().inflate(16D),
     e->e.isAlive()&&!e.isAlliedTo(player));
  enemies.sort(Comparator.comparingDouble(e->e.distanceToSqr(suit)));
  for(Monster enemy:enemies){
   if(!world.isLoaded(enemy.blockPosition()))continue;
   Vec3 end=enemy.getEyePosition();
   double sq=start.distanceToSqr(end);
   if(sq>V176MicroMgRules.AUTO_TARGET_RANGE_SQ)continue;
   if(world.clip(new ClipContext(start,end,ClipContext.Block.COLLIDER,
        ClipContext.Fluid.NONE,suit)).getType()!=HitResult.Type.MISS)continue;
   if(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
      true,true,false,true,sq,EnergyTool.energy(chest),now,last))continue;
   Vec3 dir=end.subtract(start).normalize();
   var shot=new V176MicroMgProjectile(
      dev.obsidiannetwork.ObsidianNetwork.MICRO_MG_PROJECTILE.get(),world);
   shot.setOwner(player);
   shot.setPos(start.x,start.y,start.z);
   shot.shoot(dir.x,dir.y,dir.z,3.0F,0.7F);
   String raw=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   V176LootingEvents.mark(shot,V176LootingSupport.level(raw));
   if(!world.addFreshEntity(shot))break;
   if(!EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)){
    shot.discard();break;
   }
   LAST_SHOT.put(suit,now);
   world.sendParticles(ParticleTypes.END_ROD,start.x,start.y,start.z,
     2,0.05,0.05,0.05,0.02);
   world.playSound(null,suit.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
     SoundSource.PLAYERS,0.45F,1.7F);
   break;
  }
 }
}
''')
print("V176_B676_FOLLOW_TURRET_EXCLUSIVE_MODES PASS")
