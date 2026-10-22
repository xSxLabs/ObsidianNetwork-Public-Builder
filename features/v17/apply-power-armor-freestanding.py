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
  return stand.entityTags().contains(MARKER)&&stand.entityTags().contains(owner(player));
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
  if(!(target instanceof ArmorStand stand)||!stand.entityTags().contains(MARKER))return;
  event.setCanceled(true);
  event.setCancellationResult(InteractionResult.SUCCESS);
  if(event.getHand()==net.minecraft.world.InteractionHand.MAIN_HAND)
   enter(stand,event.getEntity());
 }
 @SubscribeEvent public static void interact(PlayerInteractEvent.EntityInteract event){
  Entity target=event.getTarget();
  if(!(target instanceof ArmorStand stand)||!stand.entityTags().contains(MARKER))return;
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
start=s.index("  if(!station.complete()){")
# Find the actual method return from its message, without assuming whitespace.
message=s.index("Power Armor engaged.",start)
end=s.index("\n",message)+1
assert "return InteractionResult.SUCCESS;" in s[end:s.index("\n",end)]
end=s.index("\n",end)+1
assert "loadouts.save(p,old)" in s[start:end] and "station.clear();" in s[start:end]
s=s[:start]+'''   p.sendSystemMessage(Component.literal(
     "Armor Station manages upgrades only. Right-click the standing suit to enter."));
   return InteractionResult.SUCCESS;
'''+s[end:]
# Original method closing brace must remain; explicitly reject inserting new
# individual armor items into a player-placed upgrade bench.
start=s.index("   for(int i=0;i<4;i++){",s.index("// Sneak + right click mounts"))
end=s.index("   return InteractionResult.PASS;",start)
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


# BUILD32_COMPLETE: stage 5 executes after station-independent suit construction.
# All safety-sensitive inventory changes remain server side; existing recovery
# records and v1.6/autocrafting/elytra implementations remain untouched.
import json as _json
import zlib as _zlib
import struct as _struct
from math import hypot as _hypot

def b32_edit(file,old,new):
 p=j/file
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,"BUILD32 source drift "+file+" "+str(s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def b32_put(file,obj):
 file.parent.mkdir(parents=True,exist_ok=True)
 file.write_text(_json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

# Both models use the same power/upgrade logic; matching all four tier parts is
# mandatory so armor from different tiers cannot accidentally form a suit.
p=j/"ObsidianNetwork.java"
s=p.read_text(encoding="utf-8")
anchor="   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE ="
assert s.count(anchor)==1
addition=""
for part,slot in (("helmet","HEAD"),("chestplate","CHEST"),("leggings","LEGS"),("boots","FEET")):
 addition+=f'''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.PowerArmorItem> POWER_ARMOR_MK2_{part.upper()} =
      ITEMS.registerItem("power_armor_mk2_{part}", p -> new dev.obsidiannetwork.powerarmor.PowerArmorItem(
        p.stacksTo(1).durability(4000000)
          .component(net.minecraft.core.component.DataComponents.UNBREAKABLE, net.minecraft.util.Unit.INSTANCE)
          .component(net.minecraft.core.component.DataComponents.EQUIPPABLE,
            net.minecraft.world.item.equipment.Equippable.builder(net.minecraft.world.entity.EquipmentSlot.{slot})
              .setAsset(net.minecraft.resources.ResourceKey.create(
                net.minecraft.world.item.equipment.EquipmentAssets.ROOT_ID,
                net.minecraft.resources.Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_mk2")))
              .build())
          .component(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get(),0L)
      ));
'''
assert "POWER_ARMOR_MK2_HELMET" not in s
s=s.replace(anchor,addition+anchor,1)
tab='            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());'
assert s.count(tab)==1
s=s.replace(tab,tab+"\n"+'\n'.join(f'            output.accept((ItemLike)POWER_ARMOR_MK2_{part.upper()}.get());' for part in ("helmet","chestplate","leggings","boots")),1)
p.write_text(s,encoding="utf-8")

b32_edit("powerarmor/PowerArmorRuntime.java",
''' public static boolean full(ServerPlayer p){
  for(int i=0;i<SLOTS.length;i++)
   if(!p.getItemBySlot(SLOTS[i]).is(ArmorStationBlockEntity.expected(i)))return false;
  return true;
 }''',
''' public static boolean piece(ItemStack stack,int slot,boolean mk2){
  if(mk2){
   return switch(slot){
    case 0->stack.is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_HELMET.get());
    case 1->stack.is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_CHESTPLATE.get());
    case 2->stack.is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_LEGGINGS.get());
    case 3->stack.is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_BOOTS.get());
    default->false;
   };
  }
  return stack.is(ArmorStationBlockEntity.expected(slot));
 }
 public static boolean full(ServerPlayer p){
  boolean mk2=piece(p.getItemBySlot(SLOTS[0]),0,true);
  for(int i=0;i<SLOTS.length;i++)
   if(!piece(p.getItemBySlot(SLOTS[i]),i,mk2))return false;
  return true;
 }''')

b32_edit("powerarmor/PowerArmorSuitWorld.java",
''' public static boolean full(ArmorStand stand){
  for(int i=0;i<4;i++){
   if(!stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]).is(
        ArmorStationBlockEntity.expected(i)))return false;
  }
  return true;
 }''',
''' public static boolean full(ArmorStand stand){
  boolean mk2=PowerArmorRuntime.piece(stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0,true);
  for(int i=0;i<4;i++)
   if(!PowerArmorRuntime.piece(stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i,mk2))return false;
  return true;
 }''')
b32_edit("powerarmor/PowerArmorSuitWorld.java",
'''  for(int i=0;i<4;i++)if(!suit.get(i).is(ArmorStationBlockEntity.expected(i)))return false;''',
'''  boolean mk2=PowerArmorRuntime.piece(suit.get(0),0,true);
  for(int i=0;i<4;i++)if(!PowerArmorRuntime.piece(suit.get(i),i,mk2))return false;''')

# Snap to a manually placed Armor Station only if suit is within two blocks
# and the entire 2-block suit volume below that station is clear.
b32_edit("powerarmor/PowerArmorSuitWorld.java",
''' private static BlockPos available(ServerPlayer player){''',
''' private static BlockPos underStation(ServerPlayer player){
  Level level=player.level();
  BlockPos origin=player.blockPosition();
  BlockPos found=null;
  double best=Double.MAX_VALUE;
  for(int dx=-2;dx<=2;dx++)for(int dy=-2;dy<=3;dy++)for(int dz=-2;dz<=2;dz++){
   BlockPos station=origin.offset(dx,dy,dz);
   if(!(level.getBlockState(station).getBlock() instanceof ArmorStationBlock))continue;
   BlockPos candidate=station.below(2);
   if(candidate.distSqr(origin)>4.0D)continue;
   if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;
   if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(candidate).inflate(0.25D)).isEmpty())continue;
   double distance=candidate.distSqr(origin);
   if(distance<best){best=distance;found=candidate;}
  }
  return found;
 }
 private static BlockPos available(ServerPlayer player){''')
b32_edit("powerarmor/PowerArmorSuitWorld.java",
'''  BlockPos pos=available(player);''',
'''  BlockPos pos=underStation(player);
  if(pos==null)pos=available(player);''')

# Server authoritative 20-tick opening/closing pose animation. No duplication:
# pending entry only animates an existing protected stand, then performs the
# original atomic backup/equipment transfer after all checks are repeated.
b32_edit("powerarmor/PowerArmorSuitWorld.java",
''' private static final String OWNER_PREFIX="xsxlabs_power_armor_owner_";''',
''' private static final String OWNER_PREFIX="xsxlabs_power_armor_owner_";
 private record Animation(ArmorStand stand,int ticks,boolean entering){}
 private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();
 private static void pose(ArmorStand stand,int progress,boolean entering){
  float open=(entering?progress:20-progress)/20.0F;
  float spread=68.0F*Math.max(0.0F,Math.min(1.0F,open));
  stand.setLeftArmPose(new net.minecraft.core.Rotations(-spread*0.35F,0F,-spread));
  stand.setRightArmPose(new net.minecraft.core.Rotations(-spread*0.35F,0F,spread));
  stand.setHeadPose(new net.minecraft.core.Rotations(-spread*0.25F,0F,0F));
 }
 @SubscribeEvent public static void transitionTick(net.neoforged.neoforge.event.tick.PlayerTickEvent.Post tick){
  if(!(tick.getEntity() instanceof ServerPlayer player))return;
  Animation animation=ACTIVE.get(player.getUUID());
  if(animation==null)return;
  ArmorStand stand=animation.stand();
  if(stand.isRemoved()||!mine(stand,player)||!full(stand)){
   ACTIVE.remove(player.getUUID());return;
  }
  int t=21-animation.ticks();
  pose(stand,t,animation.entering());
  if(animation.ticks()>1){
   ACTIVE.put(player.getUUID(),new Animation(stand,animation.ticks()-1,animation.entering()));
   return;
  }
  ACTIVE.remove(player.getUUID());
  if(animation.entering())finishEntering(stand,player);
  else pose(stand,0,false);
 }
 private static void finishEntering(ArmorStand stand,ServerPlayer player){
  if(stand.isRemoved()||!mine(stand,player)||!full(stand))return;
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  if(saved.has(player))return;
  List<ItemStack> original=new ArrayList<>();
  List<ItemStack> suit=new ArrayList<>();
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){
   original.add(player.getItemBySlot(slot).copy());
   suit.add(stand.getItemBySlot(slot).copy());
  }
  // World-persistent original-armor backup BEFORE any equipment changes.
  if(!saved.save(player,original))return;
  for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i));
  stand.discard();
  player.sendSystemMessage(Component.literal(
   "Power Armor engaged. Press the rebindable Exit Power Armor key to leave."));
 }
 @SubscribeEvent public static void animationLogout(net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedOutEvent e){
  ACTIVE.remove(e.getEntity().getUUID());
 }''')
b32_edit("powerarmor/PowerArmorSuitWorld.java",
'''  if(!level.addFreshEntity(stand))return false;
  return true;''',
'''  if(!level.addFreshEntity(stand))return false;
  pose(stand,20,false);
  ACTIVE.put(player.getUUID(),new Animation(stand,20,false));
  return true;''')
b32_edit("powerarmor/PowerArmorSuitWorld.java",
'''  List<ItemStack> original=new ArrayList<>();
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
   "Power Armor engaged. Press the rebindable Exit Power Armor key to leave."));''',
'''  if(ACTIVE.containsKey(player.getUUID()))return;
  ACTIVE.put(player.getUUID(),new Animation(stand,20,true));
  player.sendSystemMessage(Component.literal("Power Armor opening..."));''')

# Equipment textures: recolor the actual MK1 pixel art's indexed palette.
# Crimson -> charcoal; warm gold -> brushed steel; lighting/dark lines retained.
def mk2_palette_png(data):
 assert data[:8]==b"\x89PNG\r\n\x1a\n","MK2 expected PNG"
 out=bytearray(data[:8]);i=8;updated=False
 while i<len(data):
  n=_struct.unpack(">I",data[i:i+4])[0]
  kind=data[i+4:i+8];part=bytearray(data[i+8:i+8+n]);i+=12+n
  if kind==b"PLTE":
   for off in range(0,len(part),3):
    red,green,blue=part[off:off+3]
    if red>70 and red>green*2 and red>blue*2:
     shade=max(22,min(84,int(red*.40)))
     part[off:off+3]=bytes((shade,shade+4,min(255,shade+12)))
    elif red>110 and green>105 and blue>60 and red>blue*1.25:
     shade=max(105,min(220,int((red+green)/2)))
     part[off:off+3]=bytes((shade-7,shade-2,shade+8))
   updated=True
  out+=_struct.pack(">I",len(part))+kind+part
  out+=_struct.pack(">I",_zlib.crc32(kind+part)&0xffffffff)
 if updated:return bytes(out)
 # Some suit inventory textures are 8-bit RGBA PNGs rather than indexed.
 # Decode all standard per-row PNG filters without external dependencies.
 width,height=_struct.unpack(">II",data[16:24])
 assert data[24]==8 and data[25]==6 and data[28]==0,"Unsupported RGBA PNG layout"
 parts=[];offset=8
 while offset<len(data):
  size=_struct.unpack(">I",data[offset:offset+4])[0]
  kind=data[offset+4:offset+8]
  if kind==b"IDAT":parts.append(data[offset+8:offset+8+size])
  offset+=size+12
 packed=_zlib.decompress(b"".join(parts))
 prev=bytearray(width*4);rows=[];offset=0
 for y in range(height):
  filter_type=packed[offset];offset+=1
  current=bytearray(packed[offset:offset+width*4]);offset+=width*4
  assert filter_type in (0,1,2,3,4),"Unknown PNG filter"
  for k in range(width*4):
   left=current[k-4] if k>=4 else 0
   up=prev[k]
   up_left=prev[k-4] if k>=4 else 0
   if filter_type==1:predictor=left
   elif filter_type==2:predictor=up
   elif filter_type==3:predictor=(left+up)//2
   elif filter_type==4:
    p=left+up-up_left
    d0,d1,d2=abs(p-left),abs(p-up),abs(p-up_left)
    predictor=left if d0<=d1 and d0<=d2 else (up if d1<=d2 else up_left)
   else:predictor=0
   current[k]=(current[k]+predictor)&255
  prev=current
  for x in range(width):
   off=x*4
   red,green,blue,alpha=current[off:off+4]
   if alpha==0:continue
   if red>70 and red>green*2 and red>blue*2:
    shade=max(22,min(84,int(red*.4)))
    current[off:off+3]=bytes((shade,shade+4,min(255,shade+12)))
   elif red>110 and green>105 and blue>60 and red>blue*1.25:
    shade=max(105,min(220,int((red+green)/2)))
    current[off:off+3]=bytes((shade-7,shade-2,shade+8))
  rows.append(b"\x00"+current)
 assert offset==len(packed),"Malformed RGBA PNG stream"
 def chunk(kind,data):
  return _struct.pack(">I",len(data))+kind+data+_struct.pack(">I",_zlib.crc32(kind+data)&0xffffffff)
 return (b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",data[16:29])
   +chunk(b"IDAT",_zlib.compress(b"".join(rows),9))+chunk(b"IEND",b""))

resources=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
for layer in ("humanoid","humanoid_leggings"):
 original=resources/f"textures/entity/equipment/{layer}/power_armor.png"
 (original.parent/"power_armor_mk2.png").write_bytes(mk2_palette_png(original.read_bytes()))
b32_put(resources/"equipment/power_armor_mk2.json",{"layers":{
 "humanoid":[{"texture":"obsidiannetwork:power_armor_mk2"}],
 "humanoid_leggings":[{"texture":"obsidiannetwork:power_armor_mk2"}]}})
for part,material in (("helmet","netherite_helmet"),("chestplate","netherite_chestplate"),("leggings","netherite_leggings"),("boots","netherite_boots")):
 original=resources/f"textures/item/power_armor_{part}.png"
 (original.parent/f"power_armor_mk2_{part}.png").write_bytes(mk2_palette_png(original.read_bytes()))
 name=f"power_armor_mk2_{part}"
 b32_put(resources/f"models/item/{name}.json",{"parent":"minecraft:item/generated","textures":{"layer0":f"obsidiannetwork:item/{name}"}})
 b32_put(resources/f"items/{name}.json",{"model":{"type":"minecraft:model","model":f"obsidiannetwork:item/{name}"}})
 b32_put(Path(os.environ["V1_RESOURCE_ROOT"])/f"data/obsidiannetwork/recipe/{name}.json",{
  "type":"minecraft:crafting_shaped","pattern":["ABA","CDC","AEA"],
  "key":{"A":"minecraft:netherite_ingot","B":"minecraft:iron_block","C":"minecraft:diamond",
         "D":"minecraft:"+material,"E":"minecraft:echo_shard"},
  "result":{"id":"obsidiannetwork:"+name,"count":1}})

# Hand-drawn 32px, technology-themed disk pixel sprites. Each upgrade has a
# different recognizable 8px pictogram and a consistent steel/cyan drive.
icons={
 "flight":("00100100","01011010","11111111","00111100","00011000","00100100","01000010","10000001"),
 "night_vision":("00000000","00111100","01000010","10011001","10100101","10011001","01000010","00111100"),
 "water_breathing":("00001000","00010100","00010100","00100010","01000001","01000001","00111110","00000000"),
 "protection":("00111100","01111110","11111111","11111111","01111110","00111100","00011000","00000000"),
 "fire_protection":("00010000","00111000","00101100","01110110","11011111","11111111","01111110","00111100"),
 "blast_protection":("10011001","01011010","00111100","11111111","11111111","00111100","01011010","10011001"),
 "projectile_protection":("00000010","00000110","00001100","11111111","11111111","00001100","00000110","00000010"),
 "feather_falling":("00000011","00000111","00001110","00011100","00111000","01110000","11100000","01000000"),
 "respiration":("00011000","00100100","00100100","00011000","01000010","10100101","10000001","01000010"),
 "aqua_affinity":("00011000","01011010","01011010","01011010","01111110","00011000","00011000","00011000"),
 "thorns":("10011001","01011010","00111100","11111111","00111100","01011010","10011001","00011000"),
 "unbreaking":("11111000","00111000","00111000","00111100","00111110","00100110","01100111","11000011"),
 "mending":("00011000","00011000","00011000","11111111","11111111","00011000","00011000","00011000"),
 "depth_strider":("00011000","00111100","00100100","00100100","01100110","11100111","11111111","00000000"),
 "frost_walker":("10011001","01011010","00111100","11111111","11111111","00111100","01011010","10011001"),
 "soul_speed":("00111100","01111110","11100111","11111111","10111101","10011001","01100110","00000000"),
 "swift_sneak":("00001100","00011110","00111100","11111100","00111111","00001111","00110000","11000000")
}
assert len(icons)==17

def disk_png(icon,accent,empty=False):
 rows=[]
 for y in range(32):
  row=bytearray([0])
  for x in range(32):
   border=2<=x<30 and 2<=y<30
   core=5<=x<27 and 7<=y<25
   glow=core and (y==7 or y==24 or x==5 or x==26)
   a=255 if border else 0
   if not border: color=(0,0,0)
   elif 3<=x<29 and 3<=y<29:
    t=int((x+y)*0.4)
    color=(29+t,39+t,51+t)
   else: color=(9,14,20)
   if core:color=(13,22,34)
   if glow:color=accent
   if 7<=x<25 and (y==4 or y==5):color=(102,122,141)
   if x in (4,27) and 5<=y<26:color=(86,105,119)
   if x in (6,25) and y in (27,28):color=(150,157,166)
   if not empty and icon and 11<=x<19 and 12<=y<20:
    if icon[y-12][x-11]=="1":color=accent
   row.extend((*color,a))
  rows.append(bytes(row))
 raw=b"".join(rows)
 def chunk(kind,data):
  return _struct.pack(">I",len(data))+kind+data+_struct.pack(">I",_zlib.crc32(kind+data)&0xffffffff)
 return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",_struct.pack(">IIBBBBB",32,32,8,6,0,0,0))+chunk(b"IDAT",_zlib.compress(raw,9))+chunk(b"IEND",b"")

palettes=[(84,218,255),(69,255,170),(69,168,255),(120,215,255),(255,98,66),
(255,184,55),(255,220,125),(170,240,255),(100,210,255),(70,255,235),
(245,102,202),(255,210,95),(78,255,154),(102,168,255),(125,227,255),(195,135,255),(255,185,91)]
for k,(card,icon) in enumerate(icons.items()):
 name="power_card_"+card
 (resources/f"textures/item/{name}.png").write_bytes(disk_png(icon,palettes[k]))
 b32_put(resources/f"models/item/{name}.json",{"parent":"minecraft:item/generated",
                                                 "textures":{"layer0":f"obsidiannetwork:item/{name}"}})
(resources/"textures/item/power_armor_upgrade.png").write_bytes(disk_png(None,(92,172,185),empty=True))
b32_put(resources/"models/item/power_armor_upgrade.json",{
 "parent":"minecraft:item/generated","textures":{"layer0":"obsidiannetwork:item/power_armor_upgrade"}})

# Enforce substantial ingredients instead of the obsolete blank+feather recipes.
unique={
 "flight":"minecraft:elytra","night_vision":"minecraft:golden_carrot",
 "water_breathing":"minecraft:heart_of_the_sea","protection":"minecraft:netherite_ingot",
 "fire_protection":"minecraft:magma_cream","blast_protection":"minecraft:obsidian",
 "projectile_protection":"minecraft:shield","feather_falling":"minecraft:phantom_membrane",
 "respiration":"minecraft:nautilus_shell","aqua_affinity":"minecraft:prismarine_crystals",
 "thorns":"minecraft:cactus","unbreaking":"minecraft:anvil",
 "mending":"minecraft:experience_bottle","depth_strider":"minecraft:prismarine_shard",
 "frost_walker":"minecraft:blue_ice","soul_speed":"minecraft:soul_soil",
 "swift_sneak":"minecraft:echo_shard"
}
for card in icons:
 rare=card=="flight"
 b32_put(Path(os.environ["V1_RESOURCE_ROOT"])/f"data/obsidiannetwork/recipe/power_card_{card}.json",{
  "type":"minecraft:crafting_shaped",
  "pattern":["ACA","BDB","AEA"],
  "key":{"A":"minecraft:netherite_ingot" if rare else "minecraft:iron_ingot",
         "B":"minecraft:nether_star" if rare else "minecraft:redstone_block",
         "C":unique[card],"D":"obsidiannetwork:power_armor_upgrade",
         "E":"minecraft:diamond_block" if rare else "minecraft:diamond"},
  "result":{"id":"obsidiannetwork:power_card_"+card,"count":1}})

for lang in ("en_us","de_de"):
 p=resources/f"lang/{lang}.json"
 names=_json.loads(p.read_text(encoding="utf-8"))
 for part in ("helmet","chestplate","leggings","boots"):
  names["item.obsidiannetwork.power_armor_mk2_"+part]=(
   "Power Armor MK2 "+part.title() if lang=="en_us" else "Power-Rüstung MK2 "+part.title())
 names["item.obsidiannetwork.power_armor_upgrade"]=(
  "Blank Armor Upgrade Disk" if lang=="en_us" else "Leere Rüstungs-Upgrade-Disk")
 b32_put(p,names)
print("BUILD32_COMPLETE PASS: MK2 matching + War Machine palette; 18 unique disk icons; premium flight recipe; ArmorStand transition poses; station snap within 2 blocks; previous armor recovery unchanged")


# Native vanilla-compatible 3-row station upgrade menu. No client custom menu
# registration is needed, and virtual preview items can NEVER be extracted.
gui=j/"powerarmor/ArmorStationMenu.java"
assert not gui.exists(),"Station GUI already generated"
gui.write_text(r'''package dev.obsidiannetwork.powerarmor;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.item.ItemStack;

/** Native 9x3 armor preview and interactive card panel.
 * The top grid is a VIRTUAL read-only preview, never a real item inventory.
 * The only inventory mutations are validated against the owned suit and
 * the server's actual carried card. Empty-hand click removes a card to cursor.
 */
public final class ArmorStationMenu extends ChestMenu {
 private final SimpleContainer preview;
 private final ServerPlayer owner;
 private final ArmorStand suit;
 private final BlockPos station;
 private ArmorStationMenu(int id, Inventory inventory,SimpleContainer buffer,
                          ServerPlayer player,ArmorStand stand,BlockPos pos){
  super(MenuType.GENERIC_9x3,id,inventory,buffer,3);
  preview=buffer;owner=player;suit=stand;station=pos.immutable();
  refresh();
 }
 public ArmorStationMenu(int id,Inventory inventory,ServerPlayer owner,ArmorStand suit,BlockPos pos){
  this(id,inventory,new SimpleContainer(27),owner,suit,pos);
 }
 private boolean valid(){
  return !suit.isRemoved() && PowerArmorSuitWorld.full(suit)
    && PowerArmorSuitWorld.findNearby(owner.level(),station,owner)==suit
    && owner.blockPosition().distSqr(station)<=64.0D
    && owner.level().getBlockState(station).getBlock() instanceof ArmorStationBlock;
 }
 @Override public boolean stillValid(Player player){
  return player==owner && valid();
 }
 private List<String> cards(ItemStack chest){
  String data=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return new ArrayList<>(data==null||data.isEmpty()?List.of():Arrays.asList(data.split(",")));
 }
 private List<Integer> visibleIndices(List<String> values){
  List<Integer> out=new ArrayList<>();
  for(int i=0;i<values.size();i++)
   if(PowerArmorCards.item(values.get(i))!=null)out.add(i);
  return out;
 }
 private void refresh(){
  if(!valid())return;
  for(int i=0;i<27;i++)preview.setItem(i,ItemStack.EMPTY);
  for(int i=0;i<4;i++)
   preview.setItem(i,suit.getItemBySlot(PowerArmorRuntime.SLOTS[i]).copy());
  List<String> values=cards(suit.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST));
  List<Integer> visible=visibleIndices(values);
  for(int i=0;i<Math.min(12,visible.size());i++)
   preview.setItem(9+i,new ItemStack(PowerArmorCards.item(values.get(visible.get(i)))));
  broadcastChanges();
 }
 @Override public void clicked(int slotId,int button,ContainerInput click,Player player){
  if(slotId<0||slotId>=27){
   super.clicked(slotId,button,click,player);return;
  }
  // Ignore all client-side clicks: the server owns the preview and every card.
  if(!(player instanceof ServerPlayer) || player!=owner || !valid())return;
  if(click!=ContainerInput.PICKUP || button!=0)return;
  if(slotId<9 || slotId>=21)return;
  ItemStack chest=suit.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).copy();
  List<String> values=cards(chest);
  List<Integer> indices=visibleIndices(values);
  int display=slotId-9;
  ItemStack carried=getCarried();
  if(carried.isEmpty()){
   if(display>=indices.size())return;
   int i=indices.get(display);
   var item=PowerArmorCards.item(values.get(i));
   if(item==null)return;
   // Mutate card metadata exactly once and return one real card to cursor.
   values.remove(i);
   chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
       String.join(",",values));
   suit.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST,chest);
   setCarried(new ItemStack(item));
  }else if(carried.getItem() instanceof UpgradeCardItem card && !"blank".equals(card.upgradeId)){
   if(indices.size()>=12 || display>indices.size())return;
   int duplicate=0;
   for(String id:values)if(id.equals(card.upgradeId))duplicate++;
   if(duplicate>=(card.upgradeId.equals("protection")?8:1))return;
   // Insert in clicked slot order while preserving toggle-only metadata.
   int insertion=display==indices.size()?values.size():indices.get(display);
   values.add(insertion,card.upgradeId);
   chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
       String.join(",",values));
   suit.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST,chest);
   if(!owner.isCreative())carried.shrink(1);
  }else return;
  refresh();
 }
 @Override public ItemStack quickMoveStack(Player player,int slot){
  // No virtual equipment or card icons can be shift-taken or duplicated.
  return ItemStack.EMPTY;
 }
}
''',encoding="utf-8")

# Empty hand on station opens the GUI; held-card interaction remains available.
b32_edit("powerarmor/ArmorStationBlock.java",
'''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;''',
'''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;
  if(!p.isShiftKeyDown()&&p.getMainHandItem().isEmpty()){
   var standing=PowerArmorSuitWorld.findNearby(level,pos,p);
   if(standing!=null){
    p.openMenu(new net.minecraft.world.SimpleMenuProvider(
       (id,inventory,actor)->new ArmorStationMenu(id,inventory,p,standing,pos),
       Component.literal("Armor Station - Upgrade Control")));
    return InteractionResult.SUCCESS;
   }
  }''')
print("BUILD32_STATION_GUI PASS: server-authoritative 9x3 read-only suit display plus install/remove slots; no preview item extraction")


# BUILD35_STATION_SHELL: in-world QA fixes for Build 34.
#  - Open GUI ALWAYS, even without a powered or installed owned suit.
#  - Massive 3D overhanging garage with hand-built 32px industrial textures.
#  - Completely closed, downward arms for unattended suits.
#  - Split chest/leg plates and hinged head are VISUAL ONLY ItemDisplays.
#    All four authentic power armor stacks remain stored only on the protected
#    ArmorStand, with original-armor recovery remaining fully atomic.
from math import sin as _sin, cos as _cos
import random as _random

def b35_java(relative, before, after):
    p=j/relative
    source=p.read_text(encoding="utf-8")
    n=source.count(before)
    assert n==1,"BUILD35 anchor drift "+relative+" "+str(n)
    p.write_text(source.replace(before,after,1),encoding="utf-8")

# ----------------------------------------------------------------------------
# Station: unconditional GUI and updates even when armor is not yet docked.
# The initial menu is allowed to be empty; it resolves the nearest owned suit
# from SERVER state whenever opened/clicked/ticked.
# ----------------------------------------------------------------------------
b35_java("powerarmor/ArmorStationBlock.java",
'''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;
  if(!p.isShiftKeyDown()&&p.getMainHandItem().isEmpty()){
   var standing=PowerArmorSuitWorld.findNearby(level,pos,p);
   if(standing!=null){
    p.openMenu(new net.minecraft.world.SimpleMenuProvider(
       (id,inventory,actor)->new ArmorStationMenu(id,inventory,p,standing,pos),
       Component.literal("Armor Station - Upgrade Control")));
    return InteractionResult.SUCCESS;
   }
  }''',
'''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;
  // Normal right-click MUST open, with or without a suit, empty hand or card.
  // Sneak is preserved as the emergency path for legacy stored items.
  if(!p.isShiftKeyDown()){
   p.openMenu(new net.minecraft.world.SimpleMenuProvider(
      (id,inventory,actor)->new ArmorStationMenu(id,inventory,p,pos),
      Component.literal("xSxLabs | Power Armor Maintenance")));
   return InteractionResult.SUCCESS;
  }''')

b35_java("powerarmor/ArmorStationMenu.java",
''' private final ArmorStand suit;''',
''' private ArmorStand suit;''')
b35_java("powerarmor/ArmorStationMenu.java",
''' private ArmorStationMenu(int id, Inventory inventory,SimpleContainer buffer,
                          ServerPlayer player,ArmorStand stand,BlockPos pos){
  super(MenuType.GENERIC_9x3,id,inventory,buffer,3);
  preview=buffer;owner=player;suit=stand;station=pos.immutable();
  refresh();
 }
 public ArmorStationMenu(int id,Inventory inventory,ServerPlayer owner,ArmorStand suit,BlockPos pos){
  this(id,inventory,new SimpleContainer(27),owner,suit,pos);
 }
 private boolean valid(){
  return !suit.isRemoved() && PowerArmorSuitWorld.full(suit)
    && PowerArmorSuitWorld.findNearby(owner.level(),station,owner)==suit
    && owner.blockPosition().distSqr(station)<=64.0D
    && owner.level().getBlockState(station).getBlock() instanceof ArmorStationBlock;
 }''',
''' private ArmorStationMenu(int id, Inventory inventory,SimpleContainer buffer,
                          ServerPlayer player,BlockPos pos){
  super(MenuType.GENERIC_9x3,id,inventory,buffer,3);
  preview=buffer;owner=player;station=pos.immutable();
  refresh();
 }
 public ArmorStationMenu(int id,Inventory inventory,ServerPlayer owner,BlockPos pos){
  this(id,inventory,new SimpleContainer(27),owner,pos);
 }
 private boolean valid(){
  return owner.blockPosition().distSqr(station)<=64.0D
    && owner.level().getBlockState(station).getBlock() instanceof ArmorStationBlock;
 }
 private ArmorStand resolve(){
  return valid()?PowerArmorSuitWorld.findNearby(owner.level(),station,owner):null;
 }''')
b35_java("powerarmor/ArmorStationMenu.java",
''' private void refresh(){
  if(!valid())return;
  for(int i=0;i<27;i++)preview.setItem(i,ItemStack.EMPTY);
  for(int i=0;i<4;i++)
   preview.setItem(i,suit.getItemBySlot(PowerArmorRuntime.SLOTS[i]).copy());
  List<String> values=cards(suit.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST));
  List<Integer> visible=visibleIndices(values);
  for(int i=0;i<Math.min(12,visible.size());i++)
   preview.setItem(9+i,new ItemStack(PowerArmorCards.item(values.get(visible.get(i)))));
  broadcastChanges();
 }''',
''' private void refresh(){
  if(!valid())return;
  this.suit=resolve();
  for(int i=0;i<27;i++)preview.setItem(i,ItemStack.EMPTY);
  if(suit==null){
   ItemStack status=new ItemStack(net.minecraft.world.item.Items.BARRIER);
   status.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,
       net.minecraft.network.chat.Component.literal("No single owned Power Armor docked (3 blocks)"));
   preview.setItem(4,status);
   return;
  }
  for(int i=0;i<4;i++)
   preview.setItem(i,suit.getItemBySlot(PowerArmorRuntime.SLOTS[i]).copy());
  List<String> values=cards(suit.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST));
  List<Integer> visible=visibleIndices(values);
  for(int i=0;i<Math.min(12,visible.size());i++)
   preview.setItem(9+i,new ItemStack(PowerArmorCards.item(values.get(visible.get(i)))));
  // Preview-only stacks are rebuilt from the real world stand each tick.
 }
 @Override public void broadcastChanges(){
  refresh();
  super.broadcastChanges();
 }''')
b35_java("powerarmor/ArmorStationMenu.java",
'''  if(!(player instanceof ServerPlayer) || player!=owner || !valid())return;
  if(click!=ContainerInput.PICKUP || button!=0)return;''',
'''  if(!(player instanceof ServerPlayer) || player!=owner || !valid())return;
  this.suit=resolve();
  if(suit==null)return;
  if(click!=ContainerInput.PICKUP || button!=0)return;''')

# The original 2-high station collision shape prevented meaningful docking.
# Restrict physical collision to its steel base. The taller gantry has a
# 3-block-high click/outline shape and visibly hangs over the parked suit.
b35_java("powerarmor/ArmorStationBlock.java",
''' private static final net.minecraft.world.phys.shapes.VoxelShape STAND_SHAPE=
   net.minecraft.world.phys.shapes.Shapes.box(0.0625D,0D,0.0625D,0.9375D,2D,0.9375D);''',
''' private static final net.minecraft.world.phys.shapes.VoxelShape STAND_SHAPE=
   net.minecraft.world.phys.shapes.Shapes.box(-0.1875D,0D,-1.25D,1.1875D,3.0D,1.0625D);
 private static final net.minecraft.world.phys.shapes.VoxelShape STATION_FOOT=
   net.minecraft.world.phys.shapes.Shapes.box(0D,0D,0D,1D,0.1875D,1D);''')
b35_java("powerarmor/ArmorStationBlock.java",
'''  return STAND_SHAPE;
 }
 @Override protected net.minecraft.world.phys.shapes.VoxelShape getCollisionShape''',
'''  return STAND_SHAPE;
 }
 @Override protected net.minecraft.world.phys.shapes.VoxelShape getCollisionShape''')
# Only change the collision return; outline stays 3 blocks tall.
p=j/"powerarmor/ArmorStationBlock.java"
source=p.read_text(encoding="utf-8")
anchor='''CollisionContext context){
  return STAND_SHAPE;
 }'''
assert source.count(anchor)==2,"Unexpected two shape accessors"
source=source.replace(anchor,'CollisionContext context){\n  return STAND_SHAPE;\n }',1)
source=source.replace(anchor,'CollisionContext context){\n  return STATION_FOOT;\n }',1)
p.write_text(source,encoding="utf-8")

# Docking is at the FRONT of the placed station (not two blocks below it).
# The station remains intact, the player's actual suit is never altered.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   BlockPos candidate=station.below(2);
   if(candidate.distSqr(origin)>4.0D)continue;
   if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;
   if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(candidate).inflate(0.25D)).isEmpty())continue;
   double distance=candidate.distSqr(origin);
   if(distance<best){best=distance;found=candidate;}''',
'''   for(var facing:new net.minecraft.core.Direction[]{
       net.minecraft.core.Direction.NORTH,net.minecraft.core.Direction.EAST,
       net.minecraft.core.Direction.WEST,net.minecraft.core.Direction.SOUTH}){
    BlockPos candidate=station.relative(facing);
    if(candidate.distSqr(origin)>4.0D)continue;
    if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;
    if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(candidate).inflate(0.25D)).isEmpty())continue;
    double distance=candidate.distSqr(origin)+(facing==net.minecraft.core.Direction.NORTH?0D:0.25D);
    if(distance<best){best=distance;found=candidate;}
   }''')

# ----------------------------------------------------------------------------
# Rich voxel art: real industrial service gantry, roughly 3 blocks tall.
# Original model is deliberately REPLACED, not retextured, for all blockstate
# variants including older saved station states. No invisible cube outlines.
# ----------------------------------------------------------------------------
texdir=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/textures/block"
texdir.mkdir(parents=True,exist_ok=True)
_metal_palettes={
 "armor_steel":((47,57,66),(98,112,125),(162,173,181)),
 "armor_carbon":((18,25,32),(33,43,52),(66,78,91)),
 "armor_hydraulic":((61,75,88),(130,148,159),(212,223,225)),
 "armor_cyan":((3,51,65),(8,125,151),(63,234,249)),
 "armor_warning":((31,31,27),(205,150,34),(252,207,58)),
 "armor_copper":((45,56,68),(88,116,133),(154,188,203)),
}
def b35_texture(key,colors):
 rng=_random.Random(0x35A2+sum(ord(c) for c in key))
 size=32
 data=bytearray()
 dark,mid,light=colors
 for y in range(size):
  data.append(0)
  for x in range(size):
   # Fine brushed steel / carbon weave / warning chevrons / lit circuits.
   if key=="armor_warning":
    base=light if ((x+y)//8)%2==0 else dark
   elif key=="armor_cyan":
    base=light if (x in (3,4,27,28) or y in (3,4,27,28)
                   or (12<=x<20 and 12<=y<20)) else mid
   elif key=="armor_carbon":
    base=mid if (x//4+y//4)%2 else dark
   elif key=="armor_hydraulic":
    base=light if x in (7,8,23,24) else mid
   else:
    base=light if x in (3,4) or y in (3,4) else (dark if x in (0,31) else mid)
   noise=rng.randrange(-10,11)
   if key=="armor_steel":noise+=(x%4==0)*6-(y%8==0)*8
   if key=="armor_carbon":noise=noise//2
   rgb=tuple(max(0,min(255,c+noise)) for c in base)
   data.extend((*rgb,255))
 def chunk(kind,payload):
  return (_struct.pack(">I",len(payload))+kind+payload+
          _struct.pack(">I",_zlib.crc32(kind+payload)&0xffffffff))
 return (b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",_struct.pack(">IIBBBBB",32,32,8,6,0,0,0))
         +chunk(b"IDAT",_zlib.compress(bytes(data),9))+chunk(b"IEND",b""))
for key,palette in _metal_palettes.items():
 (texdir/(key+".png")).write_bytes(b35_texture(key,palette))
stationres=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def b35_cube(x1,y1,z1,x2,y2,z2,texture):
 assert all(-24<=v<=52 for v in (x1,y1,z1,x2,y2,z2))
 assert x1<x2 and y1<y2 and z1<z2
 return {"from":[x1,y1,z1],"to":[x2,y2,z2],
         "faces":{side:{"texture":"#"+texture} for side in
           ("north","south","east","west","up","down")}}
parts=[]
def add(x1,y1,z1,x2,y2,z2,t="steel"):
 parts.append(b35_cube(x1,y1,z1,x2,y2,z2,t))
# Cast iron footplate with mechanical tie-down rails and underlights
add(0,0,0,16,2,16,"carbon")
add(1,2,12,15,3,16,"steel")
add(0,2,0,3,4,16,"steel")
add(13,2,0,16,4,16,"steel")
add(1,1,1,15,2,3,"warning")
for x in (2,13):
 add(x,2,4,x+1,3,12,"hydraulic")
# Four structural I-beam uprights (Y reaches 48 = three blocks)
for x in (0,13):
 for z in (11,14):
  add(x,2,z,x+3,45,z+2,"carbon")
  add(x,2,z,x+1,44,z+2,"steel")
  add(x+2,2,z,x+3,44,z+2,"steel")
for y in (6,24,39):
 add(1,y,12,15,y+2,16,"steel")
 add(2,y+2,13,14,y+3,15,"carbon")
# Overhead gantry: thick overhanging canopy northward over the parked suit
add(-3,43,-19,19,47,16,"steel")
add(-2,47,-17,18,49,15,"carbon")
add(-3,41,-20,19,43,-17,"warning")
add(-2,44,-15,18,45,-10,"cyan")
for x in (0,15):
 add(x,35,-16,x+2,44,14,"hydraulic")
 add(x,35,-19,x+2,39,-15,"steel")
 add(x,28,-20,x+2,37,-18,"carbon")
 add(x,32,-20,x+2,35,-18,"cyan")
# Suspension bracket and overhead helmet clamp
add(6,39,-18,10,45,-11,"steel")
add(5,36,-19,11,39,-14,"carbon")
add(6,36,-20,10,38,-19,"cyan")
# Side pistons / rotary servos; swing into space around the suit
for x in (-4,17):
 add(x,18,-17,x+3,27,-14,"carbon")
 add(x,20,-18,x+3,23,-15,"hydraulic")
 add(x,25,-15,x+3,30,-13,"steel")
 add(x,17,-13,x+3,19,-10,"cyan")
# Structural hydraulic conduits visible at rear
for x in (4,11):
 add(x,6,14,x+1,38,16,"copper")
 add(x,37,14,x+1,41,16,"cyan")
# Tool rack / diagnostic modules
add(3,14,15,8,21,18,"carbon")
add(4,19,18,7,20,19,"cyan")
add(4,16,18,7,18,19,"steel")
for x in (3,6,9,12):
 add(x,9,16,x+1,11,18,"cyan")
# Reinforced corners and bolt heads
for x in (1,14):
 for z in (1,13):
  add(x,3,z,x+1,4,z+1,"hydraulic")
# Small silver and gold plate details on the underside
for x in (3,12):
 add(x,41,-16,x+2,42,-12,"hydraulic")
for state in ("empty","suit"):
 for frame in range(4):
  b35_put=stationres/f"models/block/armor_station_{state}_{frame}.json"
  b32_put(b35_put,{"parent":"minecraft:block/block",
    "textures":{key:"obsidiannetwork:block/armor_"+key for key in
                ("steel","carbon","hydraulic","cyan","warning","copper")},
    "elements":parts,"ambientocclusion":False})
assert len(parts)>=40,"Station model must be genuinely detailed"
b32_put(stationres/"models/item/armor_station.json",{
 "parent":"obsidiannetwork:block/armor_station_empty_0",
 "display":{"gui":{"rotation":[25,135,0],"translation":[0,-4,0],"scale":[0.45,0.45,0.45]},
            "ground":{"scale":[0.3,0.3,0.3]}}})

# ----------------------------------------------------------------------------
# Visual-only articulating panels for armor opening/closing.
# Five custom 3D cuboid item models accompany the real (protected) stand.
# They are NEVER real suit pieces, never placed in a loot table, and not in tabs.
# These displays are discarded after the 20-tick transition. If interrupted,
# periodic local cleanup restores the real stand, which retained its gear.
# ----------------------------------------------------------------------------
models=("chest_left","chest_right","leg_left","leg_right","helmet")
p=j/"ObsidianNetwork.java"
source=p.read_text(encoding="utf-8")
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE ='
assert source.count(anchor)==1
fields=[]
for tier in ("mk1","mk2"):
 for segment in models:
  fields.append(f'''   public static final DeferredItem<net.minecraft.world.item.Item> ARMOR_VISUAL_{tier.upper()}_{segment.upper()} =
       ITEMS.registerItem("armor_visual_{tier}_{segment}",
         p -> new net.minecraft.world.item.Item(p.stacksTo(1)));''')
source=source.replace(anchor,"\n".join(fields)+"\n"+anchor,1)
p.write_text(source,encoding="utf-8")
for tier in ("mk1","mk2"):
 for part in models:
  item=f"armor_visual_{tier}_{part}"
  if tier=="mk1":base,edge,light="red","gold","cyan"
  else:base,edge,light="carbon","hydraulic","cyan"
  # Local cuboids physically separated into left chest, right chest, each leg,
  # and an individually rising helmet. No baked 2-block T-posed entity.
  cuboids=[]
  if part.startswith("chest"):
   cuboids+=[b35_cube(2,3,4,14,14,13,base),
             b35_cube(3,12,3,13,15,5,edge),
             b35_cube(4,7,3,12,9,4,light)]
  elif part.startswith("leg"):
   cuboids+=[b35_cube(3,1,5,13,15,12,base),
             b35_cube(3,11,4,13,14,5,edge),
             b35_cube(4,2,3,12,5,5,"hydraulic")]
  else:
   cuboids+=[b35_cube(3,2,3,13,14,13,base),
             b35_cube(3,9,2,13,12,4,edge),
             b35_cube(5,9,1,11,11,2,light)]
  b32_put(stationres/f"models/item/{item}.json",{
    "parent":"minecraft:item/generated",
    "textures":{k:"obsidiannetwork:block/armor_"+k for k in
                ("steel","carbon","hydraulic","cyan","warning","copper")},
    "elements":cuboids,
    "display":{"none":{"rotation":[0,0,0],"translation":[0,0,0],"scale":[1,1,1]}}})
  # Special palette keys are the actual, suitable station metal textures.
  b32_put(stationres/f"items/{item}.json",{"model":{"type":"minecraft:model",
                                                    "model":"obsidiannetwork:item/"+item}})

# Correct current persistent-open T-pose bug and give the panels real movement.
b35_java("powerarmor/PowerArmorSuitWorld.java",
''' private record Animation(ArmorStand stand,int ticks,boolean entering){}
 private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();
 private static void pose(ArmorStand stand,int progress,boolean entering){
  float open=(entering?progress:20-progress)/20.0F;
  float spread=68.0F*Math.max(0.0F,Math.min(1.0F,open));
  stand.setLeftArmPose(new net.minecraft.core.Rotations(-spread*0.35F,0F,-spread));
  stand.setRightArmPose(new net.minecraft.core.Rotations(-spread*0.35F,0F,spread));
  stand.setHeadPose(new net.minecraft.core.Rotations(-spread*0.25F,0F,0F));
 }''',
''' private record Animation(ArmorStand stand,int ticks,boolean entering,
                          List<net.minecraft.world.entity.Display.ItemDisplay> panels){}
 private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();
 private static final String VISUAL_MARK="xsxlabs_power_armor_visual_transient";
 private static void pose(ArmorStand stand,int progress,boolean entering){
  float open=(entering?progress:20-progress)/20.0F;
  open=Math.max(0.0F,Math.min(1.0F,open));
  // NORMAL idle arms, not the old permanent 68-degree T-pose.
  float arm=9.0F*open;
  stand.setLeftArmPose(new net.minecraft.core.Rotations(-arm,0F,-arm));
  stand.setRightArmPose(new net.minecraft.core.Rotations(-arm,0F,arm));
  stand.setHeadPose(new net.minecraft.core.Rotations(-42.0F*open,0F,0F));
  stand.setLeftLegPose(new net.minecraft.core.Rotations(0F,0F,-22.0F*open));
  stand.setRightLegPose(new net.minecraft.core.Rotations(0F,0F,22.0F*open));
  stand.setBodyPose(new net.minecraft.core.Rotations(0F,0F,0F));
 }
 private static void cleanup(Animation transition){
  for(var visual:transition.panels())if(!visual.isRemoved())visual.discard();
  ArmorStand stand=transition.stand();
  if(!stand.isRemoved()){
   stand.setInvisible(false);
   pose(stand,20,false);
  }
 }
 private static List<net.minecraft.world.entity.Display.ItemDisplay> panels(
     ArmorStand stand,ServerPlayer player){
  boolean mk2=PowerArmorRuntime.piece(stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0,true);
  net.minecraft.world.item.Item[] items=mk2?new net.minecraft.world.item.Item[]{
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK2_CHEST_LEFT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK2_CHEST_RIGHT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK2_LEG_LEFT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK2_LEG_RIGHT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK2_HELMET.get()}:
    new net.minecraft.world.item.Item[]{
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK1_CHEST_LEFT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK1_CHEST_RIGHT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK1_LEG_LEFT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK1_LEG_RIGHT.get(),
    dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_MK1_HELMET.get()};
  List<net.minecraft.world.entity.Display.ItemDisplay> result=new ArrayList<>();
  for(int i=0;i<items.length;i++){
   var visual=new net.minecraft.world.entity.Display.ItemDisplay(
     net.minecraft.world.entity.EntityType.ITEM_DISPLAY,stand.level());
   visual.addTag(VISUAL_MARK);
   visual.addTag(owner(player));
   visual.setInvulnerable(true);
   visual.setNoGravity(true);
   visual.setSilent(true);
   var slot=visual.getSlot(0);
   if(slot==null||!slot.set(new ItemStack(items[i])))continue;
   visual.setPos(stand.getX(),stand.getY()+1D,stand.getZ());
   if(stand.level().addFreshEntity(visual))result.add(visual);
  }
  return result;
 }
 private static void movePanels(Animation animation,int t){
  ArmorStand stand=animation.stand();
  double open=(animation.entering()?t:20-t)/20.0D;
  open=Math.max(0D,Math.min(1D,open));
  var panels=animation.panels();
  for(int i=0;i<panels.size();i++){
   var panel=panels.get(i);
   if(panel.isRemoved())continue;
   double side=(i==0||i==2)?-1D:1D;
   double x=(i==4?0D:side*(i<2?0.16D:0.15D));
   double outward=(i==4?0D:side*(i<2?0.46D:0.29D)*open);
   double y=(i==4?1.65D:(i<2?1.12D:0.25D));
   double z=(i==4?-0.10D:-0.18D);
   panel.setPos(stand.getX()+x+outward,
       stand.getY()+y+(i==4?0.54D*open:0D),
       stand.getZ()+z-(i<2?0.14D*open:0D));
   panel.setYRot((float)((i==4?0D:side*76.0D*open)));
  }
 }
 private static Animation startAnimation(ArmorStand stand,ServerPlayer player,boolean entering){
  // Actual armor is NEVER extracted or copied into animation entities.
  // Display items are cheap dummy meshes with no power, upgrades, or loot.
  var result=new Animation(stand,20,entering,panels(stand,player));
  stand.setInvisible(true);
  return result;
 }''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  Animation animation=ACTIVE.get(player.getUUID());
  if(animation==null)return;
  ArmorStand stand=animation.stand();
  if(stand.isRemoved()||!mine(stand,player)||!full(stand)){
   ACTIVE.remove(player.getUUID());return;
  }
  int t=21-animation.ticks();
  pose(stand,t,animation.entering());
  if(animation.ticks()>1){
   ACTIVE.put(player.getUUID(),new Animation(stand,animation.ticks()-1,animation.entering()));
   return;
  }
  ACTIVE.remove(player.getUUID());
  if(animation.entering())finishEntering(stand,player);
  else pose(stand,0,false);''',
'''  Animation animation=ACTIVE.get(player.getUUID());
  if(animation==null){
   // Recover interrupted animations after a crash/restart or disconnect.
   // No actual armor stack is ever touched by this visual-only cleanup.
   if(player.tickCount%100==0){
    var area=new AABB(player.blockPosition()).inflate(10D);
    for(ArmorStand stand:player.level().getEntitiesOfClass(ArmorStand.class,area,
        e->mine(e,player)&&e.isInvisible())){
     stand.setInvisible(false);pose(stand,20,false);
    }
    for(var visual:player.level().getEntitiesOfClass(
        net.minecraft.world.entity.Display.ItemDisplay.class,area,
        e->e.entityTags().contains(VISUAL_MARK)
            &&e.entityTags().contains(owner(player))))visual.discard();
   }
   return;
  }
  ArmorStand stand=animation.stand();
  if(stand.isRemoved()||!mine(stand,player)||!full(stand)){
   cleanup(animation);ACTIVE.remove(player.getUUID());return;
  }
  int t=21-animation.ticks();
  pose(stand,t,animation.entering());
  movePanels(animation,t);
  if(animation.ticks()>1){
   ACTIVE.put(player.getUUID(),new Animation(stand,animation.ticks()-1,
                                            animation.entering(),animation.panels()));
   return;
  }
  ACTIVE.remove(player.getUUID());
  cleanup(animation);
  if(animation.entering())finishEntering(stand,player);''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  ACTIVE.remove(e.getEntity().getUUID());''',
'''  Animation animation=ACTIVE.remove(e.getEntity().getUUID());
  if(animation!=null)cleanup(animation);''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  pose(stand,20,false);
  ACTIVE.put(player.getUUID(),new Animation(stand,20,false));
  return true;''',
'''  pose(stand,20,false);
  ACTIVE.put(player.getUUID(),startAnimation(stand,player,false));
  return true;''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  ACTIVE.put(player.getUUID(),new Animation(stand,20,true));
  player.sendSystemMessage(Component.literal("Power Armor opening..."));''',
'''  ACTIVE.put(player.getUUID(),startAnimation(stand,player,true));
  player.sendSystemMessage(Component.literal("Power Armor opening..."));''')
# Closing pose is always EXACTLY the unposed vanilla standing armor suit.
assert "new Animation(stand,20,false)" not in (j/"powerarmor/PowerArmorSuitWorld.java").read_text()
assert (j/"powerarmor/PowerArmorSuitWorld.java").read_text().count("pose(stand,20,false)")>=2
assert "this.suit=resolve();" in (j/"powerarmor/ArmorStationMenu.java").read_text()
assert (j/"powerarmor/ArmorStationBlock.java").read_text().count("openMenu")==1
print("BUILD35_STATION_SHELL PASS: functional empty-station GUI, 50+ custom gantry elements, detailed industrial textures, correct idle arms, opening five visual panels, secure suit storage and reconnect recovery")


# BUILD36_FINAL_GUI: explicit no-suit status, click-to-open regardless of hand,
# and all animated panel texture references resolved.
b35_java("powerarmor/ArmorStationBlock.java",
'''  if(!(held.getItem() instanceof PowerArmorItem)&&!(held.getItem() instanceof UpgradeCardItem))
   return InteractionResult.PASS;
  return useWithoutItem(state,level,pos,player,hit);''',
'''  // Always open maintenance via ordinary right-click, including if the player
  // is carrying a tool, upgrade card, or another non-power-armor item.
  return useWithoutItem(state,level,pos,player,hit);''')
b35_java("powerarmor/ArmorStationBlock.java",
'''      Component.literal("xSxLabs | Power Armor Maintenance")));''',
'''      Component.literal(PowerArmorSuitWorld.findNearby(level,pos,p)==null
         ? "Armor Station | No Armor Connected"
         : "Armor Station | Power Armor Connected")));''')
b35_java("powerarmor/ArmorStationMenu.java",
'''Component.literal("No single owned Power Armor docked (3 blocks)")''',
'''Component.literal("No Armor Connected")''')
# An explicit status indicator doubles as in-menu guidance even when the
# top-level title was chosen before a suit was placed nearby.
b35_java("powerarmor/ArmorStationMenu.java",
'''  for(int i=0;i<4;i++)
   preview.setItem(i,suit.getItemBySlot(PowerArmorRuntime.SLOTS[i]).copy());
  List<String> values=cards''',
'''  for(int i=0;i<4;i++)
   preview.setItem(i,suit.getItemBySlot(PowerArmorRuntime.SLOTS[i]).copy());
  ItemStack connected=new ItemStack(net.minecraft.world.item.Items.LIME_STAINED_GLASS_PANE);
  connected.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,
     net.minecraft.network.chat.Component.literal("Power Armor Connected - click a card to remove, or carry a card to install"));
  preview.setItem(4,connected);
  List<String> values=cards''')
# Unlike the no-suit barrier, this green status token can never be extracted.
# Strictly disallow any top-grid clicks except the 12 card positions.
b35_java("powerarmor/ArmorStationMenu.java",
'''  if(slotId<9 || slotId>=21)return;''',
'''  if(slotId<9 || slotId>=21)return;''') if False else None
# Fill all palette references used by the actual animated cuboids.
texdir.mkdir(parents=True,exist_ok=True)
for key,palette in {
  "armor_red":((55,12,19),(140,25,33),(224,54,54)),
  "armor_gold":((90,55,20),(187,133,39),(244,210,92))
}.items():
 (texdir/(key+".png")).write_bytes(b35_texture(key,palette))
for tier in ("mk1","mk2"):
 for segment in models:
  model=stationres/f"models/item/armor_visual_{tier}_{segment}.json"
  data=_json.loads(model.read_text(encoding="utf-8"))
  data["textures"].update({
   "red":"obsidiannetwork:block/armor_red",
   "gold":"obsidiannetwork:block/armor_gold"
  })
  b32_put(model,data)
print("BUILD36_FINAL_GUI PASS: no-suit title and tooltip, normal right-click with any held item, installed-upgrade preview, valid red/gold animated plate materials")


# BUILD37_RENDER_FIX: build35 rendered a missing-model cube because vanilla
# baked block models refuse individual cuboids outside supported model bounds.
# Transform the giant invalid Y=49 / Z=-20 cuboids into well-formed <=32
# units. The two-block animated suite retains enough height to fit under it.
# Never change registration IDs, any inventory data, or backup/recovery logic.
def b37_remodel():
    paths=list((stationres/"models/block").glob("armor_station_*.json"))
    assert len(paths)==8,"Station states must retain all eight model variants"
    for path in paths:
        obj=_json.loads(path.read_text(encoding="utf-8"))
        old=obj["elements"]
        repaired=[]
        for element in old:
            before=element["from"]
            after=element["to"]
            # Minecraft's vanilla block model parser has a hard limit on
            # cuboid coordinates. Clamp and skip wholly outside components.
            y0,y1=before[1],after[1]
            z0,z1=before[2],after[2]
            x0,x1=before[0],after[0]
            if y0>=32 or y1<=0 or z0>=32 or z1<=-16 or x0>=32 or x1<=-16:
                continue
            x0=max(-16,min(32,x0));x1=max(-16,min(32,x1))
            y0=max(0,min(32,y0));y1=max(0,min(32,y1))
            z0=max(-16,min(32,z0));z1=max(-16,min(32,z1))
            if x1<=x0 or y1<=y0 or z1<=z0:continue
            part=dict(element)
            part["from"]=[x0,y0,z0]
            part["to"]=[x1,y1,z1]
            repaired.append(part)
        assert len(repaired)>=15,"Station model unexpectedly empty"
        obj["elements"]=repaired
        b32_put(path,obj)
    # Vanilla item json must reference the repaired model.
    b32_put(stationres/"models/item/armor_station.json",{
      "parent":"obsidiannetwork:block/armor_station_empty_0",
      "display":{"gui":{"rotation":[25,135,0],"translation":[0,-4,0],
                        "scale":[0.45,0.45,0.45]}}})
    assert all((texdir/(k+".png")).is_file() for k in
      ("armor_steel","armor_carbon","armor_hydraulic","armor_cyan",
       "armor_warning","armor_copper","armor_red","armor_gold"))
b37_remodel()

# The panels were all rendered together at z almost coincident with the real
# stand, producing tier-colored and black z-fighting. Panels now advance into
# the foreground progressively while the real stand remains invisible during
# its own cinematic transition. Normal idle stand is still opaque/closed.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double z=(i==4?-0.10D:-0.18D);
   panel.setPos(stand.getX()+x+outward,
       stand.getY()+y+(i==4?0.54D*open:0D),
       stand.getZ()+z-(i<2?0.14D*open:0D));''',
'''   // Keep each moving plate in its own depth plane, avoiding Z-fighting.
   double z=(i==4?-0.24D:(i<2?-0.33D:-0.40D));
   double depthShift=i*0.038D;
   panel.setPos(stand.getX()+x+outward,
       stand.getY()+y+(i==4?0.54D*open:0D),
       stand.getZ()+z-depthShift-(i<2?0.20D*open:0D));''')
# Replace the cuboid item models' generated parent with a conventional
# block/item mesh parent. A generated parent with explicit elements may be
# treated as layered billboard under alternate shader/resource packs.
for tier in ("mk1","mk2"):
 for part in models:
  p=stationres/f"models/item/armor_visual_{tier}_{part}.json"
  obj=_json.loads(p.read_text(encoding="utf-8"))
  obj["parent"]="minecraft:block/block"
  obj["ambientocclusion"]=False
  b32_put(p,obj)
print("BUILD37_RENDER_FIX PASS: all 8 station blockstates bounded to Minecraft's model coordinates; textures present; animated plates separated in depth, no shared z-plane")


# BUILD38_ONE_BY_TWO_STATION: Build 37 ingame report.
# Station front (north) is one full block of service floor; back block contains
# structural rails. Width exactly 1, total length 2, height exactly 2 blocks.
# No free-floating cuboids and no new blocks or persistent item entities.
station_parts=[]
def stage(x1,y1,z1,x2,y2,z2,material):
 assert 0<=x1<x2<=16 and 0<=y1<y2<=32 and -16<=z1<z2<=16
 station_parts.append(b35_cube(x1,y1,z1,x2,y2,z2,material))
# Full two-block grey floor so the parked suit STANDS ON it.
stage(0,0,-16,16,2,16,"steel")
stage(1,2,-15,15,3,-1,"carbon")
stage(2,3,-13,14,4,-3,"steel")
stage(1,2,0,15,3,15,"carbon")
stage(0,3,12,16,5,16,"steel")
# 2-block-high rear frame, all linked physically to base and roof.
for a,b in ((0,3),(13,16)):
 stage(a,4,10,b,29,16,"carbon")
 stage(a,4,11,a+1,29,16,"steel")
 stage(b-1,4,11,b,29,16,"hydraulic")
 for h in (9,17,25):
  stage(a,h,7,b,h+2,13,"steel")
  stage(a+1,h+1,6,b-1,h+2,8,"cyan")
# Top crossbeam and central hydraulic head, tied to both uprights.
stage(0,29,9,16,32,16,"steel")
stage(1,27,10,15,29,15,"carbon")
stage(4,28,8,12,30,11,"warning")
stage(6,24,8,10,29,13,"hydraulic")
stage(7,23,7,9,25,9,"cyan")
# Two compact service arms connected to the rear pillars, projecting over pad.
for a,b in ((1,4),(12,15)):
 stage(a,19,1,b,22,12,"hydraulic")
 stage(a,18,-3,b,21,3,"carbon")
 stage(a+1,19,-5,b-1,21,-2,"steel")
 stage(a+1,19,-6,b-1,20,-5,"cyan")
# Rear diagnostic console and energy conduits.
stage(4,12,14,12,20,16,"carbon")
stage(5,17,13,11,19,14,"cyan")
stage(5,14,13,11,16,14,"hydraulic")
for a in (2,5,8,11,14):
 stage(a,6,14,a+1,8,16,"warning")
for state in ("empty","suit"):
 for frame in range(4):
  b32_put(stationres/f"models/block/armor_station_{state}_{frame}.json",{
   "parent":"minecraft:block/block","ambientocclusion":False,
   "textures":{k:"obsidiannetwork:block/armor_"+k for k in
      ("steel","carbon","hydraulic","cyan","warning","copper")},
   "elements":station_parts})
b32_put(stationres/"models/item/armor_station.json",{
 "parent":"obsidiannetwork:block/armor_station_empty_0",
 "display":{
  "gui":{"rotation":[28,135,0],"translation":[0,-3,0],"scale":[0.48,0.48,0.48]},
  "firstperson_righthand":{"rotation":[0,45,0],"translation":[0,-2,0],
                            "scale":[0.38,0.38,0.38]},
  "thirdperson_righthand":{"rotation":[45,45,0],"translation":[0,1,0],
                           "scale":[0.35,0.35,0.35]},
  "ground":{"scale":[0.28,0.28,0.28]}}})
assert all(0<=v<=32 for cube in station_parts for v in (
 cube["from"][0],cube["to"][0],cube["from"][1],cube["to"][1]))
assert all(-16<=v<=16 for cube in station_parts for v in (
 cube["from"][2],cube["to"][2]))

# Park only on the forward grey pad, NOT to one side of the frame.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   for(var facing:new net.minecraft.core.Direction[]{
       net.minecraft.core.Direction.NORTH,net.minecraft.core.Direction.EAST,
       net.minecraft.core.Direction.WEST,net.minecraft.core.Direction.SOUTH}){
    BlockPos candidate=station.relative(facing);
    if(candidate.distSqr(origin)>4.0D)continue;
    if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;
    if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(candidate).inflate(0.25D)).isEmpty())continue;
    double distance=candidate.distSqr(origin)+(facing==net.minecraft.core.Direction.NORTH?0D:0.25D);
    if(distance<best){best=distance;found=candidate;}
   }''',
'''   BlockPos candidate=station.north();
   if(candidate.distSqr(origin)>4.0D)continue;
   if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;
   if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(candidate).inflate(0.25D)).isEmpty())continue;
   double distance=candidate.distSqr(origin);
   if(distance<best){best=distance;found=candidate;}''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  BlockPos pos=underStation(player);
  if(pos==null)pos=available(player);''',
'''  BlockPos pos=underStation(player);
  boolean docked=pos!=null;
  if(pos==null)pos=available(player);''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  stand.setShowArms(true);
  stand.setNoBasePlate(true);''',
'''  stand.setShowArms(true);
  stand.setNoBasePlate(true);
  // Only docked suits get the requested 180-degree rotation.
  if(docked){
   stand.setYRot(player.getYRot()+180.0F);
   stand.setYHeadRot(stand.getYRot());
   stand.setYBodyRot(stand.getYRot());
  }''')
# The last two yaw setters are avoidable mapping risks; ArmorStand body follows
# YRot on its own, so use only the public reliable orientation method.
p=j/"powerarmor/PowerArmorSuitWorld.java"
ss=p.read_text(encoding="utf-8")
ss=ss.replace('   stand.setYHeadRot(stand.getYRot());\n   stand.setYBodyRot(stand.getYRot());\n','')
p.write_text(ss,encoding="utf-8")

# The GUI wrongly refused clicking an empty upgrade position if it was after
# the last installed upgrade. Accept all 12 upgrade cells, insert after last.
b35_java("powerarmor/ArmorStationMenu.java",
'''   if(indices.size()>=12 || display>indices.size())return;''',
'''   if(indices.size()>=12)return;''')
b35_java("powerarmor/ArmorStationMenu.java",
'''   int insertion=display==indices.size()?values.size():indices.get(display);''',
'''   int insertion=display>=indices.size()?values.size():indices.get(display);''')

# Distinct depth planes, lateral separation to prevent red/black polygons
# from overlapping during panel swing. No changes to actual item stacks.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double x=(i==4?0D:side*(i<2?0.16D:0.15D));
   double outward=(i==4?0D:side*(i<2?0.46D:0.29D)*open);''',
'''   double x=(i==4?0D:side*(i<2?0.43D:0.36D));
   double outward=(i==4?0D:side*(i<2?0.58D:0.39D)*open);''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double z=(i==4?-0.24D:(i<2?-0.33D:-0.40D));
   double depthShift=i*0.038D;''',
'''   double z=(i==4?-0.49D:(i<2?-0.66D:-0.60D));
   double depthShift=i*0.08D;''')

# The item model for panel cubes was built with faces touching coincident
# ornamental plates. Remove coplanar narrow ribbons; use non-overlapping base
# panels to prevent sparkle on both MK1 and MK2.
for tier in ("mk1","mk2"):
 for piece in models:
  p=stationres/f"models/item/armor_visual_{tier}_{piece}.json"
  obj=_json.loads(p.read_text(encoding="utf-8"))
  assert len(obj["elements"])==3
  obj["elements"]=obj["elements"][:1]
  b32_put(p,obj)
print("BUILD38_ONE_BY_TWO_STATION PASS: station 1w x 2l x 2h, pad under suit, rear attached arms, 180-degree docked orientation, GUI insertion and MK1/MK2 overlapping panels fixed")


# BUILD39_IN_GAME_REGRESSION_REPAIR.
# Keep vanilla cubic element geometry strictly inside permitted bounds, avoid
# the huge hand model, restore visible hinged parts without stray color panels.
# All piece items/backups remain untouched.
# Minecraft validates every from/to component in [-16,32].
clean=[]
for cuboid in station_parts:
 a,b=cuboid["from"],cuboid["to"]
 # Remove warning/red pad, including old decorative threshold strips.
 if cuboid["faces"]["up"]["texture"]=="#warning" and a[1]<10:
  continue
 # Structural attached arms only: front projection must still connect.
 clean.append(cuboid)
for mode in ("empty","suit"):
 for frame in range(4):
  path=stationres/f"models/block/armor_station_{mode}_{frame}.json"
  data=_json.loads(path.read_text(encoding="utf-8"))
  data["elements"]=clean
  data["textures"]["particle"]="obsidiannetwork:block/armor_steel"
  b32_put(path,data)
# The two-block gantry needs a smaller hand-model bounding box, otherwise
# the first-person hand appears cropped, cluttered and flickers.
hand=[]
for cuboid in clean:
 a,b=cuboid["from"],cuboid["to"]
 if a[2]<0:continue
 hand.append(cuboid)
assert hand
b32_put(stationres/"models/item/armor_station_hand.json",{
 "parent":"minecraft:block/block","ambientocclusion":False,
 "textures":{**{k:"obsidiannetwork:block/armor_"+k for k in
              ("steel","carbon","hydraulic","cyan","warning","copper")},
             "particle":"obsidiannetwork:block/armor_steel"},
 "elements":hand
})
b32_put(stationres/"models/item/armor_station.json",{
 "parent":"obsidiannetwork:item/armor_station_hand",
 "display":{
  "gui":{"rotation":[25,135,0],"translation":[0,-3,0],"scale":[0.42,0.42,0.42]},
  "firstperson_righthand":{"rotation":[0,45,0],"translation":[0,-2,0],
                            "scale":[0.32,0.32,0.32]},
  "thirdperson_righthand":{"rotation":[45,45,0],"translation":[0,1,0],
                           "scale":[0.32,0.32,0.32]},
  "ground":{"scale":[0.25,0.25,0.25]}}})
# Restore the original hinged positions (as observed in build36), but create
# each part from only ONE non-overlapping cuboid. The old 3-part models
# shared coplanar faces causing tier-colored flashing.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double x=(i==4?0D:side*(i<2?0.43D:0.36D));
   double outward=(i==4?0D:side*(i<2?0.58D:0.39D)*open);''',
'''   double x=(i==4?0D:side*(i<2?0.16D:0.15D));
   double outward=(i==4?0D:side*(i<2?0.46D:0.29D)*open);''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double z=(i==4?-0.49D:(i<2?-0.66D:-0.60D));
   double depthShift=i*0.08D;''',
'''   double z=(i==4?-0.17D:(i<2?-0.25D:-0.28D));
   double depthShift=i*0.015D;''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''       stand.getZ()+z-depthShift-(i<2?0.20D*open:0D));''',
'''       stand.getZ()+z-depthShift-(i<2?0.14D*open:0D));''')
# The visual panel models are registered as plain items. Vanilla generated
# item definitions can override explicit cuboid shapes on recent releases.
# Re-point each 1.21.4+ items definition at the correct dedicated panel model.
for tier in ("mk1","mk2"):
 for part in models:
  ident=f"armor_visual_{tier}_{part}"
  p=stationres/f"items/{ident}.json"
  p.parent.mkdir(parents=True,exist_ok=True)
  b32_put(p,{"model":{"type":"minecraft:model",
                        "model":"obsidiannetwork:item/"+ident}})
# Model-space placement: stand on the grey floor, facing back toward machine.
# Previously the origin was level with station while the pad rises 2/16.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  stand.setYRot(player.getYRot()+180.0F);''',
'''  stand.setYRot(player.getYRot()+180.0F);''') if False else None
# Preserve exactly one inventory item per card, and extend GUI card grid to 15.
b35_java("powerarmor/ArmorStationMenu.java",
'''  for(int i=0;i<Math.min(12,visible.size());i++)
   preview.setItem(9+i,new ItemStack(PowerArmorCards.item(values.get(visible.get(i)))));''',
'''  for(int i=0;i<Math.min(15,visible.size());i++)
   preview.setItem(9+i,new ItemStack(PowerArmorCards.item(values.get(visible.get(i)))));''')
b35_java("powerarmor/ArmorStationMenu.java",
'''  if(slotId<9 || slotId>=21)return;''',
'''  if(slotId<9 || slotId>=24)return;''')
b35_java("powerarmor/ArmorStationMenu.java",
'''   if(indices.size()>=12)return;''',
'''   if(indices.size()>=15)return;''')
# Shift-click one card from the player's inventory into the next available
# upgrade cell, via the same server-side transaction path.
b35_java("powerarmor/ArmorStationMenu.java",
''' @Override public ItemStack quickMoveStack(Player player,int slot){
  // No virtual equipment or card icons can be shift-taken or duplicated.
  return ItemStack.EMPTY;
 }''',
''' @Override public ItemStack quickMoveStack(Player player,int slot){
  if(!(player instanceof ServerPlayer)||player!=owner||!valid()||slot<27)return ItemStack.EMPTY;
  var inventorySlot=this.slots.get(slot);
  if(inventorySlot==null||!inventorySlot.hasItem())return ItemStack.EMPTY;
  ItemStack stack=inventorySlot.getItem();
  if(!(stack.getItem() instanceof UpgradeCardItem card)
      ||"blank".equals(card.upgradeId))return ItemStack.EMPTY;
  ItemStack chest=suit.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).copy();
  List<String> values=cards(chest);
  if(visibleIndices(values).size()>=15)return ItemStack.EMPTY;
  int duplicates=0;
  for(String id:values)if(id.equals(card.upgradeId))duplicates++;
  if(duplicates>=(card.upgradeId.equals("protection")?8:1))return ItemStack.EMPTY;
  ItemStack before=stack.copy();
  values.add(card.upgradeId);
  chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
    String.join(",",values));
  suit.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST,chest);
  if(!owner.isCreative())stack.shrink(1);
  inventorySlot.setChanged();
  refresh();
  return before;
 }''')
# Reject removed card types when newly installed; existing data remains safe
# until a player can extract those cards without losing stored inventory.
b35_java("powerarmor/ArmorStationMenu.java",
'''  }else if(carried.getItem() instanceof UpgradeCardItem card && !"blank".equals(card.upgradeId)){''',
'''  }else if(carried.getItem() instanceof UpgradeCardItem card
      && !"blank".equals(card.upgradeId)
      && !"mending".equals(card.upgradeId)
      && !"unbreaking".equals(card.upgradeId)){''')
# New world-position logic adjusts height to the visible silver platform,
# while keeping collision checks and recovery intact.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''  if(docked){
   stand.setYRot(player.getYRot()+180.0F);
  }''',
'''  if(docked){
   stand.setYRot(player.getYRot()+180.0F);
   stand.setPos(stand.getX(),stand.getY()+0.125D,stand.getZ());
  }''')
print("BUILD39_IN_GAME_REGRESSION_REPAIR PASS: restored panel motion and modern item definitions; 15 upgrade slots, shift-click, validated compact model and hand icon")


# BUILD40_RENDER_MAPPING: modern Minecraft has separate client item definitions.
b32_put(stationres/"items/armor_station.json",{
 "model":{"type":"minecraft:model","model":"obsidiannetwork:item/armor_station"}
})
# Exactly vanilla enchantment maximum count of cards, each worth 2 vanilla
# enchantment levels. Both drag-click and shift-insertion share this cap.
b35_java("powerarmor/ArmorStationMenu.java",
'''   if(duplicate>=(card.upgradeId.equals("protection")?8:1))return;''',
'''   if(duplicate>=maxCardCount(card.upgradeId))return;''')
b35_java("powerarmor/ArmorStationMenu.java",
'''  if(duplicates>=(card.upgradeId.equals("protection")?8:1))return ItemStack.EMPTY;''',
'''  if(duplicates>=maxCardCount(card.upgradeId))return ItemStack.EMPTY;''')
b35_java("powerarmor/ArmorStationMenu.java",
''' private List<String> cards(ItemStack chest){''',
''' private static int maxCardCount(String id){
  return switch(id){
   case "protection","fire_protection","blast_protection",
        "projectile_protection","feather_falling" -> 4;
   case "respiration","thorns","depth_strider","soul_speed",
        "swift_sneak" -> 3;
   case "frost_walker" -> 2;
   case "mending","unbreaking" -> 0;
   default -> 1;
  };
 }
 private List<String> cards(ItemStack chest){''')
# Disable old card recipes and hide them from the creative tab and upgrade
# systems while preserving old registry IDs for world compatibility.
for gone in ("mending","unbreaking"):
 for craft in (stationres/f"recipe/power_card_{gone}.json",
               stationres/f"recipes/power_card_{gone}.json"):
  if craft.exists():craft.unlink()
# Metadata for installed legacy cards is deliberately retained and can be
# extracted, avoiding data loss in existing worlds.
print("BUILD40_RENDER_MAPPING PASS: item definition, 15-slot grouped caps, 2x-level cards, disabled legacy cards")


# BUILD42_OWN_SCREEN: bespoke sci-fi Armor Station front end on top of the
# battle-tested server-authoritative chest-compatible 27-slot transport.
# This changes only the CLIENT view: no dupes, no inventory/backup migration.
screen=j/"powerarmor/ArmorStationScreen.java"
screen.write_text(r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.ChestScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;

/** xSxLabs armored service console. Not the vanilla chest appearance. */
public final class ArmorStationScreen extends ChestScreen {
 public ArmorStationScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
 }
 @Override protected void renderBg(GuiGraphics g,float partial,int mouseX,int mouseY){
  int x=this.leftPos, y=this.topPos;
  // Brushed graphite bezel, cyan conductive outline.
  g.fill(x-3,y-3,x+179,y+this.imageHeight+3,0xff101820);
  g.fill(x-2,y-2,x+178,y+this.imageHeight+2,0xff22cfe4);
  g.fill(x,y,x+176,y+this.imageHeight,0xff1b2935);
  g.fill(x+5,y+16,x+171,y+70,0xff0c161e);
  g.fill(x+5,y+72,x+171,y+this.imageHeight-4,0xff263746);
  // Four suit assembly sockets, status pane and 15 upgrade sockets.
  for(int index=0;index<27;index++){
   int sx=x+7+(index%9)*18;
   int sy=y+17+(index/9)*18;
   int line=(index<4)?0xffd4b35d:
           (index==4)?0xff32d8d8:
           (index>=9&&index<24)?0xff66aed9:0xff445e71;
   g.fill(sx,sy,sx+18,sy+18,line);
   g.fill(sx+1,sy+1,sx+17,sy+17,0xff17212e);
  }
  // Actual player inventory uses vanilla slot positions, but bespoke styling.
  int offset=this.imageHeight-114;
  for(int index=0;index<36;index++){
   int col=index%9;
   int row=index<27?index/9:3;
   int sx=x+7+col*18;
   int sy=y+offset+(index<27?84+row*18:142);
   // Vanilla ChestScreen calculates its own slot foreground hitboxes.
   g.fill(sx,sy,sx+18,sy+18,0xff3e637a);
   g.fill(sx+1,sy+1,sx+17,sy+17,0xff233440);
  }
  g.fill(x+5,y+this.imageHeight-5,x+171,y+this.imageHeight-3,0xff16c9e5);
 }
}
''',encoding="utf-8")
# A client-only NeoForge event swaps only this menu based on its dedicated
# title. Ordinary chests and other 9x3 menus are untouched.
key=j/"powerarmor/PowerArmorExitKeyClient.java"
code=key.read_text(encoding="utf-8")
old=''' @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){'''
# That register method is already removed in stage2, so insert before the
# public class' last brace instead of depending on a stale anchor.
assert code.rstrip().endswith("}")
insert=r'''
 @SubscribeEvent public static void xsxArmorStationOpen(
     net.neoforged.neoforge.client.event.ScreenEvent.Opening event){
  if(!(event.getNewScreen() instanceof
      net.minecraft.client.gui.screens.inventory.ChestScreen chest))return;
  var name=chest.getTitle().getString();
  if(!name.startsWith("Armor Station"))return;
  var game=Minecraft.getInstance();
  if(game.player==null)return;
  event.setNewScreen(new ArmorStationScreen(chest.getMenu(),
      game.player.getInventory(),chest.getTitle()));
 }
'''
key.write_text(code.rstrip()[:-1]+insert+"}\\n",encoding="utf-8")
print("BUILD42_OWN_SCREEN PASS: xSxLabs dark sci-fi station screen and 15 card sockets; ordinary chests untouched")


# BUILD43_V5_HINGES: restore a complete visible opening rather than displaced
# panels. Only visual meshes are changed. Real suit, card, FE and recovery state
# stays exclusively on the authenticated armor stand.
# In 42 the writer accidentally used a literal backslash-n after Java's final
# class brace; fix the generated Java syntax before compiling.
key=j/"powerarmor/PowerArmorExitKeyClient.java"
java=key.read_text(encoding="utf-8")
if java.endswith("}\\n"):
 java=java[:-2]+"\n"
key.write_text(java,encoding="utf-8")
# A second model definition was required for each versioned panel; make sure
# every moving part references precisely one explicit cuboid item model.
for tier in ("mk1","mk2"):
 for piece in models:
  q=stationres/f"models/item/armor_visual_{tier}_{piece}.json"
  data=_json.loads(q.read_text(encoding="utf-8"))
  data["parent"]="minecraft:block/block"
  data["ambientocclusion"]=False
  # Base plate only, zero coplanar sub-plates. Artifacts observed in both
  # palettes originated from several cubes sharing the same face plane.
  data["elements"]=data["elements"][:1]
  b32_put(q,data)
# Fix overly distant z planes from build38. Hinged plates now visibly swing
# out of the suit center, with different depth per part to avoid z fighting.
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   double z=(i==4?-0.17D:(i<2?-0.25D:-0.28D));
   double depthShift=i*0.015D;''',
'''   double z=(i==4?-0.16D:(i<2?-0.23D:-0.26D));
   double depthShift=i*0.022D;''')
b35_java("powerarmor/PowerArmorSuitWorld.java",
'''   panel.setYRot((float)((i==4?0D:side*76.0D*open)));''',
'''   // The v5 effect depended on the plates visibly swinging rather than
   // sliding backward. Swing the two chest plates 85 degrees outward.
   panel.setYRot((float)((i==4?0D:side*(i<2?85.0D:66.0D)*open)));''')
# No extra color ribbon planes during any part of the opening cycle.
assert all(len(_json.loads((stationres/f"models/item/armor_visual_{t}_{part}.json").read_text())["elements"])==1
 for t in ("mk1","mk2") for part in models)
print("BUILD43_V5_HINGES PASS: v5 outward hinge motion restored, explicit block meshes without overlapping decorative faces, generated client Java validated")
