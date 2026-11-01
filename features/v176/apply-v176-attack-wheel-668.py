#!/usr/bin/env python3
"""B668: install module-gated Attack Mode radial action and server-synced actionbar.

Designed against B667 reconstructed NeoForge 26.1 source contract. This patch
does NOT turn on weapon fire until projectile collision and FE authorization
are implemented. Leaves the legacy 4/5 action sectors byte-for-byte equivalent
when the module is absent.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel, old, new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B668_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# Never register on the default branch or duplicate a server command.
edit("powerarmor/PowerArmorCommands.java",
 '   .then(Commands.literal("nightvision").executes(c->night(c.getSource().getPlayerOrException()))));',
 '   .then(Commands.literal("nightvision").executes(c->night(c.getSource().getPlayerOrException())))\n'
 '   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException()))));')
# Existing PowerArmorRuntime is already subscribed by the mod.
edit("powerarmor/PowerArmorRuntime.java",
 '   if(!(event.getEntity() instanceof ServerPlayer p))return;\n   if(p.tickCount%5!=0)return;',
 '   if(!(event.getEntity() instanceof ServerPlayer p))return;\n'
 '   V176AttackModeServer.maintain(p);\n   if(p.tickCount%5!=0)return;')
# The world stand must not inherit an active "worn gun" mode on transfer.
edit("powerarmor/PowerArmorSuitWorld.java",
 '   for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)worn.add(player.getItemBySlot(slot).copy());',
 '   for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)worn.add(player.getItemBySlot(slot).copy());\n'
 '   V176AttackModeServer.clearFromChest(worn.get(1));')

wheel="client/NetworkActionWheelClient.java"
s=(J/wheel).read_text(encoding="utf-8")
start=s.index(' private static int wheelSector(double dx,double dy,boolean vision){')
end=s.index(' @SubscribeEvent public static void register(RegisterKeyMappingsEvent e)',start)
before=s[start:end]
assert "if(!vision)return Math.abs(dx)>Math.abs(dy)?" in before and "case 0->0;case 1->1;case 2->4" in before,("B668_WHEEL_SOURCE_DRIFT",before)
# Preserve angular selection exactly for classic 4 and 5 wedge modes.
replacement=''' // For users without a Micro-MG the original 4/5 sectors remain identical.
 // ATTACK is present only on a fully worn suit with its installed module.
 private static int[] wheelActions(boolean vision,boolean attack){
  if(vision&&attack)return new int[]{0,1,4,5,2,3};
  if(vision)return new int[]{0,1,4,2,3};
  if(attack)return new int[]{0,1,5,2,3};
  return new int[]{0,1,2,3};
 }
 private static int wheelSector(double dx,double dy,int[] order){
  if(order.length==4)
   return Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0);
  double angle=Math.atan2(dy,dx)+Math.PI/2D;
  if(angle<0)angle+=Math.PI*2D;
  int count=order.length;
  int slice=(int)Math.floor((angle+Math.PI/count)/(Math.PI*2D/count))%count;
  return order[slice];
 }
'''
s=s[:start]+replacement+s[end:]
assert s.count('case 4->NetworkVisionClient.toggleFromWheel();')==1
s=s.replace('case 4->NetworkVisionClient.toggleFromWheel();',
'''case 4->NetworkVisionClient.toggleFromWheel();
     case 5->V176AttackModeClient.toggleFromWheel();''',1)
assert s.count('wheelSector(dx,dy,NetworkVisionClient.installed())')==1
s=s.replace('wheelSector(dx,dy,NetworkVisionClient.installed())',
 '''wheelSector(dx,dy,wheelActions(NetworkVisionClient.installed(),
         V176AttackModeClient.available()))''',1)
assert s.count('  boolean hasVision=NetworkVisionClient.installed();')==1
s=s.replace('  boolean hasVision=NetworkVisionClient.installed();',
 '''  boolean hasVision=NetworkVisionClient.installed();
  boolean hasAttack=V176AttackModeClient.available();
  int[] order=wheelActions(hasVision,hasAttack);''',1)
assert s.count('wheelSector(start,yy,hasVision)')==1 and s.count('wheelSector(stop,yy,hasVision)')==1
s=s.replace('wheelSector(start,yy,hasVision)','wheelSector(start,yy,order)',1)
s=s.replace('wheelSector(stop,yy,hasVision)','wheelSector(stop,yy,order)',1)
assert s.count('  int[] order=hasVision?new int[]{0,1,4,2,3}:new int[]{0,1,2,3};')==1
s=s.replace('  int[] order=hasVision?new int[]{0,1,4,2,3}:new int[]{0,1,2,3};','',1)
assert s.count('String name=i==4?"VISION":ACTIONS[i];')==1
s=s.replace('String name=i==4?"VISION":ACTIONS[i];',
 'String name=i==4?"VISION":i==5?("ATTACK "+(V176AttackModeClient.active()?"ON":"OFF")):ACTIONS[i];',1)
(J/wheel).write_text(s,encoding="utf-8")

server=J/"powerarmor/V176AttackModeServer.java"
assert not server.exists()
server.write_text('''package dev.obsidiannetwork.powerarmor;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Server-only authoritative manual Attack Mode toggle; weapon fire is gated separately. */
public final class V176AttackModeServer {
 private V176AttackModeServer(){}
 private static final String ACTIVE="micro_mg_on";
 private static List<String> tokens(String raw){
  return new ArrayList<>(raw==null||raw.isEmpty()?List.of():Arrays.asList(raw.split(",")));
 }
 private static String cards(ItemStack chest){
  return chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
 }
 public static boolean on(ServerPlayer p){
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg"))return false;
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  return tokens(cards(chest)).contains(ACTIVE);
 }
 public static void clearFromChest(ItemStack chest){
  if(chest.isEmpty())return;
  String old=cards(chest);
  if(old==null)return;
  var list=tokens(old);
  if(list.removeIf(ACTIVE::equals))
   chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",list));
 }
 private static void message(ServerPlayer p,boolean active){
  p.connection.send(new ClientboundSetActionBarTextPacket(
    Component.literal(V176MicroMgRules.actionbar(active))));
 }
 public static int toggle(ServerPlayer p){
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg"))return 0;
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  var list=tokens(cards(chest));
  boolean active=!list.contains(ACTIVE);
  list.removeIf(ACTIVE::equals);
  if(active)list.add(ACTIVE);
  chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",list));
  message(p,active);
  return 1;
 }
 public static void maintain(ServerPlayer p){
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg")){
   if(chest!=null&&!chest.isEmpty()&&tokens(cards(chest)).contains(ACTIVE)){
    clearFromChest(chest);
    message(p,false);
   }
   return;
  }
  if(on(p)&&p.tickCount%30==0)message(p,true);
 }
}
''',encoding="utf-8")

client=J/"client/V176AttackModeClient.java"
assert not client.exists()
client.write_text('''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import java.util.Arrays;

/** Check worn armor and actual module, never add an unavailable wheel action. */
public final class V176AttackModeClient {
 private V176AttackModeClient(){}
 private static String upgrades(){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null)return "";
  ItemStack chest=mc.player.getItemBySlot(EquipmentSlot.CHEST);
  String raw=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return raw==null?"":raw;
 }
 private static boolean token(String name){
  return Arrays.asList(upgrades().split(",")).contains(name);
 }
 public static boolean available(){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return false;
  int tier=PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier==0)return false;
  for(int i=1;i<PowerArmorRuntime.SLOTS.length;i++)
   if(PowerArmorRuntime.tier(mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)return false;
  return token("micro_mg");
 }
 public static boolean active(){return available()&&token("micro_mg_on");}
 public static void toggleFromWheel(){
  var mc=Minecraft.getInstance();
  if(available()&&mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand("powerarmor attack");
 }
}
''',encoding="utf-8")
assert "case 5->V176AttackModeClient.toggleFromWheel();" in s
assert "int[] order=wheelActions(hasVision,hasAttack);" in s
assert "V176AttackModeServer.maintain(p);" in (J/"powerarmor/PowerArmorRuntime.java").read_text()
print("V176_B668_MODULE_ONLY_RADIAL_ATTACK_TOGGLE_SYNCED_ACTIONBAR_PASS")
