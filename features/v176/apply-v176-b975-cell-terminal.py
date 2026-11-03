#!/usr/bin/env python3
"""B975: network-attached Cell Terminal, 16-slot drive distribution and art.

Never stores a duplicate cell inventory. Server shift-clicks into the existing
DriveMenu backing Container, using 16 real slots per loaded drive. Network
identity must match the terminal's connected powered topology, not merely
nearby blocks. No chunk loading, bounded scan, no client-side mutation.
"""
import os,json
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
D=R/"data/obsidiannetwork"

def change(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    n=s.count(old)
    assert n==1,("B975_SOURCE_DRIFT",rel,n,old[:100])
    p.write_text(s.replace(old,new,1),encoding="utf-8")

def add(rel,body):
    p=J/rel
    assert not p.exists(),("B975_DUPLICATE_CLASS",rel)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(body,encoding="utf-8")

def asset(rel,body):
    p=R/rel
    assert not p.exists(),("B975_DUPLICATE_ASSET",rel)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(body,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

change("ObsidianNetwork.java",
    "   public static final DeferredBlock<dev.obsidiannetwork.power.V176PowerTerminalBlock> V176_POWER_TERMINAL =",
    """   public static final DeferredBlock<dev.obsidiannetwork.cellterminal.V176CellTerminalBlock> V176_CELL_TERMINAL =
       BLOCKS.registerBlock("cell_terminal",dev.obsidiannetwork.cellterminal.V176CellTerminalBlock::new,
         p -> p.mapColor(MapColor.METAL).strength(3.5F,9.0F).requiresCorrectToolForDrops().noOcclusion());
   public static final DeferredItem<BlockItem> V176_CELL_TERMINAL_ITEM =
       ITEMS.registerSimpleBlockItem("cell_terminal",V176_CELL_TERMINAL);
   public static final DeferredBlock<dev.obsidiannetwork.power.V176PowerTerminalBlock> V176_POWER_TERMINAL =""")
change("ObsidianNetwork.java",
    "            output.accept((ItemLike)V176_POWER_TERMINAL_ITEM.get());",
    "            output.accept((ItemLike)V176_POWER_TERMINAL_ITEM.get());\n"+
    "            output.accept((ItemLike)V176_CELL_TERMINAL_ITEM.get());")

change("registry/ModBlockEntities.java",
    "   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.",
    """   public static final DeferredHolder<BlockEntityType<?>,BlockEntityType<dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity>> V176_CELL_TERMINAL =
     TYPES.register("cell_terminal",()->new BlockEntityType(
       dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity::new,
       new Block[]{(Block)ObsidianNetwork.V176_CELL_TERMINAL.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.""")

# DriveMenu is authoritative for how a Drive writes a live storage cell,
# including the 16 real slots, dirty marking and the cell-storage runtime.
# Grant access to its EXISTING inner Container; do not reimplement NBT.
# Avoid repeatedly materializing full 64k-cell NBT just to count empty slots.
# The existing drive's optimized occupiedSlots() already uses its item shells.
change("blockentity/StorageDriveBlockEntity.java",
    "   public int occupiedSlots() {",
    """   // Cell Terminal discovers empty slots from item shells, not serialized cell NBT.
   public int xsxCellTerminalFirstEmptySlot() {
      int index=0;
      for (ItemStack shell : this.cellInventory.copyToList()) {
         if (index>=16) break;
         if (shell.isEmpty()) return index;
         index++;
      }
      return index<16 ? index : -1;
   }
   public int occupiedSlots() {""")

change("menu/DriveMenu.java",
    "   private static final class DriveContainer implements Container {",
    """   // B975: identical storage mutation path for the Cell Terminal.
   // Every use must be checked on the server against the live cable topology.
   public static Container xsxCellTerminalBacking(StorageDriveBlockEntity drive) {
      return new DriveContainer(drive);
   }
   private static final class DriveContainer implements Container {""")

add("cellterminal/V176CellTerminalTopology.java",r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import dev.obsidiannetwork.network.NetworkSignalRelayBridge;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;

/** Never loads chunks or walks another cable network. All results server-owned. */
public final class V176CellTerminalTopology {
 private V176CellTerminalTopology(){}
 private static final int MAX_CABLES=16_384;
 private static final int MAX_DRIVES=2048;
 public record Scan(boolean online, List<StorageDriveBlockEntity> drives,
                    int freeSlots,boolean truncated){}
 private static boolean cable(ServerLevel world,BlockPos at){
  // Reuse the storage system's authoritative NETWORK-only predicate.
  // Includes Network Cable and bundle NETWORK layer; never FE-only bundles.
  return world.hasChunkAt(at)&&NetworkSignalRelayBridge.networkWire(world,at);
 }
 public static Scan scan(ServerLevel world,BlockPos terminal){
  if(!world.hasChunkAt(terminal)||
      !(world.getBlockEntity(terminal) instanceof V176CellTerminalBlockEntity))
   return new Scan(false,List.of(),0,false);
  NetworkRuntime identity=null;
  var pending=new ArrayDeque<BlockPos>();
  for(Direction d:Direction.values()){
   BlockPos adjacent=terminal.relative(d);
   if(!cable(world,adjacent))continue;
   NetworkRuntime network=WorldTopologyBridge.runtimeForAccessory(world,adjacent);
   if(network!=null&&network.powered()){
    identity=network;
    pending.add(adjacent);
    break;
   }
  }
  if(identity==null)return new Scan(false,List.of(),0,false);
  var seen=new HashSet<BlockPos>();
  var found=new HashSet<BlockPos>();
  var drives=new ArrayList<StorageDriveBlockEntity>();
  boolean truncated=false;
  while(!pending.isEmpty()){
   if(seen.size()>=MAX_CABLES){truncated=true;break;}
   BlockPos node=pending.removeFirst();
   if(!seen.add(node)||!cable(world,node))continue;
   // Cable adjacency alone is NOT enough to cross into another network.
   if(WorldTopologyBridge.runtimeForAccessory(world,node)!=identity)continue;
   for(Direction face:Direction.values()){
    BlockPos next=node.relative(face);
    if(!world.hasChunkAt(next))continue;
    if(cable(world,next)){
     if(!seen.contains(next))pending.add(next);
    }else if(!next.equals(terminal)&&found.add(next)
       &&world.getBlockEntity(next) instanceof StorageDriveBlockEntity drive){
     // Only drives physically connected to the verified cable component.
     if(drives.size()>=MAX_DRIVES){truncated=true;pending.clear();break;}
     drives.add(drive);
    }
   }
  }
  drives.sort(Comparator.comparingLong(e->e.getBlockPos().asLong()));
  int free=0;
  for(StorageDriveBlockEntity drive:drives){
   // occupiedSlots() uses lightweight live inventory shells (no full-cell NBT).
   free+=Math.max(0,16-drive.occupiedSlots());
  }
  return new Scan(true,List.copyOf(drives),free,truncated);
 }
}
''')

add("cellterminal/V176CellTerminalBlock.java",r'''package dev.obsidiannetwork.cellterminal;

import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

/** Full-size network hardware; no block face occlusion (noOcclusion on registration). */
public final class V176CellTerminalBlock extends BaseEntityBlock {
 private static final MapCodec<V176CellTerminalBlock> CODEC=simpleCodec(V176CellTerminalBlock::new);
 public static final EnumProperty<Direction> FACING=BlockStateProperties.HORIZONTAL_FACING;
 public V176CellTerminalBlock(Properties properties){
  super(properties);
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder){
  builder.add(FACING);
 }
 @Override public BlockState getStateForPlacement(BlockPlaceContext context){
  return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());
 }
 @Override public BlockState rotate(BlockState state,Rotation rotation){
  return state.setValue(FACING,rotation.rotate(state.getValue(FACING)));
 }
 @Override public BlockState mirror(BlockState state,Mirror mirror){
  return state.rotate(mirror.getRotation(state.getValue(FACING)));
 }
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new V176CellTerminalBlockEntity(pos,state);
 }
 @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
     Level world,BlockState state,BlockEntityType<T> type){
  return world.isClientSide()?null:createTickerHelper(type,
      ModBlockEntities.V176_CELL_TERMINAL.get(),V176CellTerminalBlockEntity::serverTick);
 }
 private InteractionResult open(Level world,BlockPos pos,Player player){
  if(player instanceof ServerPlayer server&&!server.isSpectator()
     &&world.getBlockEntity(pos) instanceof V176CellTerminalBlockEntity terminal){
   server.openMenu(new SimpleMenuProvider((id,inv,p)->
        new V176CellTerminalMenu(id,inv,terminal),
        Component.literal("xSxLabs Cell Terminal @"+
           pos.getX()+","+pos.getY()+","+pos.getZ())));
  }
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState state,Level world,
       BlockPos pos,Player player,BlockHitResult hit){
  return open(world,pos,player);
 }
 @Override protected InteractionResult useItemOn(ItemStack held,BlockState state,
      Level world,BlockPos pos,Player player,InteractionHand hand,BlockHitResult hit){
  return hand==InteractionHand.MAIN_HAND?open(world,pos,player):InteractionResult.PASS;
 }
}
''')

add("cellterminal/V176CellTerminalBlockEntity.java",r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Status only. Cells always reside in real Drive block entities, never here. */
public final class V176CellTerminalBlockEntity extends BlockEntity {
 private int connectedDrives,freeSlots,revision;
 private boolean online,truncated;
 public V176CellTerminalBlockEntity(BlockPos p,BlockState state){
  super(ModBlockEntities.V176_CELL_TERMINAL.get(),p,state);
 }
 public int connectedDrives(){return connectedDrives;}
 public int freeSlots(){return freeSlots;}
 public boolean online(){return online;}
 public boolean truncated(){return truncated;}
 @Override protected void saveAdditional(ValueOutput output){
  super.saveAdditional(output);
  output.putInt("xsxDrives",connectedDrives);
  output.putInt("xsxFree",freeSlots);
  output.putInt("xsxRev",revision);
  output.putBoolean("xsxOnline",online);
  output.putBoolean("xsxTruncated",truncated);
 }
 @Override protected void loadAdditional(ValueInput input){
  super.loadAdditional(input);
  connectedDrives=input.getIntOr("xsxDrives",0);
  freeSlots=input.getIntOr("xsxFree",0);
  revision=input.getIntOr("xsxRev",0);
  online=input.getBooleanOr("xsxOnline",false);
  truncated=input.getBooleanOr("xsxTruncated",false);
 }
 @Override public CompoundTag getUpdateTag(HolderLookup.Provider lookup){
  return saveWithoutMetadata(lookup);
 }
 @Override public Packet<ClientGamePacketListener> getUpdatePacket(){
  return ClientboundBlockEntityDataPacket.create(this);
 }
 public static void serverTick(Level world,BlockPos pos,BlockState state,
                                V176CellTerminalBlockEntity be){
  if(!(world instanceof ServerLevel server)||server.getGameTime()%40L!=0L)return;
  var scan=V176CellTerminalTopology.scan(server,pos);
  if(be.connectedDrives!=scan.drives().size()||be.freeSlots!=scan.freeSlots()
      ||be.online!=scan.online()||be.truncated!=scan.truncated()){
   be.connectedDrives=scan.drives().size();
   be.freeSlots=scan.freeSlots();
   be.online=scan.online();
   be.truncated=scan.truncated();
   be.revision++;
   be.setChanged();
   server.sendBlockUpdated(pos,state,state,3);
  }
 }
}
''')

add("cellterminal/V176CellTerminalMenu.java",r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.item.StorageCellItem;
import dev.obsidiannetwork.menu.DriveMenu;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.Comparator;

/** 54 disabled preview slots + real 36-slot vanilla inventory.
 * Shift-click installs cells into live network drives, balanced by occupancy.
 * A failed or full transfer keeps every remaining cell in the player inventory.
 */
public final class V176CellTerminalMenu extends ChestMenu {
 private final V176CellTerminalBlockEntity terminal;
 public V176CellTerminalMenu(int id,Inventory inv,V176CellTerminalBlockEntity target){
  super(MenuType.GENERIC_9x6,id,inv,new SimpleContainer(54),6);
  terminal=target;
  for(int i=0;i<54;i++){
   Slot original=slots.get(i);
   slots.set(i,new Slot(original.container,original.getContainerSlot(),-10000,-10000){
    @Override public boolean isActive(){return false;}
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(Player player){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player player){
  var world=terminal.getLevel();
  var pos=terminal.getBlockPos();
  return world!=null&&world.getBlockEntity(pos)==terminal
      &&player.distanceToSqr(pos.getX()+.5D,pos.getY()+.5D,pos.getZ()+.5D)<=64D;
 }
 @Override public void clicked(int slotId,int button,ContainerInput action,Player player){
  // No spoofed slot insertion into a non-existent cell holding inventory.
  if(slotId>=0&&slotId<54)return;
  super.clicked(slotId,button,action,player);
 }
 @Override public ItemStack quickMoveStack(Player player,int clickedSlot){
  if(!(player instanceof ServerPlayer server)
      ||!(server.level() instanceof ServerLevel world)
      ||!stillValid(player)||clickedSlot<54||clickedSlot>=slots.size())
   return ItemStack.EMPTY;
  Slot playerSlot=slots.get(clickedSlot);
  ItemStack carried=playerSlot.getItem();
  if(carried.isEmpty()||!(carried.getItem() instanceof StorageCellItem))
   return ItemStack.EMPTY;
  var snapshot=V176CellTerminalTopology.scan(world,terminal.getBlockPos());
  if(!snapshot.online()||snapshot.freeSlots()<1)return ItemStack.EMPTY;
  var drives=new ArrayList<>(snapshot.drives());
  ItemStack original=carried.copy();
  int transferred=0;
  // Repeat until stack consumed or no verified free slot exists.
  // Sort before EACH cell: distribute across drives with the least cells.
  while(transferred<original.getCount()){
   drives.sort(Comparator
      .comparingInt(StorageDriveBlockEntity::occupiedSlots)
      .thenComparingLong(d->d.getBlockPos().asLong()));
   StorageDriveBlockEntity destination=null;
   int targetSlot=-1;
   for(StorageDriveBlockEntity drive:drives){
    if(drive.isRemoved()||drive.getLevel()!=world
        ||!world.hasChunkAt(drive.getBlockPos()))continue;
    int empty=drive.xsxCellTerminalFirstEmptySlot();
    if(empty>=0){destination=drive;targetSlot=empty;break;}
   }
   if(destination==null)break;
   // DriveMenu's own BE-backed Container performs the exact real install
   // and dirtying path. No off-network storage, no new NBT serialization.
   Container backing=DriveMenu.xsxCellTerminalBacking(destination);
   if(!backing.getItem(targetSlot).isEmpty())break;
   ItemStack one=original.copyWithCount(1);
   backing.setItem(targetSlot,one);
   ItemStack inserted=backing.getItem(targetSlot);
   if(!ItemStack.matches(inserted,one)){
    // Do not charge the player for a rejected cell; restore this slot.
    ItemStack rollback=backing.removeItemNoUpdate(targetSlot);
    if(!ItemStack.matches(rollback,one))
     throw new IllegalStateException("Cell Terminal cannot verify atomic insertion");
    break;
   }
   transferred++;
  }
  if(transferred<=0)return ItemStack.EMPTY;
  carried.shrink(transferred);
  playerSlot.setChanged();
  broadcastChanges();
  return original;
 }
}
''')

add("client/V176CellTerminalScreen.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Same navy/steel/cyan visual language as Power Monitor and Network Storage. */
public final class V176CellTerminalScreen extends ContainerScreen {
 private final BlockPos terminal;
 public V176CellTerminalScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
  BlockPos pos=null;
  try{
   String[] coords=title.getString().substring(title.getString().lastIndexOf('@')+1).split(",");
   if(coords.length==3)pos=new BlockPos(Integer.parseInt(coords[0]),
      Integer.parseInt(coords[1]),Integer.parseInt(coords[2]));
  }catch(RuntimeException ignored){}
  terminal=pos;
  // Clientside a vanilla ChestMenu is created; its 54 phantom cells must
  // be disabled here as well so clicks cannot target invisible slots.
  for(int i=0;i<54;i++){
   Slot source=this.menu.slots.get(i);
   this.menu.slots.set(i,new Slot(source.container,source.getContainerSlot(),-10000,-10000){
    @Override public boolean isActive(){return false;}
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player p){return false;}
   });
  }
 }
 private V176CellTerminalBlockEntity live(){
  var game=Minecraft.getInstance();
  if(terminal==null||game.level==null||!game.level.hasChunkAt(terminal))return null;
  return game.level.getBlockEntity(terminal) instanceof V176CellTerminalBlockEntity be?be:null;
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs | CELL TERMINAL",6,6,0xff90f4ff);
  var be=live();
  if(be==null){
   g.text(font,"Waiting for network data...",8,40,0xffecc38b);
  }else{
   g.text(font,"NETWORK: "+(be.online()?"ONLINE":"OFFLINE"),8,29,
       be.online()?0xff7bffb0:0xffff9595);
   g.text(font,"Connected Drives: "+be.connectedDrives(),8,50,0xffbddff0);
   g.text(font,"Free Cell Slots: "+be.freeSlots(),8,67,0xffbddff0);
   if(be.truncated())g.text(font,"Network scan limit reached",8,87,0xffffab71);
  }
  g.text(font,"SHIFT-CLICK Storage Cells to distribute",8,111,0xff90f4ff);
  g.text(font,"Storage Cells stay in your inventory if full",8,122,0xffaabec9);
  g.text(font,"Inventory",8,127,0xffc5e4f0);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();
  g.fill(x-3,y-3,x+179,y+h+3,0xff437a9e);
  g.fill(x,y,x+176,y+h,0xff142637);
  g.fill(x+4,y+16,x+172,y+137,0xff081724);
  g.fill(x+6,y+21,x+170,y+96,0xff132b3c);
  g.fill(x+8,y+100,x+168,y+103,0xff31677b);
  // Preserve all 36 real player slots, NEVER draw invisible 54-slot grid.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?139+(i/9)*18:197);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }
 }
}
''')

# This is the same ScreenEvent.Opening routing approach as the Power Monitor.
p=J/"powerarmor/PowerArmorExitKeyClient.java"
s=p.read_text(encoding="utf-8")
assert s.endswith("}\n"),"B975_CLIENT_SCREEN_EVENT_FOOTER_DRIFT"
assert "xsxV176CellTerminalScreen" not in s
s=s[:-2]+''' @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV176CellTerminalScreen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().startsWith("xSxLabs Cell Terminal @"))return;
  var game=net.minecraft.client.Minecraft.getInstance();
  if(game.player!=null&&chest.getMenu() instanceof net.minecraft.world.inventory.ChestMenu menu)
   e.setNewScreen(new dev.obsidiannetwork.client.V176CellTerminalScreen(
      menu,game.player.getInventory(),chest.getTitle()));
 }
}
'''
p.write_text(s,encoding="utf-8")

asset("assets/obsidiannetwork/blockstates/cell_terminal.json",{"variants":{
 "facing=north":{"model":"obsidiannetwork:block/cell_terminal","y":0},
 "facing=east":{"model":"obsidiannetwork:block/cell_terminal","y":90},
 "facing=south":{"model":"obsidiannetwork:block/cell_terminal","y":180},
 "facing=west":{"model":"obsidiannetwork:block/cell_terminal","y":270}
}})
# Reuse the accepted storage-system casing and color palette. Explicit
# faces without 'cullface' avoid block-occlusion/vanishing-face issues.
base=json.loads((A/"models/block/power_terminal.json").read_text(encoding="utf-8"))
textures=base["textures"].copy()
assert textures["north"]=="obsidiannetwork:block/power_terminal_computer_front"
assert all(textures.get(face) for face in ("north","south","east","west","up","down"))
textures["north"]="obsidiannetwork:block/cell_terminal_front"
faces={face:{"texture":"#"+face} for face in ("north","south","east","west","up","down")}
asset("assets/obsidiannetwork/models/block/cell_terminal.json",{
 "parent":"minecraft:block/block","textures":textures,
 "elements":[{"from":[0,0,0],"to":[16,16,16],"faces":faces}]
})
asset("assets/obsidiannetwork/items/cell_terminal.json",{
 "model":{"type":"minecraft:model","model":"obsidiannetwork:block/cell_terminal"}
})
asset("data/obsidiannetwork/loot_table/blocks/cell_terminal.json",{
 "type":"minecraft:block","pools":[{"rolls":1,
   "entries":[{"type":"minecraft:item","name":"obsidiannetwork:cell_terminal"}]}]
})
asset("data/obsidiannetwork/recipe/cell_terminal.json",{
 "type":"minecraft:crafting_shaped","pattern":["IRI","GCG","IEI"],
 "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone",
        "G":"minecraft:glass_pane","C":"minecraft:comparator",
        "E":"minecraft:ender_pearl"},
 "result":{"id":"obsidiannetwork:cell_terminal","count":1}
})
for lang in ("de_de","en_us"):
    p=A/f"lang/{lang}.json"
    data=json.loads(p.read_text(encoding="utf-8"))
    key="block.obsidiannetwork.cell_terminal"
    assert key not in data
    data[key]="Cell Terminal"
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Brand-matched 16x16 front texture: retain the current Power Monitor glass,
# but depict four luminous storage cells. Do not redraw the accepted front.
from PIL import Image,ImageDraw
original=A/"textures/block/power_terminal_computer_front.png"
assert original.exists(),("B975_MONITOR_FRONT_NOT_FOUND",original)
with Image.open(original) as picture:
    img=picture.convert("RGBA")
# Preserve the existing 32x32 monitor texture resolution (or 16x16 if
# legacy resource packs use it). Scale pixel geometry, not the original art.
assert img.width==img.height and img.width in (16,32),("B975_MONITOR_TEXTURE_SIZE",img.size)
scale=img.width//16
def xy(*coords):return tuple(round(n*scale) for n in coords)
draw=ImageDraw.Draw(img)
draw.rectangle(xy(3,4,12,11),fill=(9,30,44,255),outline=(37,128,157,255),width=scale)
for a in (4,7,10):
    draw.rectangle(xy(a,6,a+1,9),fill=(62,220,242,255))
    draw.rectangle(xy(a,5,a,5),fill=(161,245,247,255))
draw.line(xy(4,12,11,12),fill=(23,134,166,255),width=scale)
output=A/"textures/block/cell_terminal_front.png"
assert not output.exists()
img.save(output)

assert "noOcclusion()" in (J/"ObsidianNetwork.java").read_text()
assert "xsxCellTerminalBacking" in (J/"menu/DriveMenu.java").read_text()
assert "xsxCellTerminalFirstEmptySlot()" in (J/"blockentity/StorageDriveBlockEntity.java").read_text()
assert "drive.xsxCellTerminalFirstEmptySlot()" in (J/"cellterminal/V176CellTerminalMenu.java").read_text()
assert '"cullface"' not in (A/"models/block/cell_terminal.json").read_text()
assert "backing.setItem(targetSlot,one)" in (J/"cellterminal/V176CellTerminalMenu.java").read_text()
assert "if(!ItemStack.matches(inserted,one))" in (J/"cellterminal/V176CellTerminalMenu.java").read_text()
assert "runtimeForAccessory(world,node)!=identity" in (J/"cellterminal/V176CellTerminalTopology.java").read_text()
assert "NetworkSignalRelayBridge.networkWire(world,at)" in (J/"cellterminal/V176CellTerminalTopology.java").read_text()
print("B975_CELL_TERMINAL_DRIVE16_BALANCED_SHIFT_SERVER_ATOMIC_NO_OCCLUSION_TEXTURES_READY")
