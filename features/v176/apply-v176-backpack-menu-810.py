#!/usr/bin/env python3
"""B810: actual server-owned Backpack equipment/menu bridge and unbound key.

This implements only item/cell/upgrade GUI + direct access. Search, 3x3 craft,
stored-item deposit/extraction and visual inventory are separate release gates.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

def edit(path,old,new):
 p=J/path
 source=p.read_text(encoding="utf-8")
 assert source.count(old)==1,("V176_B810_SOURCE_DRIFT",path,source.count(old))
 p.write_text(source.replace(old,new,1),encoding="utf-8")

def write(path,source):
 p=J/path
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_B810_DUPLICATE",path)
 p.write_text(source,encoding="utf-8")

# World BE item state is changed by exactly one explicit ownership transfer.
edit("backpack/NetworkBackpackBlockEntity.java",
 " public ItemStack getBackpack(){return backpack;}",
 """ public ItemStack getBackpack(){return backpack;}
 public boolean replaceBackpack(ItemStack expected,ItemStack updated){
  if(!(updated.getItem() instanceof NetworkBackpackItem)
      ||!ItemStack.matches(backpack,expected))return false;
  backpack=updated.copy();
  backpack.setCount(1);
  setChanged();
  if(level!=null&&!level.isClientSide())
   level.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);
  return true;
 }""")

# The backpack item performs GUI opening (without placing); sneaking retains
# the existing world-placement behavior and placed-bag pickup takes precedence.
edit("backpack/NetworkBackpackItem.java",
 " public int visualTier(){return visualTier;}",
 """ public int visualTier(){return visualTier;}
 @Override public InteractionResult use(net.minecraft.world.level.Level world,
        net.minecraft.world.entity.player.Player player,net.minecraft.world.InteractionHand hand){
  if(hand!=net.minecraft.world.InteractionHand.MAIN_HAND)return InteractionResult.PASS;
  return V176BackpackOpen.openHeld(player,hand);
 }""")
edit("backpack/NetworkBackpackItem.java",
 """  if(context.getPlayer()!=null&&!context.getPlayer().isShiftKeyDown())
   return InteractionResult.PASS;""",
 """  if(context.getPlayer()!=null&&!context.getPlayer().isShiftKeyDown())
   return V176BackpackOpen.openHeld(context.getPlayer(),context.getHand());""")
edit("backpack/NetworkBackpackBlock.java",
 "  // Terminal-style GUI open will be connected after menu registration.\n  return InteractionResult.SUCCESS;",
 """  return V176BackpackOpen.openPlaced(server,pos);""")

write("backpack/V176BackpackOpen.java",'''package dev.obsidiannetwork.backpack;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;

/** All entry points create a real server-validated menu, no remote slot ID. */
public final class V176BackpackOpen {
 private V176BackpackOpen(){}
 private static final Component TITLE=Component.literal("xSxLabs Network Backpack");
 public static InteractionResult openHeld(Player player,InteractionHand hand){
  if(!(player.getItemInHand(hand).getItem() instanceof NetworkBackpackItem))
   return InteractionResult.PASS;
  if(player instanceof ServerPlayer p&&!p.isSpectator()){
   V176BackpackEquipped.Where where=hand==InteractionHand.MAIN_HAND
      ?V176BackpackEquipped.Where.MAIN_HAND:V176BackpackEquipped.Where.OFF_HAND;
   ItemStack stack=p.getItemInHand(hand);
   open(p,new V176BackpackMenu.ItemSource(p,
       new V176BackpackEquipped.Located(where,-1,stack)));
  }
  return InteractionResult.SUCCESS;
 }
 public static int openWorn(ServerPlayer p){
  if(p.isSpectator())return 0;
  V176BackpackEquipped.Located source=V176BackpackEquipped.worn(p);
  if(source==null)return 0;
  open(p,new V176BackpackMenu.ItemSource(p,source));
  return 1;
 }
 public static InteractionResult openPlaced(ServerPlayer p,BlockPos pos){
  if(p.isSpectator()||p.distanceToSqr(pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5)>64)
   return InteractionResult.FAIL;
  if(!(p.level().getBlockEntity(pos) instanceof NetworkBackpackBlockEntity be)
       ||be.getBackpack().isEmpty())return InteractionResult.FAIL;
  open(p,new V176BackpackMenu.BlockSource(p,be,pos));
  return InteractionResult.SUCCESS;
 }
 private static void open(ServerPlayer p,V176BackpackMenu.Source source){
  p.openMenu(new SimpleMenuProvider(
     (id,inv,user)->new V176BackpackMenu(id,inv,source),TITLE));
 }
}
''')

write("backpack/V176BackpackMenu.java",'''package dev.obsidiannetwork.backpack;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.item.StorageCellItem;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Strictly four live side slots; NO hidden duplicate item store.
 * The 50 unused 9x6 slots are not valid containers or drop targets.
 */
public final class V176BackpackMenu extends ChestMenu {
 public interface Source {
  ItemStack current();
  boolean valid();
  boolean save(ItemStack next);
 }
 public static final class ItemSource implements Source {
  private final ServerPlayer player;
  private V176BackpackEquipped.Located location;
  public ItemSource(ServerPlayer player,V176BackpackEquipped.Located location){
   this.player=player;this.location=location;
  }
  private ItemStack live(){
   return switch(location.where()){
    case CHEST->player.getItemBySlot(EquipmentSlot.CHEST);
    case MAIN_HAND->player.getItemInHand(InteractionHand.MAIN_HAND);
    case OFF_HAND->player.getItemInHand(InteractionHand.OFF_HAND);
    case CURIOS_BACK->{
     var found=V176BackpackEquipped.worn(player);
     yield found!=null&&found.where()==V176BackpackEquipped.Where.CURIOS_BACK
          &&found.index()==location.index()?found.stack():ItemStack.EMPTY;
    }
   };
  }
  @Override public ItemStack current(){return live();}
  @Override public boolean valid(){
   return player.isAlive()&&ItemStack.matches(live(),location.stack())
       &&live().getItem() instanceof NetworkBackpackItem;
  }
  @Override public boolean save(ItemStack next){
   if(!valid()||!(next.getItem() instanceof NetworkBackpackItem))return false;
   location.persist(player,next);
   location=new V176BackpackEquipped.Located(location.where(),
       location.index(),next.copy());
   return true;
  }
 }
 public static final class BlockSource implements Source {
  private final ServerPlayer player;
  private final NetworkBackpackBlockEntity be;
  private final BlockPos pos;
  private ItemStack snapshot;
  public BlockSource(ServerPlayer player,NetworkBackpackBlockEntity be,BlockPos pos){
   this.player=player;this.be=be;this.pos=pos.immutable();
   snapshot=be.getBackpack().copy();
  }
  @Override public ItemStack current(){return be.getBackpack();}
  @Override public boolean valid(){
   return player.isAlive()&&player.level()==be.getLevel()
      &&player.level().getBlockEntity(pos)==be
      &&player.distanceToSqr(pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5)<=64
      &&ItemStack.matches(snapshot,be.getBackpack());
  }
  @Override public boolean save(ItemStack next){
   if(!valid()||!be.replaceBackpack(snapshot,next))return false;
   snapshot=next.copy();
   return true;
  }
 }
 private static final class Storage extends SimpleContainer {
  private final Source source;
  Storage(Source source){super(54);this.source=source;}
  @Override public boolean stillValid(Player player){return source.valid();}
  @Override public ItemStack getItem(int slot){
   if(slot<0||slot>=4||!source.valid())return ItemStack.EMPTY;
   return V176BackpackCells.slots(source.current()).get(slot).copy();
  }
  @Override public boolean isEmpty(){
   for(int i=0;i<4;i++)if(!getItem(i).isEmpty())return false;
   return true;
  }
  @Override public boolean canPlaceItem(int slot,ItemStack stack){
   if(slot<0||slot>=4||stack.isEmpty()||stack.getCount()!=1
      ||stack.getItem() instanceof NetworkBackpackItem)return false;
   if(slot==0)return stack.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get());
   return stack.getItem() instanceof StorageCellItem;
  }
  private boolean removable(int slot){
   ItemStack stack=getItem(slot);
   if(stack.isEmpty())return false;
   if(slot==0)return true;
   // Do not let a filled storage cell escape while other transfers are live.
   return stack.getItem() instanceof StorageCellItem cell
        &&cell.readStore(stack).used()==0;
  }
  @Override public void setItem(int slot,ItemStack stack){
   if(slot<0||slot>=4||!source.valid())return;
   var entries=V176BackpackCells.slots(source.current());
   var previous=entries.get(slot);
   if(ItemStack.matches(previous,stack))return;
   if(!stack.isEmpty()&&(!canPlaceItem(slot,stack)||!previous.isEmpty()))return;
   if(stack.isEmpty()&&!removable(slot))return;
   entries.set(slot,stack.copy());
   ItemStack updated=source.current().copy();
   V176BackpackCells.writeSlots(updated,entries);
   source.save(updated);
  }
  @Override public ItemStack removeItem(int slot,int amount){
   if(amount<=0||!removable(slot))return ItemStack.EMPTY;
   ItemStack original=getItem(slot);
   setItem(slot,ItemStack.EMPTY);
   return getItem(slot).isEmpty()?original:ItemStack.EMPTY;
  }
  @Override public ItemStack removeItemNoUpdate(int slot){
   return removeItem(slot,1);
  }
  @Override public void clearContent(){
   // Closing a GUI must NEVER destroy cells or upgrade item data.
  }
  boolean magnet(boolean enabled,boolean whitelist){
   if(!source.valid())return false;
   ItemStack next=source.current().copy();
   if(!V176BackpackCells.magnetEnabled(next)
      &&V176BackpackCells.magnet(next).isEmpty())return false;
   V176BackpackCells.magnetSettings(next,enabled,whitelist);
   return source.save(next);
  }
 }
 private final Storage storage;
 public V176BackpackMenu(int id,Inventory playerInventory,Source source){
  this(id,playerInventory,new Storage(source));
 }
 private V176BackpackMenu(int id,Inventory playerInventory,Storage storage){
  super(MenuType.GENERIC_9x6,id,playerInventory,storage,6);
  this.storage=storage;
  for(int i=0;i<54;i++){
   final int slot=i;
   // The other 50 placeholder slots must be completely inaccessible.
   slots.set(i,new Slot(storage,i,i<4?195:-100,i<4?20+i*24:-100){
    @Override public boolean mayPlace(ItemStack stack){
     return slot<4&&storage.canPlaceItem(slot,stack)
          &&storage.getItem(slot).isEmpty();
    }
    @Override public boolean mayPickup(Player player){
     return slot<4&&storage.removable(slot);
    }
   });
  }
 }
 @Override public boolean stillValid(Player player){return storage.stillValid(player);}
 @Override public ItemStack quickMoveStack(Player p,int index){
  // A future transaction-aware transfer will implement shift-click; until then
  // fail CLOSED rather than duplicating a filled cell or recursive backpack.
  return ItemStack.EMPTY;
 }
 public boolean setMagnet(ServerPlayer player,boolean enabled,boolean whitelist){
  return player.containerMenu==this&&storage.magnet(enabled,whitelist);
 }
}
''')

write("backpack/V176BackpackCommands.java",'''package dev.obsidiannetwork.backpack;

import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** Only the actually open validated backpack menu may mutate magnet state. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176BackpackCommands {
 private V176BackpackCommands(){}
 @SubscribeEvent public static void register(RegisterCommandsEvent e){
  e.getDispatcher().register(Commands.literal("networkbackpack")
    .then(Commands.literal("open").executes(ctx->
       V176BackpackOpen.openWorn(ctx.getSource().getPlayerOrException())))
    .then(Commands.literal("magnet")
      .then(Commands.literal("on").executes(ctx->change(ctx.getSource().getPlayerOrException(),true,null)))
      .then(Commands.literal("off").executes(ctx->change(ctx.getSource().getPlayerOrException(),false,null)))
      .then(Commands.literal("whitelist").executes(ctx->change(ctx.getSource().getPlayerOrException(),null,true)))
      .then(Commands.literal("blacklist").executes(ctx->change(ctx.getSource().getPlayerOrException(),null,false)))));
 }
 private static int change(ServerPlayer p,Boolean enabled,Boolean whitelist){
  if(!(p.containerMenu instanceof V176BackpackMenu menu))return 0;
  // The menu's server source is authoritative, never a selected client slot.
  return menu.setMagnet(p,enabled==null?menuMagnet(p):enabled,
                       whitelist==null?menuWhitelist(p):whitelist)?1:0;
 }
 private static boolean menuMagnet(ServerPlayer p){
  if(!(p.containerMenu instanceof V176BackpackMenu menu))return false;
  return menu.magnetEnabled();
 }
 private static boolean menuWhitelist(ServerPlayer p){
  if(!(p.containerMenu instanceof V176BackpackMenu menu))return false;
  return menu.magnetWhitelist();
 }
}
''')
# Read-only accessors for the command's unchanged flag.
edit("backpack/V176BackpackMenu.java",
 " public boolean setMagnet(ServerPlayer player,boolean enabled,boolean whitelist){",
 """ public boolean magnetEnabled(){return storage.source.valid()
     &&V176BackpackCells.magnetEnabled(storage.source.current());}
 public boolean magnetWhitelist(){return storage.source.valid()
     &&V176BackpackCells.magnetWhitelist(storage.source.current());}
 public boolean setMagnet(ServerPlayer player,boolean enabled,boolean whitelist){""")

write("client/V176BackpackKeyClient.java",'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.platform.InputConstants;
import dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** Unbound by default. Key never transmits arbitrary coordinates or slots. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176BackpackKeyClient {
 private V176BackpackKeyClient(){}
 public static final KeyMapping OPEN=new KeyMapping(
   "key.obsidiannetwork.open_backpack",
   InputConstants.Type.KEYSYM,InputConstants.UNKNOWN.getValue(),
   PowerArmorExitKeyClient.CATEGORY);
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  while(OPEN.consumeClick()){
   var mc=Minecraft.getInstance();
   if(mc.player!=null&&mc.screen==null&&mc.player.connection!=null)
    mc.player.connection.sendCommand("networkbackpack open");
  }
 }
}
''')

# ClientModEvents already registers Power Armor exit in the same xSxLabs group.
edit("client/ClientModEvents.java",
 "  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.EXIT);",
 """  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.EXIT);
  event.register(dev.obsidiannetwork.client.V176BackpackKeyClient.OPEN);""")

import json
for locale,text in (("de_de","Network-Rucksack öffnen"),("en_us","Open Network Backpack")):
 p=R/"assets/obsidiannetwork/lang"/(locale+".json")
 data=json.loads(p.read_text(encoding="utf-8"))
 assert "key.obsidiannetwork.open_backpack" not in data
 data["key.obsidiannetwork.open_backpack"]=text
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V176_B810_BACKPACK_REAL_4_SLOTS_BLOCK_HELD_HOTKEY_MAGNET_SERVER_MENU_READY")
