#!/usr/bin/env python3
"""Add Power Armor suit sleep command/action-wheel action after B757.

Sleep is server-authorized: complete worn suit, night, hostile radius, safe
standing location. All living non-spectator players in the same dimension
must participate to advance dawn; it cannot silently skip others' nights.
No bed is required. Does not touch armor inventory or equipment ownership.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(path, needle, replacement):
    p=J/path
    data=p.read_text(encoding="utf-8")
    assert data.count(needle)==1,("V176_SLEEP_ANCHOR_DRIFT",path,needle[:180],data.count(needle))
    p.write_text(data.replace(needle,replacement,1),encoding="utf-8")

def add(path, content):
    p=J/path
    p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),("V176_SLEEP_DUPLICATE_CLASS",str(p))
    p.write_text(content,encoding="utf-8")

edit("powerarmor/PowerArmorCommands.java",
'''   .then(Commands.literal("turret").executes(c->V176CompanionMode.toggle(c.getSource().getPlayerOrException(),true))));''',
'''   .then(Commands.literal("turret").executes(c->V176CompanionMode.toggle(c.getSource().getPlayerOrException(),true)))
   .then(Commands.literal("sleep").executes(c->V176PowerSleepServer.toggle(c.getSource().getPlayerOrException()))));''')

wheel=J/"client/NetworkActionWheelClient.java"
src=wheel.read_text(encoding="utf-8")
start=src.index(" private static int[] wheelActions(boolean vision,boolean attack){")
end=src.index(" private static int wheelSector(",start)
assert "V176CompanionClient.actions(vision)" in src[start:end]
src=src[:start]+''' private static int[] wheelActions(boolean vision,boolean attack){
  int[] companion=V176CompanionClient.actions(vision);
  if(companion!=null)return companion;
  int[] base;
  if(vision&&attack)base=new int[]{0,1,4,5,2,3};
  else if(vision)base=new int[]{0,1,4,2,3};
  else if(attack)base=new int[]{0,1,5,2,3};
  else base=new int[]{0,1,2,3};
  if(!V176PowerSleepClient.available())return base;
  int[] actions=java.util.Arrays.copyOf(base,base.length+1);
  actions[base.length]=8;
  return actions;
 }
'''+src[end:]
assert src.count('case 7->V176CompanionClient.toggleTurret();')==1
src=src.replace('case 7->V176CompanionClient.toggleTurret();',
'''case 7->V176CompanionClient.toggleTurret();
     case 8->V176PowerSleepClient.toggle();''',1)
old='i==6?"FOLLOW":i==7?"TURRET":ACTIONS[i];'
assert src.count(old)==1,("V176_SLEEP_LABEL_DRIFT",src.count(old))
src=src.replace(old,'i==6?"FOLLOW":i==7?"TURRET":i==8?"SLEEP":ACTIONS[i];',1)
wheel.write_text(src,encoding="utf-8")

add("client/V176PowerSleepClient.java",'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import net.minecraft.client.Minecraft;

/** Sleep sector exists on the wheel only while a COMPLETE suit is worn. */
public final class V176PowerSleepClient {
 private V176PowerSleepClient(){}
 public static boolean available(){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return false;
  int tier=PowerArmorRuntime.tier(
       mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  if(tier<=0)return false;
  for(int slot=1;slot<PowerArmorRuntime.SLOTS.length;slot++)
   if(PowerArmorRuntime.tier(
       mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[slot]),slot)!=tier)
    return false;
  return true;
 }
 public static void toggle(){
  var mc=Minecraft.getInstance();
  if(available()&&mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand("powerarmor sleep");
 }
}
''')

add("powerarmor/V176PowerSleepServer.java",'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import java.util.Map;
import java.util.WeakHashMap;

/** Armor sleep does not consume, replace, drop or unequip ANY armor item. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176PowerSleepServer {
 private V176PowerSleepServer(){}
 private static final Map<ServerPlayer,Integer> SLEEPING=new WeakHashMap<>();
 private static boolean night(ServerLevel w){
  long time=Math.floorMod(w.getDayTime(),24000L);
  return time>=12542L && time<=23460L;
 }
 private static boolean hostile(ServerPlayer p){
  var monsters=p.level().getEntitiesOfClass(Monster.class,
     p.getBoundingBox().inflate(8.0D,5.0D,8.0D),e->e.isAlive());
  return !monsters.isEmpty();
 }
 private static boolean safe(ServerPlayer p){
  return p.onGround()&&!p.isPassenger()&&!p.isInWaterOrBubble()&&p.isAlive();
 }
 private static void say(ServerPlayer p,String s){
  p.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(s)));
 }
 private static void stop(ServerPlayer p,String msg){
  if(SLEEPING.remove(p)!=null){
   p.setPose(Pose.STANDING);
   say(p,msg);
  }
 }
 public static int toggle(ServerPlayer p){
  if(SLEEPING.containsKey(p)){
   stop(p,"Power Armor Sleep: OFF");return 1;
  }
  if(!(p.level() instanceof ServerLevel world))return 0;
  var check=V176PowerSleepRules.validate(PowerArmorRuntime.full(p),
       night(world),hostile(p),safe(p),false);
  if(check!=V176PowerSleepRules.Rejection.NONE){
   say(p,"Power Armor Sleep: "+check.name().replace('_',' '));
   return 0;
  }
  V176AttackModeServer.clearFromChest(p.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST));
  SLEEPING.put(p,0);
  p.setPose(Pose.SLEEPING);
  say(p,"Power Armor Sleep: ON");
  return 1;
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer p)||!SLEEPING.containsKey(p))return;
  if(!(p.level() instanceof ServerLevel world)){
   stop(p,"Power Armor Sleep: OFF");return;
  }
  if(!PowerArmorRuntime.full(p)||!night(world)||hostile(p)||!p.isAlive()){
   stop(p,"Power Armor Sleep: CANCELLED");return;
  }
  p.setDeltaMovement(Vec3.ZERO);
  p.setPose(Pose.SLEEPING);
  int elapsed=SLEEPING.get(p)+1;
  SLEEPING.put(p,elapsed);
  if(elapsed<100)return; // five seconds of the synchronized sleeping pose
  for(ServerPlayer other:world.players()){
   if(other.isAlive()&&!other.isSpectator()&&!SLEEPING.containsKey(other))
    return; // never skip another player's night without their consent
  }
  long day=world.getDayTime();
  world.setDayTime(Math.multiplyExact(Math.addExact(Math.floorDiv(day,24000L),1L),24000L));
  for(ServerPlayer other:java.util.List.copyOf(SLEEPING.keySet())){
   if(other.level()==world)stop(other,"Power Armor Sleep: MORNING");
  }
 }
}
''')

print("V176_SLEEP_ACTION_WHEEL_SERVER_NIGHT_HOSTILE_MULTIPLAYER_GATES_INSTALLED")
