#!/usr/bin/env python3
"""v1.7.3 functional devices: Laser Miner, Blueprint/Network Printer, Hologram.

Blueprint records an area using two right-clicked corners and stores selected
block IDs in ItemStack CUSTOM_DATA, not in unsafe client-only memory.
Printer consumes actual xSxLabs network inventory and local FE, preserves
progress across chunk reloads and reports missing materials in GUI title.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def add(path,body):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p;p.write_text(body,encoding="utf-8")
def change(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8");assert s.count(old)==1,(path,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def obj(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
newblocks={"NETWORK_HOLOGRAM_TERMINAL":("network_hologram_terminal","HOLOGRAM"),
 "NETWORK_LASER_MINER":("network_laser_miner","MINER"),
 "NETWORK_PRINTER":("network_printer","PRINTER")}
declarations="\n".join('''    public static final DeferredBlock<dev.obsidiannetwork.block.NetworkDeviceBlock> %s =
        BLOCKS.registerBlock("%s",p -> new dev.obsidiannetwork.block.NetworkDeviceBlock(p,dev.obsidiannetwork.block.NetworkDeviceBlock.Mode.%s),
             p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F).noOcclusion());
    public static final DeferredItem<BlockItem> %s_ITEM =
        ITEMS.registerSimpleBlockItem("%s",%s);'''%(field,name,kind,field,name,field) for field,(name,kind) in newblocks.items())
declarations+='''\n    public static final DeferredItem<dev.obsidiannetwork.item.NetworkBlueprintItem> NETWORK_BLUEPRINT =
        ITEMS.registerItem("network_blueprint",dev.obsidiannetwork.item.NetworkBlueprintItem::new);\n'''
change("ObsidianNetwork.java",
 'ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);',
 'ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);\n'+declarations)
change("ObsidianNetwork.java",
 '            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());',
 '            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());\n'+
 ''.join('            output.accept((ItemLike)%s_ITEM.get());\n'%k for k in newblocks)+
 '            output.accept((ItemLike)NETWORK_BLUEPRINT.get());')
change("registry/ModBlockEntities.java",
 '   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity>> NETWORK_PLANTER =',
 '''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity>> NETWORK_DEVICE =
       TYPES.register("network_device",()->new BlockEntityType(
         dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.NETWORK_HOLOGRAM_TERMINAL.get(),
            (Block)ObsidianNetwork.NETWORK_LASER_MINER.get(),
            (Block)ObsidianNetwork.NETWORK_PRINTER.get()}));
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity>> NETWORK_PLANTER =''')
add("item/NetworkBlueprintItem.java",r'''package dev.obsidiannetwork.item;

import java.util.*;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.component.TypedDataComponent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.Blocks;

/** V173_BLUEPRINT_ITEM: left marker/right marker via two clicks, max 16x16x16.
 * Strict dimension check and immutable copy on insertion into printer.
 */
public final class NetworkBlueprintItem extends Item {
 public static final int MAX_SIZE=16;
 public NetworkBlueprintItem(Properties p){super(p.stacksTo(1));}
 public static String read(ItemStack item,String key){
  CustomData data=item.get(DataComponents.CUSTOM_DATA);
  return data==null?"":data.copyTag().getStringOr(key,"");
 }
 public static void write(ItemStack item,String key,String value){
  CompoundTag tag=item.get(DataComponents.CUSTOM_DATA)==null?new CompoundTag():
    item.get(DataComponents.CUSTOM_DATA).copyTag();
  tag.putString(key,value);
  item.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
 }
 public static List<String> blocks(ItemStack item){
  String str=read(item,"xsxlabs_blocks");
  return str.isBlank()?List.of():Arrays.asList(str.split(",",-1));
 }
 @Override public InteractionResult useOn(UseOnContext context){
  if(!(context.getLevel() instanceof ServerLevel level))return InteractionResult.SUCCESS;
  var user=context.getPlayer();if(user==null)return InteractionResult.PASS;
  ItemStack stack=context.getItemInHand();
  BlockPos at=context.getClickedPos();
  String dimension=level.dimension().identifier().toString();
  String start=read(stack,"xsxlabs_first");
  String key=dimension+"|"+at.getX()+"|"+at.getY()+"|"+at.getZ();
  if(start.isBlank()||!start.startsWith(dimension+"|")){
   write(stack,"xsxlabs_first",key);
   write(stack,"xsxlabs_blocks","");
   user.displayClientMessage(Component.literal("Blueprint: First corner "+at.toShortString()+" saved. Right-click opposite corner."),true);
   return InteractionResult.SUCCESS;
  }
  String[] p=start.substring(dimension.length()+1).split(",");
  if(p.length!=3){write(stack,"xsxlabs_first",key);return InteractionResult.SUCCESS;}
  int x1=Integer.parseInt(p[0]),y1=Integer.parseInt(p[1]),z1=Integer.parseInt(p[2]);
  int loX=Math.min(x1,at.getX()),loY=Math.min(y1,at.getY()),loZ=Math.min(z1,at.getZ());
  int sx=Math.abs(x1-at.getX())+1,sy=Math.abs(y1-at.getY())+1,sz=Math.abs(z1-at.getZ())+1;
  if(sx>MAX_SIZE||sy>MAX_SIZE||sz>MAX_SIZE){
   user.displayClientMessage(Component.literal("Blueprint selection too large (max 16 x 16 x 16). Select the first corner again."),true);
   write(stack,"xsxlabs_first","");return InteractionResult.FAIL;
  }
  ArrayList<String> out=new ArrayList<>(sx*sy*sz);
  for(int y=0;y<sy;y++)for(int z=0;z<sz;z++)for(int x=0;x<sx;x++){
   BlockPos where=new BlockPos(loX+x,loY+y,loZ+z);
   var state=level.getBlockState(where);
   // Safe capture excludes BE blocks (inventories/claims) and unsuitable blocks.
   if(level.getBlockEntity(where)!=null||!state.getFluidState().isEmpty()||state.getDestroySpeed(level,where)<0){
    out.add("minecraft:air");continue;
   }
   out.add(BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString());
  }
  write(stack,"xsxlabs_blocks",String.join(",",out));
  write(stack,"xsxlabs_size",sx+","+sy+","+sz);
  write(stack,"xsxlabs_first","");
  user.displayClientMessage(Component.literal("Blueprint saved: "+sx+"x"+sy+"x"+sz+
       " ("+out.size()+" blocks). Insert into Network Printer."),true);
  return InteractionResult.SUCCESS;
 }
}
''')
add("v173/BlueprintIds.java",r'''package dev.obsidiannetwork.v173;
import net.minecraft.resources.Identifier;
/** No package identifiers looked up through runtime variable shadowing. */
public final class BlueprintIds {
 private BlueprintIds(){}
 public static Identifier parse(String text){return Identifier.tryParse(text);}
}
''')
add("block/NetworkDeviceBlock.java",r'''package dev.obsidiannetwork.block;

import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
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

public final class NetworkDeviceBlock extends BaseEntityBlock {
 public enum Mode { HOLOGRAM, MINER, PRINTER }
 private final Mode mode;
 private static final MapCodec<NetworkDeviceBlock> H=
    simpleCodec(p->new NetworkDeviceBlock(p,Mode.HOLOGRAM));
 private static final MapCodec<NetworkDeviceBlock> M=
    simpleCodec(p->new NetworkDeviceBlock(p,Mode.MINER));
 private static final MapCodec<NetworkDeviceBlock> P=
    simpleCodec(p->new NetworkDeviceBlock(p,Mode.PRINTER));
 public NetworkDeviceBlock(Properties p,Mode m){super(p);mode=m;}
 public Mode mode(){return mode;}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){
  return switch(mode){case HOLOGRAM->H;case MINER->M;case PRINTER->P;};
 }
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new NetworkDeviceBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
       Level l,BlockState s,BlockEntityType<T> t){
  return l.isClientSide()?null:createTickerHelper(t,ModBlockEntities.NETWORK_DEVICE.get(),
       NetworkDeviceBlockEntity::tick);
 }
 private InteractionResult act(Level level,BlockPos pos,Player player,ItemStack held){
  if(level.isClientSide())return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer sp)||!(level.getBlockEntity(pos) instanceof NetworkDeviceBlockEntity be))return InteractionResult.PASS;
  if(be.mode()==Mode.PRINTER&&held.isEmpty()&&!player.isShiftKeyDown()){
   // Native synchronized inventory GUI (blueprint slot 0, FE cell slot 1).
   sp.openMenu(new SimpleMenuProvider((id,inv,p)->new dev.obsidiannetwork.menu.NetworkPrinterMenu(id,inv,be),
       Component.literal("xSxLabs Network Printer | "+be.status())));
  }else be.handle(sp,held);
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,
      Player u,BlockHitResult hit){return act(l,p,u,ItemStack.EMPTY);}
 @Override protected InteractionResult useItemOn(ItemStack stack,BlockState s,Level l,
      BlockPos p,Player u,net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?act(l,p,u,stack):InteractionResult.PASS;
 }
}
''')
add("menu/NetworkPrinterMenu.java",r'''package dev.obsidiannetwork.menu;

import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** V173_PRINTER_GUI: two real synced inventory slots; 25 blocked background slots. */
public final class NetworkPrinterMenu extends ChestMenu {
 private final NetworkDeviceBlockEntity printer;
 public NetworkPrinterMenu(int id,Inventory inventory,NetworkDeviceBlockEntity be){
  super(MenuType.GENERIC_9x3,id,inventory,be,3);
  printer=be;
  slots.set(0,new Slot(be,0,26,35){
   @Override public boolean mayPlace(ItemStack s){return s.getItem() instanceof dev.obsidiannetwork.item.NetworkBlueprintItem;}
  });
  slots.set(1,new Slot(be,1,62,35){
   @Override public boolean mayPlace(ItemStack s){return dev.obsidiannetwork.core.EnergyTool.capacity(s)>0;}
  });
  for(int i=2;i<27;i++){
   final int index=i;
   slots.set(i,new Slot(be,index,8+(i%9)*18,18+(i/9)*18){
    @Override public boolean mayPlace(ItemStack s){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player p){return printer.stillValid(p);}
}
''')
add("blockentity/NetworkDeviceBlockEntity.java",r'''package dev.obsidiannetwork.blockentity;

import java.util.*;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.block.NetworkDeviceBlock;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.core.ItemKey;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.item.NetworkBlueprintItem;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/** V173_NETWORK_MACHINE: three devices, authoritative server-side actions.
 * None runs clientside or extracts FE across wireless network links.
 */
public final class NetworkDeviceBlockEntity extends BlockEntity implements Container {
 private ItemStack blueprint=ItemStack.EMPTY,energy=ItemStack.EMPTY,tool=ItemStack.EMPTY;
 private final ItemStack[] output=new ItemStack[9];
 private int index=0,completed=0,range=2;
 private boolean running=false;
 private String status="IDLE";
 private static final int WORK_TICKS=5;
 public NetworkDeviceBlockEntity(BlockPos pos,BlockState state){
  super(ModBlockEntities.NETWORK_DEVICE.get(),pos,state);
  Arrays.fill(output,ItemStack.EMPTY);
 }
 public NetworkDeviceBlock.Mode mode(){
  return getBlockState().getBlock() instanceof NetworkDeviceBlock b?b.mode():NetworkDeviceBlock.Mode.HOLOGRAM;
 }
 public String status(){return status;}
 private void setStatus(String s){if(!s.equals(status)){status=s;setChanged();}}
 private void sync(){setChanged();if(level!=null&&!level.isClientSide())level.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);}
 @Override public net.minecraft.nbt.CompoundTag getUpdateTag(HolderLookup.Provider registry){return saveWithoutMetadata(registry);}
 @Override public Packet<ClientGamePacketListener> getUpdatePacket(){return ClientboundBlockEntityDataPacket.create(this);}
 private NetworkRuntime network(ServerLevel world){
  for(Direction d:Direction.values()){
   BlockPos p=worldPosition.relative(d);
   if(!world.hasChunkAt(p)||!world.getBlockState(p).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;
   var rt=WorldTopologyBridge.runtimeForAccessory(world,p);
   if(rt!=null&&rt.powered())return rt;
  }
  return null;
 }
 public void handle(ServerPlayer player,ItemStack held){
  if(!(level instanceof ServerLevel world))return;
  if(mode()==NetworkDeviceBlock.Mode.MINER && held.is(Items.NETHERITE_PICKAXE)
    || mode()==NetworkDeviceBlock.Mode.MINER && held.is(Items.DIAMOND_PICKAXE)){
   if(tool.isEmpty()){tool=held.copyWithCount(1);if(!player.isCreative())held.shrink(1);sync();}
   return;
  }
  if(EnergyTool.capacity(held)>0L && energy.isEmpty()){
   energy=held.copyWithCount(1);if(!player.isCreative())held.shrink(1);sync();return;
  }
  if(player.isShiftKeyDown()){
   if(mode()==NetworkDeviceBlock.Mode.MINER){
    range=range>=4?1:range+1;index=0;sync();
    player.sendSystemMessage(Component.literal("Laser Miner radius "+range+
        " (ores only, depth 12). Use Diamond/Netherite pickaxe and charged FE cell."));
   }else if(mode()==NetworkDeviceBlock.Mode.PRINTER){
    running=!running;sync();
    player.sendSystemMessage(Component.literal("Network Printer "+(running?"RUNNING":"PAUSED")+" | "+status));
   }else player.sendSystemMessage(Component.literal(summary(world)));
  }else{
   if(mode()==NetworkDeviceBlock.Mode.HOLOGRAM)player.sendSystemMessage(Component.literal(summary(world)));
   else {
    running=!running;sync();
    player.sendSystemMessage(Component.literal(mode()+" "+(running?"RUNNING":"PAUSED")+" | "+status));
   }
  }
 }
 private String summary(ServerLevel world){
  var net=network(world);
  if(net==null)return "NETWORK OFFLINE - attach NETWORK cable";
  long used=0L,cap=0L;
  for(var cell:net.storage().cells()){used+=cell.used();cap+=cell.used()+cell.free();}
  int pct=cap>0?(int)(100D*used/cap):0;
  return used+"/"+cap+" items ("+pct+"%) / "+net.storage().cells().size()+" cells"+
      (pct>=90?" / STORAGE WARNING":"");
 }
 private String labelTag(){return "xsx-holo-"+worldPosition.asLong();}
 private void hologram(ServerLevel world){
  var list=world.getEntitiesOfClass(ArmorStand.class,new AABB(worldPosition).inflate(1.5,2.5,1.5),
    e->e.getTags().contains(labelTag()));
  ArmorStand entity;
  if(list.isEmpty()){
   entity=new ArmorStand(world,worldPosition.getX()+.5,worldPosition.getY()+1.55,worldPosition.getZ()+.5);
   entity.setInvisible(true);entity.setNoGravity(true);entity.setMarker(true);
   entity.setCustomNameVisible(true);entity.addTag(labelTag());
   world.addFreshEntity(entity);
  }else entity=list.get(0);
  String str=summary(world);
  entity.setCustomName(Component.literal("xSxLabs | "+str));
  setStatus(str);
  world.sendParticles(new DustParticleOptions(str.contains("WARNING")?0xff9b35:0x29d7eb,.6f),
    worldPosition.getX()+.5,worldPosition.getY()+1.25,worldPosition.getZ()+.5,
    2,.25,.05,.25,.002);
 }
 private int[] size(){
  try{
   String[] s=NetworkBlueprintItem.read(blueprint,"xsxlabs_size").split(",");
   if(s.length!=3)return new int[0];
   int[] d={Integer.parseInt(s[0]),Integer.parseInt(s[1]),Integer.parseInt(s[2])};
   return d[0]>0&&d[1]>0&&d[2]>0&&d[0]<=16&&d[1]<=16&&d[2]<=16?d:new int[0];
  }catch(NumberFormatException e){return new int[0];}
 }
 private void printer(ServerLevel world,NetworkRuntime net){
  if(!running)return;
  int[] dims=size();
  var plan=NetworkBlueprintItem.blocks(blueprint);
  if(dims.length!=3||plan.size()!=dims[0]*dims[1]*dims[2]){
   setStatus("INSERT SAVED BLUEPRINT");return;
  }
  if(net==null){setStatus("NETWORK OFFLINE");return;}
  if(EnergyTool.energy(energy)<250L){setStatus("FE LOW: need 250 FE/block");return;}
  if(index>=plan.size()){running=false;setStatus("COMPLETE "+completed+"/"+plan.size());sync();return;}
  int dx=index%dims[0],dz=(index/dims[0])%dims[2],dy=index/(dims[0]*dims[2]);
  BlockPos dest=worldPosition.offset(dx-dims[0]/2,1+dy,dz+2);
  if(!world.hasChunkAt(dest)){setStatus("CHUNK NOT LOADED");return;}
  if(!world.getBlockState(dest).isAir()){
   index++;setStatus("SKIPPED BLOCKED POSITION "+index+"/"+plan.size());sync();return;
  }
  String name=plan.get(index);
  if("minecraft:air".equals(name)){index++;setStatus("SKIPPED AIR "+index+"/"+plan.size());sync();return;}
  var id=dev.obsidiannetwork.v173.BlueprintIds.parse(name);
  if(id==null){setStatus("INVALID BLUEPRINT BLOCK "+name);return;}
  Block block=BuiltInRegistries.BLOCK.getValue(id);
  ItemStack material=new ItemStack(block.asItem());
  if(block==Blocks.AIR||material.isEmpty()||!block.defaultBlockState().getFluidState().isEmpty()){
   setStatus("UNSUPPORTED BLOCK "+name);return;
  }
  ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(material.getItem()).toString());
  long extracted=net.storage().extract(key,1L);
  if(extracted!=1L){setStatus("MISSING: 1 x "+material.getHoverName().getString());return;}
  // Refund on failed placement; never mine/replace existing world blocks.
  boolean placed=world.setBlock(dest,block.defaultBlockState(),3);
  if(!placed){
   net.storage().insert(key,1L);
   setStatus("PROTECTED/BLOCKED AT "+dest.toShortString());return;
  }
  EnergyTool.consume(energy,250L);
  index++;completed++;
  setStatus("PRINTING "+completed+"/"+plan.size());
  sync();
 }
 private void miner(ServerLevel world,NetworkRuntime net){
  if(!running)return;
  if(net==null){setStatus("NETWORK OFFLINE");return;}
  if(tool.isEmpty()){setStatus("INSERT DIAMOND/NETHERITE PICKAXE");return;}
  if(EnergyTool.energy(energy)<750L){setStatus("FE LOW: need 750 FE/ore");return;}
  int width=2*range+1,slots=width*width*12;
  for(int attempts=0;attempts<8;attempts++){
   int current=(index++)%slots;
   int dy=current/(width*width),ix=current%width;
   BlockPos pos=worldPosition.offset((ix%width)-range,-1-dy,(ix/width)-range);
   if(!world.hasChunkAt(pos))continue;
   BlockState s=world.getBlockState(pos);
   if(world.getBlockEntity(pos)!=null||s.getDestroySpeed(world,pos)<0)continue;
   String id=BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath();
   // Naturally occurring ores only, never machine inventories or claims.
   if(!(id.endsWith("_ore")||id.equals("ancient_debris")))continue;
   var drops=Block.getDrops(s,world,pos,null,null,tool);
   if(drops.isEmpty())continue;
   // Conservatively insert exactly before removing ore. Prevents item loss
   // if network fills, at the cost of one transaction per ore.
   if(drops.size()!=1||drops.get(0).getCount()!=1){setStatus("UNSUPPORTED MULTI-DROP ORE "+id);return;}
   ItemStack drop=drops.get(0);
   ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(drop.getItem()).toString());
   if(net.storage().insert(key,1L)!=1L){setStatus("STORAGE FULL: "+drop.getHoverName().getString());return;}
   if(!world.setBlock(pos,Blocks.AIR.defaultBlockState(),3)){
    net.storage().extract(key,1L);
    setStatus("BLOCK BREAK REFUSED");return;
   }
   EnergyTool.consume(energy,750L);
   setStatus("MINED "+id+" | radius "+range);
   sync();
   world.sendParticles(new DustParticleOptions(0x58d7ff,.8f),
    pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,8,.22,.22,.22,.02);
   return;
  }
 }
 public static void tick(Level level,BlockPos pos,BlockState state,NetworkDeviceBlockEntity be){
  if(!(level instanceof ServerLevel world)||world.getGameTime()%WORK_TICKS!=0)return;
  if(be.mode()==NetworkDeviceBlock.Mode.HOLOGRAM){
   if(world.getGameTime()%40==0)be.hologram(world);
  }else if(be.mode()==NetworkDeviceBlock.Mode.PRINTER)be.printer(world,be.network(world));
  else be.miner(world,be.network(world));
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(!blueprint.isEmpty())out.store("blueprint",ItemStack.CODEC,blueprint);
  if(!energy.isEmpty())out.store("energy",ItemStack.CODEC,energy);
  if(!tool.isEmpty())out.store("tool",ItemStack.CODEC,tool);
  out.putInt("index",index);out.putInt("completed",completed);out.putInt("range",range);
  out.putBoolean("running",running);out.putString("status",status);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  blueprint=in.read("blueprint",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  energy=in.read("energy",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  tool=in.read("tool",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  index=Math.max(0,in.getIntOr("index",0));completed=Math.max(0,in.getIntOr("completed",0));
  range=Math.max(1,Math.min(4,in.getIntOr("range",2)));
  running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");
 }
 @Override public void preRemoveSideEffects(BlockPos pos,BlockState state){
  if(level instanceof ServerLevel world){
   for(ItemStack s:new ItemStack[]{blueprint,energy,tool})
    if(!s.isEmpty())Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,s.copy());
  }
  super.preRemoveSideEffects(pos,state);
 }
 @Override public int getContainerSize(){return 27;}
 @Override public boolean isEmpty(){return blueprint.isEmpty()&&energy.isEmpty()&&tool.isEmpty();}
 @Override public ItemStack getItem(int slot){return slot==0?blueprint:slot==1?energy:ItemStack.EMPTY;}
 @Override public ItemStack removeItem(int slot,int count){
  ItemStack s=getItem(slot);if(s.isEmpty())return ItemStack.EMPTY;
  ItemStack removed=s.split(count);if(s.isEmpty())setItem(slot,ItemStack.EMPTY);sync();return removed;
 }
 @Override public ItemStack removeItemNoUpdate(int slot){
  ItemStack s=getItem(slot);if(s.isEmpty())return ItemStack.EMPTY;
  ItemStack copy=s.copy();setItem(slot,ItemStack.EMPTY);return copy;
 }
 @Override public void setItem(int slot,ItemStack s){
  if(slot==0&&(s.isEmpty()||s.getItem() instanceof NetworkBlueprintItem)){
   if(!ItemStack.isSameItemSameComponents(blueprint,s)){index=0;completed=0;}
   blueprint=s.copy();sync();
  }else if(slot==1&&(s.isEmpty()||EnergyTool.capacity(s)>0)){
   energy=s.copy();sync();
  }
 }
 @Override public boolean canPlaceItem(int slot,ItemStack s){
  return slot==0?s.getItem() instanceof NetworkBlueprintItem:slot==1&&EnergyTool.capacity(s)>0;
 }
 @Override public boolean stillValid(Player p){return !isRemoved()&&p.distanceToSqr(worldPosition.getX()+.5,worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;}
 @Override public void clearContent(){blueprint=energy=tool=ItemStack.EMPTY;index=completed=0;sync();}
}
''')
for name,(field,kind) in [(v[0],(k,v[1])) for k,v in newblocks.items()]:
 asset("models/block/"+name+".json",{"parent":"minecraft:block/cube_all",
   "textures":{"all":"minecraft:block/iron_block","particle":"minecraft:block/iron_block"}})
 asset("blockstates/"+name+".json",{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 asset("models/item/"+name+".json",{"parent":"obsidiannetwork:block/"+name})
 asset("items/"+name+".json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+name}})
 obj(D/"recipe"/(name+".json"),{"type":"minecraft:crafting_shaped","pattern":["IGI","RCR","IHI"],
   "key":{"I":"minecraft:iron_block","G":"minecraft:glass","R":"minecraft:redstone_block",
      "C":"obsidiannetwork:advanced_energy_cell","H":"minecraft:hopper"},
   "result":{"id":"obsidiannetwork:"+name,"count":1}})
obj(D/"recipe/network_blueprint.json",{"type":"minecraft:crafting_shaped","pattern":["PBP","GRG","PBP"],
  "key":{"P":"minecraft:paper","B":"minecraft:book","G":"minecraft:glass","R":"minecraft:redstone"},
  "result":{"id":"obsidiannetwork:network_blueprint","count":1}})
asset("models/item/network_blueprint.json",{"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/paper"}})
asset("items/network_blueprint.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_blueprint"}})
for language in ("de_de","en_us"):
 p=R/"lang"/(language+".json");d=json.loads(p.read_text(encoding="utf-8"))
 for name in [*map(lambda x:x[0],newblocks.values()),"network_blueprint"]:
  d["item.obsidiannetwork."+name]=name.replace("_"," ").title()
  d["block.obsidiannetwork."+name]=name.replace("_"," ").title()
 obj(p,d)
print("V173_PRINTER_MINER_HOLOGRAM_PATCHED: blueprint corners + network-consuming printer, status GUI, FE-dependent miner, holographic telemetry")
