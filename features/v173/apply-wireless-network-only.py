#!/usr/bin/env python3
"""v1.7.3 wireless NETWORK-only bridge, not wireless FE.

Owner-bound channel via physical Pairing Card. Transmitter source network,
receivers access it via xSxLabs network cables, including cross-dimension.
No range limitation between paired blocks; physical local cable traversal is
bounded to prevent CPU exhaustion. One source per channel; no FE transfer.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def add(name,body):
 p=J/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p;p.write_text(body)
def replace(name,old,new):
 p=J/name;s=p.read_text(encoding="utf-8");assert s.count(old)==1,(name,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def asset(name,value):
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+"\n")
def data(name,value):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+"\n")
replace("ObsidianNetwork.java",
 'ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);',
 '''ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);
    // V173_WIRELESS_NETWORK_ONLY: no FE link, owner-bound channels.
    public static final DeferredBlock<dev.obsidiannetwork.block.WirelessNetworkBlock> NETWORK_TRANSMITTER =
      BLOCKS.registerBlock("network_transmitter",
          p -> new dev.obsidiannetwork.block.WirelessNetworkBlock(p,true),
          p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F));
    public static final DeferredItem<BlockItem> NETWORK_TRANSMITTER_ITEM =
      ITEMS.registerSimpleBlockItem("network_transmitter",NETWORK_TRANSMITTER);
    public static final DeferredBlock<dev.obsidiannetwork.block.WirelessNetworkBlock> NETWORK_RECEIVER =
      BLOCKS.registerBlock("network_receiver",
          p -> new dev.obsidiannetwork.block.WirelessNetworkBlock(p,false),
          p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F));
    public static final DeferredItem<BlockItem> NETWORK_RECEIVER_ITEM =
      ITEMS.registerSimpleBlockItem("network_receiver",NETWORK_RECEIVER);
    public static final DeferredItem<dev.obsidiannetwork.item.NetworkLinkCardItem> NETWORK_LINK_CARD =
      ITEMS.registerItem("network_link_card",dev.obsidiannetwork.item.NetworkLinkCardItem::new);''')
replace("ObsidianNetwork.java",
 '            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());',
 '''            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());
            output.accept((ItemLike)NETWORK_TRANSMITTER_ITEM.get());
            output.accept((ItemLike)NETWORK_RECEIVER_ITEM.get());
            output.accept((ItemLike)NETWORK_LINK_CARD.get());''')
replace("registry/ModBlockEntities.java",
 '   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity>> NETWORK_PLANTER =',
 '''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity>> NETWORK_WIRELESS =
       TYPES.register("network_wireless",()->new BlockEntityType(
         dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.NETWORK_TRANSMITTER.get(),
             (Block)ObsidianNetwork.NETWORK_RECEIVER.get()}));
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity>> NETWORK_PLANTER =''')
add("item/NetworkLinkCardItem.java",r'''package dev.obsidiannetwork.item;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.nbt.CompoundTag;
/** Pairing token, not a wireless energy source. */
public final class NetworkLinkCardItem extends Item {
 public NetworkLinkCardItem(Properties p){super(p.stacksTo(1));}
 public static String read(ItemStack card,String key){
  CustomData data=card.get(DataComponents.CUSTOM_DATA);
  return data==null?"":data.copyTag().getStringOr(key,"");
 }
 public static void write(ItemStack card,String channel,String owner){
  CustomData data=card.get(DataComponents.CUSTOM_DATA);
  CompoundTag nbt=data==null?new CompoundTag():data.copyTag();
  nbt.putString("xsxlabs_network_channel",channel);
  nbt.putString("xsxlabs_network_owner",owner);
  card.set(DataComponents.CUSTOM_DATA,CustomData.of(nbt));
 }
}
''')
add("block/WirelessNetworkBlock.java",r'''package dev.obsidiannetwork.block;

import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

/** Network transmitter and network receiver: metadata only, absolutely no FE. */
public final class WirelessNetworkBlock extends BaseEntityBlock {
 private final boolean transmitter;
 private static final MapCodec<WirelessNetworkBlock> TRANSMITTER=
    simpleCodec(p->new WirelessNetworkBlock(p,true));
 private static final MapCodec<WirelessNetworkBlock> RECEIVER=
    simpleCodec(p->new WirelessNetworkBlock(p,false));
 public WirelessNetworkBlock(Properties p,boolean transmitter){super(p);this.transmitter=transmitter;}
 public boolean transmitter(){return transmitter;}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){
  return transmitter?TRANSMITTER:RECEIVER;
 }
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new WirelessNetworkBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
     Level level,BlockState state,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.NETWORK_WIRELESS.get(),
      WirelessNetworkBlockEntity::tick);
 }
 private InteractionResult interact(Level level,BlockPos pos,Player p,ItemStack stack){
  if(level.isClientSide())return InteractionResult.SUCCESS;
  if(p instanceof net.minecraft.server.level.ServerPlayer player
    &&level.getBlockEntity(pos) instanceof WirelessNetworkBlockEntity be){
    be.interact(player,stack);
  }
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,
     Player player,BlockHitResult hit){return interact(l,p,player,ItemStack.EMPTY);}
 @Override protected InteractionResult useItemOn(ItemStack held,BlockState s,Level l,
     BlockPos p,Player player,net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?
     interact(l,p,player,held):InteractionResult.PASS;
 }
}
''')
add("blockentity/WirelessNetworkBlockEntity.java",r'''package dev.obsidiannetwork.blockentity;

import dev.obsidiannetwork.block.WirelessNetworkBlock;
import dev.obsidiannetwork.item.NetworkLinkCardItem;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import java.util.UUID;

/** Owner-scoped pairing. Transmitter stays loaded to provide cross-dim access.
 * No energy capability, inventory capability, or item-copying functions.
 */
public final class WirelessNetworkBlockEntity extends BlockEntity {
 private String channel="",owner="";
 public WirelessNetworkBlockEntity(BlockPos pos,BlockState state){
  super(ModBlockEntities.NETWORK_WIRELESS.get(),pos,state);
 }
 public boolean transmitter(){
  return getBlockState().getBlock() instanceof WirelessNetworkBlock b && b.transmitter();
 }
 public String channel(){return channel;}
 public String owner(){return owner;}
 public boolean paired(){return !owner.isEmpty()&&!channel.isEmpty();}
 public void interact(ServerPlayer player,ItemStack held){
  if(!(level instanceof ServerLevel world))return;
  String user=player.getUUID().toString();
  if(paired()&&!owner.equals(user)){
   player.sendSystemMessage(Component.literal("This network link belongs to another player."));
   return;
  }
  if(!(held.getItem() instanceof NetworkLinkCardItem)){
   player.sendSystemMessage(Component.literal((transmitter()?"Transmitter":"Receiver")+
     (paired()?" | Paired: "+channel.substring(0,8):" | Unpaired")+
     " | Use Network Link Card to configure."));
   return;
  }
  if(transmitter()){
   if(!paired()){owner=user;channel=UUID.randomUUID().toString();setChanged();}
   NetworkLinkCardItem.write(held,channel,owner);
   world.setChunkForced(worldPosition.getX()>>4,worldPosition.getZ()>>4,true);
   setChanged();
   player.sendSystemMessage(Component.literal("Network Transmitter paired. Transfer this LINK CARD to any receiver, even in another dimension."));
   return;
  }
  String key=NetworkLinkCardItem.read(held,"xsxlabs_network_channel");
  String cardOwner=NetworkLinkCardItem.read(held,"xsxlabs_network_owner");
  if(!cardOwner.equals(user)||key.isBlank()||key.length()!=36){
   player.sendSystemMessage(Component.literal("Use a Link Card configured by your own Network Transmitter."));return;
  }
  try{UUID.fromString(key);}catch(IllegalArgumentException ex){return;}
  channel=key;owner=user;setChanged();
  player.sendSystemMessage(Component.literal("Network Receiver paired with channel "+key.substring(0,8)+". Attach NETWORK cable; energy is NOT transferred."));
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putString("channel",channel);out.putString("owner",owner);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  channel=in.getStringOr("channel","");owner=in.getStringOr("owner","");
 }
 @Override public void preRemoveSideEffects(BlockPos p,BlockState state){
  if(transmitter()&&level instanceof ServerLevel world)
   world.setChunkForced(worldPosition.getX()>>4,worldPosition.getZ()>>4,false);
  super.preRemoveSideEffects(p,state);
 }
 public static void tick(Level l,BlockPos p,BlockState s,WirelessNetworkBlockEntity be){
  // No FE ticking, no entity movement and no forced cross-dim transfer loop.
 }
}
''')
add("network/WirelessNetworkBridge.java",r'''package dev.obsidiannetwork.network;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import dev.obsidiannetwork.core.NetworkRuntime;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

/** V173_WIRELESS_NETWORK_BRIDGE: only resolves live, paired network paths.
 * No FE forwarding; xSxLabs NetworkRuntime remains authoritative.
 * Cross dimension/distance: paired TX searched on all server levels.
 * Local cable BFS bounded to 512 nodes; no chunk loads during lookup.
 */
public final class WirelessNetworkBridge {
 private WirelessNetworkBridge(){}
 private static final ThreadLocal<Boolean> RESOLVING=ThreadLocal.withInitial(()->false);
 public static NetworkRuntime resolve(ServerLevel level,BlockPos queried){
  if(RESOLVING.get()||queried==null)return null;
  RESOLVING.set(true);
  try{
   Set<BlockPos> seen=new HashSet<>();
   ArrayDeque<BlockPos> queue=new ArrayDeque<>();
   queue.add(queried);
   int hops=0;
   while(!queue.isEmpty()&&hops++<512){
    BlockPos at=queue.removeFirst();
    if(!seen.add(at)||!level.hasChunkAt(at))continue;
    var b=level.getBlockState(at);
    if(!b.is(ObsidianNetwork.NETWORK_CABLE.get())&&!at.equals(queried))continue;
    for(Direction face:Direction.values()){
     BlockPos neighbor=at.relative(face);
     if(!level.hasChunkAt(neighbor))continue;
     var state=level.getBlockState(neighbor);
     if(state.is(ObsidianNetwork.NETWORK_RECEIVER.get())&&
         level.getBlockEntity(neighbor) instanceof WirelessNetworkBlockEntity receiver &&
         receiver.paired()){
      NetworkRuntime rt=transmitterRuntime(level,receiver);
      if(rt!=null&&rt.powered())return rt;
     }
     if(state.is(ObsidianNetwork.NETWORK_CABLE.get())&&!seen.contains(neighbor))
      queue.addLast(neighbor);
    }
   }
   return null;
  }finally{RESOLVING.set(false);}
 }
 private static NetworkRuntime transmitterRuntime(ServerLevel receiverLevel,WirelessNetworkBlockEntity rx){
  for(ServerLevel other:receiverLevel.getServer().getAllLevels()){
   // Visit ONLY currently loaded block entities in chunks, never load distant
   // unpaired chunks or perform scans on every server tick.
   for(var be:other.blockEntityList){
    if(!(be instanceof WirelessNetworkBlockEntity tx)||!tx.transmitter()
       ||!tx.paired()||!tx.owner().equals(rx.owner())
       ||!tx.channel().equals(rx.channel()))continue;
    BlockPos origin=tx.getBlockPos();
    for(Direction d:Direction.values()){
     BlockPos cable=origin.relative(d);
     if(!other.hasChunkAt(cable)||
        !other.getBlockState(cable).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;
     NetworkRuntime rt=WorldTopologyBridge.runtimeForAccessory(other,cable);
     if(rt!=null&&rt.powered())return rt;
    }
   }
  }
  return null;
 }
}
''')
# Inject into the existing accessors before their local-graph lookup. The
# RESOLVING ThreadLocal prevents cycles when finding the transmitter runtime.
bridge=J/"network/WorldTopologyBridge.java"
src=bridge.read_text(encoding="utf-8")
for method in ("runtimeForTerminal","runtimeForDrive","runtimeForAutocrafter","runtimeForTesseract","runtimeForAccessory"):
 import re
 pattern=r'(public static NetworkRuntime '+method+r'\(ServerLevel level, BlockPos pos\) \{)'
 match=list(re.finditer(pattern,src))
 assert len(match)==1,(method,len(match))
 insert=match[0].group(1)+'''
       // V173_NETWORK_ONLY_RELAY: remote receiver uses source's storage network.
       // Does not create an energy conduit, cannot mint item stacks.
       NetworkRuntime remote=dev.obsidiannetwork.network.WirelessNetworkBridge.resolve(level,pos);
       if(remote!=null)return remote;'''
 src=src[:match[0].start()]+insert+src[match[0].end():]
bridge.write_text(src,encoding="utf-8")
for name in ("network_transmitter","network_receiver"):
 asset("models/block/"+name+".json",{
  "parent":"minecraft:block/cube_all",
  "textures":{"all":"minecraft:block/obsidian","particle":"minecraft:block/obsidian"}})
 asset("blockstates/"+name+".json",{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 asset("models/item/"+name+".json",{"parent":"obsidiannetwork:block/"+name})
 asset("items/"+name+".json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+name}})
 data("recipe/"+name+".json",{"type":"minecraft:crafting_shaped","pattern":["EGE","RCR","EHE"],
   "key":{"E":"minecraft:ender_pearl","G":"minecraft:glass","R":"minecraft:redstone_block",
          "C":"obsidiannetwork:advanced_energy_cell","H":"minecraft:hopper"},
   "result":{"id":"obsidiannetwork:"+name,"count":1}})
asset("models/item/network_link_card.json",{
  "parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/map"}})
asset("items/network_link_card.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_link_card"}})
data("recipe/network_link_card.json",{"type":"minecraft:crafting_shaped","pattern":["PEP","GRG","PEP"],
  "key":{"P":"minecraft:paper","E":"minecraft:ender_pearl","G":"minecraft:glass","R":"minecraft:redstone"},
  "result":{"id":"obsidiannetwork:network_link_card","count":1}})
for lang in ("de_de","en_us"):
 p=R/"lang"/(lang+".json");d=json.loads(p.read_text(encoding="utf-8"))
 for name in ("network_transmitter","network_receiver","network_link_card"):
  d["item.obsidiannetwork."+name]=name.replace("_"," ").title()
  d["block.obsidiannetwork."+name]=name.replace("_"," ").title()
 asset("lang/"+lang+".json",d)
assert src.count("V173_NETWORK_ONLY_RELAY")==5
print("V173_WIRELESS_NETWORK_ONLY_READY: owner-bound pairing, cross-dim receivers, physical network cable relay, zero wireless FE transfer")
