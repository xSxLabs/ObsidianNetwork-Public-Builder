#!/usr/bin/env python3
"""Charge each player inventory category once per 20 ticks, not once per network.

Preserves each named network's independent enable mask and transaction-safe
chargeOne implementation. No per-block/player scanning is introduced.
"""
import os
from pathlib import Path

base=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
target=base/"wireless/WirelessPlayerCharging.java"
s=target.read_text()
start=' @net.neoforged.bus.api.SubscribeEvent\n public static void tick(PlayerTickEvent.Post event){'
end=' static int chargeOne(ServerPlayer player,String network,ItemStack stack,int budget){'
assert s.count(start)==1 and s.count(end)==1, "Wireless player charging source drift"
a=s.index(start);b=s.index(end,a)
new=r''' @net.neoforged.bus.api.SubscribeEvent
 public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)||player.level().getGameTime()%20!=0)return;
  var gameServer=player.level().getServer();
  var saved=WirelessNetworkData.get(gameServer);
  // Bound player workload independently of number of transmitters/receivers.
  int remaining=MAX_PER_PLAYER_TICK;
  java.util.ArrayList<WirelessNetworkData.Entry> active=new java.util.ArrayList<>();
  for(var network:saved.available(player)){
   if(network.chargingMask()!=0&&WirelessEnergyRuntime.available(gameServer,network.id())>0)
    active.add(network);
  }
  if(active.isEmpty())return;
  // Each inventory ItemStack is enumerated once per player/interval, while
  // matching enabled networks may participate in filling that same stack.
  var inventory=player.getInventory().getNonEquipmentItems();
  for(int i=0;i<inventory.size()&&remaining>0;i++){
   int category=i<9?WirelessNetworkData.HOTBAR:WirelessNetworkData.INVENTORY;
   ItemStack stack=inventory.get(i);
   if(stack.isEmpty())continue;
   for(var network:active){
    if((network.chargingMask()&category)==0)continue;
    remaining-=chargeOne(player,network.id(),stack,remaining);
    if(remaining<=0)break;
   }
  }
  for(EquipmentSlot slot:new EquipmentSlot[]{EquipmentSlot.HEAD,EquipmentSlot.CHEST,EquipmentSlot.LEGS,EquipmentSlot.FEET}){
   if(remaining<=0)break;
   ItemStack stack=player.getItemBySlot(slot);
   if(stack.isEmpty())continue;
   for(var network:active){
    if((network.chargingMask()&WirelessNetworkData.ARMOR)==0)continue;
    remaining-=chargeOne(player,network.id(),stack,remaining);
    if(remaining<=0)break;
   }
  }
  if(remaining>0){
   ItemStack stack=player.getItemBySlot(EquipmentSlot.OFFHAND);
   if(!stack.isEmpty())for(var network:active){
    if((network.chargingMask()&WirelessNetworkData.OFFHAND)==0)continue;
    remaining-=chargeOne(player,network.id(),stack,remaining);
    if(remaining<=0)break;
   }
  }
  // Never resolve/load the Curios adapter when Curios is absent.
  if(remaining>0&&ModList.get().isLoaded("curios"))
   remaining-=WirelessCuriosCharging.charge(player,active,remaining);
 }
'''
target.write_text(s[:a]+new+s[b:])

p=base/"wireless/WirelessCuriosCharging.java"
s=p.read_text()
old=r''' static int charge(ServerPlayer player,String netId,int limit){
  int used=0;
  var optional=CuriosApi.getCuriosInventory(player);
  if(optional.isEmpty())return 0;
  for(var handler:optional.get().getCurios().values()){
   var stacks=handler.getStacks();
   for(int i=0;i<stacks.getSlots()&&used<limit;i++)
    used+=WirelessPlayerCharging.chargeOne(player,netId,stacks.getStackInSlot(i),limit-used);
  }
  return used;
 }'''
new=r''' static int charge(ServerPlayer player,java.util.List<WirelessNetworkData.Entry> networks,int limit){
  int used=0;
  var optional=CuriosApi.getCuriosInventory(player);
  if(optional.isEmpty())return 0;
  for(var handler:optional.get().getCurios().values()){
   var stacks=handler.getStacks();
   for(int i=0;i<stacks.getSlots()&&used<limit;i++){
    var stack=stacks.getStackInSlot(i);
    if(stack.isEmpty())continue;
    for(var network:networks){
     if((network.chargingMask()&WirelessNetworkData.CURIOS)==0)continue;
     used+=WirelessPlayerCharging.chargeOne(player,network.id(),stack,limit-used);
     if(used>=limit)break;
    }
   }
  }
  return used;
 }'''
assert s.count(old)==1, "Curios charging source drift"
p.write_text(s.replace(old,new,1))
print("WIRELESS_CHARGING_SINGLE_PASS_V1 PASS")
