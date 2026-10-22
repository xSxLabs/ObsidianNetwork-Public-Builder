#!/usr/bin/env python3
"""Clean v1.7 stage 4: stations are player-placed upgrade benches only.

A free-standing suit is a protected vanilla ArmorStand containing the ACTUAL
four Power Armor ItemStacks (energy, cards and components intact).
Entering: right-click the suit. Exiting: V / /powerarmor exit.
Initial placement: wear a full suit and run /powerarmor deploy.
Neither entering nor exiting consumes or creates an Armor Station.
"""
from pathlib import Path
import os

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(relative, before, after, label):
    p=j/relative
    src=p.read_text(encoding="utf-8")
    n=src.count(before)
    assert n==1, "FREE_STAND_%s source anchor count=%d file=%s"%(label,n,relative)
    p.write_text(src.replace(before,after,1),encoding="utf-8")

# Both activation paths use the same server-side equipment ownership guard.
f=j/"powerarmor/PowerArmorSuitWorld.java"
assert not f.exists(),"Free-standing suit runtime already exists"
f.write_text(r'''package dev.obsidiannetwork.powerarmor;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * A vanilla ArmorStand provides native armor rendering, persistence and
 * 2-block human proportions. It is not an Armor Station or a free station item.
 * All item transfers happen on the server, after validation of the full suit.
 */
public final class PowerArmorSuitWorld {
 private static final String MARKER="xsxlabs_power_armor_suit_v17";
 private static final String OWNER_PREFIX="xsxlabs_power_armor_owner_";
 private PowerArmorSuitWorld(){}
 private static String owner(ServerPlayer player){return OWNER_PREFIX+player.getUUID();}
 private static boolean mine(ArmorStand stand,ServerPlayer player){
  return stand.getTags().contains(MARKER)&&stand.getTags().contains(owner(player));
 }
 public static boolean full(ArmorStand stand){
  for(int i=0;i<4;i++){
   if(!stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]).is(
        ArmorStationBlockEntity.expected(i)))return false;
  }
  return true;
 }
 /** Refuse to pick one of several suits silently. */
 public static ArmorStand findNearby(Level level,BlockPos station,ServerPlayer player){
  List<ArmorStand> suits=level.getEntitiesOfClass(ArmorStand.class,
      new AABB(station).inflate(3.0D), e->mine(e,player)&&full(e));
  return suits.size()==1?suits.get(0):null;
 }
 private static BlockPos available(ServerPlayer player){
  Level level=player.level();
  for(var direction:net.minecraft.core.Direction.Plane.HORIZONTAL){
   BlockPos p=player.blockPosition().relative(direction);
   if(!level.isEmptyBlock(p)||!level.isEmptyBlock(p.above()))continue;
   if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(p).inflate(0.25D)).isEmpty())continue;
   return p;
  }
  return null;
 }
 private static boolean spawn(ServerPlayer player,List<ItemStack> suit){
  if(suit.size()!=4)return false;
  for(int i=0;i<4;i++)if(!suit.get(i).is(ArmorStationBlockEntity.expected(i)))return false;
  BlockPos pos=available(player);
  if(pos==null){
   player.sendSystemMessage(Component.literal("Power Armor: need two free blocks next to you."));
   return false;
  }
  Level level=player.level();
  ArmorStand stand=new ArmorStand(level,pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);
  stand.addTag(MARKER);
  stand.addTag(owner(player));
  stand.setInvulnerable(true);
  stand.setNoGravity(true);
  stand.setShowArms(true);
  stand.setNoBasePlate(true);
  for(int i=0;i<4;i++)stand.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i).copy());
  if(!level.addFreshEntity(stand))return false;
  return true;
 }
 /** Initial setup without any station; cannot run with an unresolved backup. */
 public static int deploy(ServerPlayer player){
  if(ArmorLoadoutData.get(player.level().getServer()).has(player)){
   player.sendSystemMessage(Component.literal(
    "Power Armor: saved previous armor exists. Exit with V instead."));
   return 0;
  }
  if(!PowerArmorRuntime.full(player)){
   player.sendSystemMessage(Component.literal(
    "Power Armor: equip all four pieces before using /powerarmor deploy."));
   return 0;
  }
  List<ItemStack> suit=new ArrayList<>();
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)suit.add(player.getItemBySlot(slot).copy());
  if(!spawn(player,suit))return 0;
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)player.setItemSlot(slot,ItemStack.EMPTY);
  player.sendSystemMessage(Component.literal(
   "Power Armor deployed. Right-click the standing suit to enter."));
  return 1;
 }
 /** Exit never creates or places an Armor Station. */
 public static int exit(ServerPlayer player){
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  var backup=saved.get(player);
  if(backup==null||!PowerArmorRuntime.full(player))return 0;
  List<ItemStack> suit=new ArrayList<>();
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)suit.add(player.getItemBySlot(slot).copy());
  if(!spawn(player,suit))return 0;
  for(int i=0;i<4;i++)player.setItemSlot(
      PowerArmorRuntime.SLOTS[i],backup.previous().get(i).copy());
  saved.finish(player);
  player.sendSystemMessage(Component.literal(
   "Power Armor exited. Original equipment restored; suit stands beside you."));
  return 1;
 }
 // Armor stands normally consume the "interact at" route first; intercept it
 // before vanilla swaps any of the suit pieces with the player's held item.
 @SubscribeEvent public static void interactSpecific(PlayerInteractEvent.EntityInteractSpecific event){
  Entity target=event.getTarget();
  if(!(target instanceof ArmorStand stand)||!stand.getTags().contains(MARKER))return;
  event.setCanceled(true);
  event.setCancellationResult(InteractionResult.SUCCESS);
  if(event.getHand()==net.minecraft.world.InteractionHand.MAIN_HAND)
   enter(stand,event.getEntity());
 }
 @SubscribeEvent public static void interact(PlayerInteractEvent.EntityInteract event){
  Entity target=event.getTarget();
  if(!(target instanceof ArmorStand stand)||!stand.getTags().contains(MARKER))return;
  event.setCanceled(true);
  event.setCancellationResult(InteractionResult.SUCCESS);
  if(event.getHand()==net.minecraft.world.InteractionHand.MAIN_HAND)
   enter(stand,event.getEntity());
 }
 private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){
  if(!(actor instanceof ServerPlayer player))return;
  if(!mine(stand,player)){
   player.sendSystemMessage(Component.literal("Power Armor: this suit belongs to another player."));
   return;
  }
  if(!full(stand)){
   player.sendSystemMessage(Component.literal("Power Armor: suit is incomplete; no items moved."));
   return;
  }
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  if(saved.has(player)){
   player.sendSystemMessage(Component.literal(
    "Power Armor: existing armor backup must be resolved first."));
   return;
  }
  List<ItemStack> original=new ArrayList<>();
  List<ItemStack> suit=new ArrayList<>();
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){
   original.add(player.getItemBySlot(slot).copy());
   suit.add(stand.getItemBySlot(slot).copy());
  }
  // Preserve the old armor FIRST. A failed backup must never touch either suit.
  if(!saved.save(player,original))return;
  for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i));
  // Remove the ACTUAL world entity; never leave a second, lootable suit behind.
  stand.discard();
  player.sendSystemMessage(Component.literal(
   "Power Armor engaged. Press the rebindable Exit Power Armor key to leave."));
 }
}
''',encoding="utf-8")

patch("ObsidianNetwork.java",
      "net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.class);",
      "net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.class);\n"
      "      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.class);",
      "register_free_suit")

p=j/"powerarmor/PowerArmorCommands.java"
s=p.read_text(encoding="utf-8")
old='''   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException())))'''
assert s.count(old)==1, "Commands registration drift"
s=s.replace(old,'''   .then(Commands.literal("deploy").executes(c->PowerArmorSuitWorld.deploy(c.getSource().getPlayerOrException())))
   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException())))''',1)
start=s.index(" public static int exit(ServerPlayer p){")
end=s.index(" public static int night(ServerPlayer p){",start)
assert "ObsidianNetwork.ARMOR_STATION.get().defaultBlockState()" in s[start:end], "Expected obsolete station spawning path"
s=s[:start]+''' public static int exit(ServerPlayer p){
  return PowerArmorSuitWorld.exit(p);
 }
'''+s[end:]
p.write_text(s,encoding="utf-8")

p=j/"powerarmor/ArmorStationBlock.java"
s=p.read_text(encoding="utf-8")
assert s.count("// CLEAN_V17_CARDS_V1: installation/deinstallation is station-only.")==1
s=s.replace("// CLEAN_V17_CARDS_V1: installation/deinstallation is station-only.",
'''// Station upgrades a nearby OWNED standing suit. Entry/exit never use a station.''',1)
old='''   if(!station.complete())return InteractionResult.FAIL;
   ItemStack chest=station.get(1).copy();'''
new='''   var suitStand=PowerArmorSuitWorld.findNearby(level,pos,p);
   if(suitStand==null){
    p.sendSystemMessage(Component.literal("Armor Station: place one of your complete suits nearby."));
    return InteractionResult.FAIL;
   }
   ItemStack chest=suitStand.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).copy();'''
assert s.count(old)==1,"Upgrade install target drift"
s=s.replace(old,new,1)
old='''  if(p.isShiftKeyDown()&&held.isEmpty()&&station.complete()){
   ItemStack chest=station.get(1).copy();'''
new='''  if(p.isShiftKeyDown()&&held.isEmpty()
     &&PowerArmorSuitWorld.findNearby(level,pos,p)!=null){
   var suitStand=PowerArmorSuitWorld.findNearby(level,pos,p);
   ItemStack chest=suitStand.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).copy();'''
assert s.count(old)==1,"Upgrade uninstall target drift"
s=s.replace(old,new,1)
assert s.count("station.put(1,chest);")==2,"Card write target drift"
s=s.replace("station.put(1,chest);",
            "suitStand.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST,chest);")
# Disallow normal station equipment and player entry. An old stored loadout
# remains extractable via sneak+empty-hand for save compatibility.
start=s.index("   if(!station.complete()){")
end=s.index("   return InteractionResult.SUCCESS;",s.index("Power Armor engaged.",start))
end=s.index("\n",end)+1
assert "loadouts.save(p,old)" in s[start:end] and "station.clear();" in s[start:end]
s=s[:start]+'''   p.sendSystemMessage(Component.literal(
     "Armor Station manages upgrades only. Right-click the standing suit to enter."));
   return InteractionResult.SUCCESS;
'''+s[end:]
# Original method closing brace must remain; explicitly reject inserting new
# individual armor items into a player-placed upgrade bench.
start=s.index("    for(int i=0;i<4;i++){",s.index("// Sneak + right click mounts"))
end=s.index("    return InteractionResult.PASS;",start)
assert "station.put(i,stack.split(1))" in s[start:end]
s=s[:start]+'''    p.sendSystemMessage(Component.literal(
      "Armor Station is for upgrades. Deploy a full suit with /powerarmor deploy."));
'''+s[end:]
p.write_text(s,encoding="utf-8")

# The old animation prototype used the station as a world suit, leaving a
# temporary empty station in the world. Stop doing that. Stations are only
# blocks the player explicitly placed, never animation carriers on entry/exit.
p=j/"powerarmor/ArmorStationBlockEntity.java"
s=p.read_text(encoding="utf-8")
# Animation fields/methods stay for backwards-compatible placed station states;
# no runtime transition is initiated when entering or exiting in the new design.
p.write_text(s,encoding="utf-8")
print("CLEAN_V17_FREE_STANDING_SUIT PASS: deploy & exit spawn only owned armor stands; station upgrades nearby suits; no station is created/consumed")
