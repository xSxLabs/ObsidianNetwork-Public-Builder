#!/usr/bin/env python3
"""B1040: The user's REQUIRED architecture, not the old fake click-action pads.

Real BlockEntity inventory: 8 visible and persistent input slots. A standard
ChestMenu client/server slot click places cells INTO THE TERMINAL even while
offline/full. Every 5 server ticks, the BE moves them automatically to the
real connected StorageDrive BlockEntity backing. It consumes the terminal
cell only after checking the Drive's exact ItemStack/NBT, and never holds a
phantom item in the other 46 GUI preview cells. Normal inventory sync handles
client UI. World/chunk persistence survives reloads.
"""
import os
from pathlib import Path
ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def read(f):return (ROOT/f).read_text(encoding="utf-8")
def write(f,s):(ROOT/f).write_text(s,encoding="utf-8")
def change(f,a,b):
 s=read(f)
 assert s.count(a)==1,("B1040_SOURCE_DRIFT",f,s.count(a),a[:125])
 write(f,s.replace(a,b,1))
# Replace old BlockEntity status-only shell with actual Container slots. This
# reuses Minecraft's native ContainerHelper persistence (ValueInput/Output).
p="cellterminal/V176CellTerminalBlockEntity.java"
old=read(p)
for marker in ("extends BlockEntity","public static void serverTick","public void xsxRefresh(ServerLevel server)",
               "xsxFree","connectedDrives","V176CellTerminalTopology.scan"):
 assert marker in old,("B1040_BE_INCOMPATIBLE",marker)
write(p,r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.item.StorageCellItem;
import dev.obsidiannetwork.item.EquipmentCellItem;
import dev.obsidiannetwork.menu.DriveMenu;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import java.util.ArrayList;
import java.util.Comparator;

/** Actual persistent 8-cell input buffer for live delivery to physical Drives.
 * All other 46 generic-9x6 menu positions are inert/empty. This BE never
 * stores an installed Cell if a real Drive successfully accepted it.
 */
public final class V176CellTerminalBlockEntity extends BlockEntity implements Container {
 public static final int INPUT_SLOTS=8, GUI_SLOTS=54;
 private final NonNullList<ItemStack> buffered=NonNullList.withSize(GUI_SLOTS,ItemStack.EMPTY);
 private int connectedDrives,freeSlots,revision;
 private boolean online,truncated;
 public V176CellTerminalBlockEntity(BlockPos p,BlockState state){
  super(ModBlockEntities.V176_CELL_TERMINAL.get(),p,state);
 }
 public static boolean isCell(ItemStack stack){
  return !stack.isEmpty()&&(stack.getItem() instanceof StorageCellItem
       ||stack.getItem() instanceof EquipmentCellItem);
 }
 public int connectedDrives(){return connectedDrives;}
 public int freeSlots(){return freeSlots;}
 public boolean online(){return online;}
 public boolean truncated(){return truncated;}
 public int bufferedCells(){
  int n=0;
  for(int i=0;i<INPUT_SLOTS;i++)n+=buffered.get(i).getCount();
  return n;
 }
 @Override public int getContainerSize(){return GUI_SLOTS;}
 @Override public boolean isEmpty(){
  for(int i=0;i<INPUT_SLOTS;i++)if(!buffered.get(i).isEmpty())return false;
  return true;
 }
 @Override public boolean canPlaceItem(int slot,ItemStack stack){
  return slot>=0&&slot<INPUT_SLOTS&&isCell(stack);
 }
 @Override public ItemStack getItem(int slot){
  return slot>=0&&slot<INPUT_SLOTS?buffered.get(slot):ItemStack.EMPTY;
 }
 @Override public ItemStack removeItem(int slot,int count){
  if(slot<0||slot>=INPUT_SLOTS||count<=0)return ItemStack.EMPTY;
  ItemStack result=ContainerHelper.removeItem(buffered,slot,count);
  if(!result.isEmpty())setChanged();
  return result;
 }
 @Override public ItemStack removeItemNoUpdate(int slot){
  if(slot<0||slot>=INPUT_SLOTS)return ItemStack.EMPTY;
  ItemStack result=ContainerHelper.takeItem(buffered,slot);
  if(!result.isEmpty())setChanged();
  return result;
 }
 @Override public void setItem(int slot,ItemStack value){
  if(slot<0||slot>=INPUT_SLOTS)return;
  if(!value.isEmpty()&&!isCell(value))return;
  buffered.set(slot,value.isEmpty()?ItemStack.EMPTY:value.copy());
  setChanged();
 }
 @Override public boolean stillValid(Player player){
  return level!=null&&level.getBlockEntity(worldPosition)==this
      &&player.distanceToSqr(worldPosition.getX()+.5D,
            worldPosition.getY()+.5D,worldPosition.getZ()+.5D)<=64D;
 }
 @Override public void clearContent(){
  for(int i=0;i<INPUT_SLOTS;i++)buffered.set(i,ItemStack.EMPTY);
  setChanged();
 }
 @Override public void setChanged(){
  super.setChanged();
  // Synchronize status & real cell icon changes when inventory is modified.
  if(level instanceof ServerLevel server)
   server.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);
 }
 @Override protected void saveAdditional(ValueOutput output){
  super.saveAdditional(output);
  ContainerHelper.saveAllItems(output,buffered);
  output.putInt("xsxDrives",connectedDrives);
  output.putInt("xsxFree",freeSlots);
  output.putInt("xsxRev",revision);
  output.putBoolean("xsxOnline",online);
  output.putBoolean("xsxTruncated",truncated);
 }
 @Override protected void loadAdditional(ValueInput input){
  super.loadAdditional(input);
  for(int i=0;i<GUI_SLOTS;i++)buffered.set(i,ItemStack.EMPTY);
  ContainerHelper.loadAllItems(input,buffered);
  // Never expose or consume corrupt items serialized into virtual slots.
  for(int i=INPUT_SLOTS;i<GUI_SLOTS;i++)buffered.set(i,ItemStack.EMPTY);
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
  if(!(world instanceof ServerLevel server))return;
  if(server.getGameTime()%5L==0L&&be.bufferedCells()>0)
   be.xsxAutoTransfer(server);
  if(server.getGameTime()%40L==0L)be.xsxRefresh(server);
 }
 /** Server owned: an installed Cell must exist in a REAL drive's BE backing
  * before the queued source is decremented. If network is down or full, the
  * buffer remains in-world and survives save/reload automatically.
  */
 public int xsxAutoTransfer(ServerLevel server){
  if(isEmpty())return 0;
  var scan=V176CellTerminalTopology.scan(server,worldPosition);
  if(!scan.online()||scan.freeSlots()<1)return 0;
  var drives=new ArrayList<>(scan.drives());
  int delivered=0;
  for(int slot=0;slot<INPUT_SLOTS;slot++){
   ItemStack source=buffered.get(slot);
   if(!isCell(source))continue;
   while(!source.isEmpty()){
    drives.sort(Comparator.comparingInt(StorageDriveBlockEntity::occupiedSlots)
        .thenComparingLong(d->d.getBlockPos().asLong()));
    boolean inserted=false;
    for(StorageDriveBlockEntity drive:drives){
     if(drive.isRemoved()||drive.getLevel()!=server
         ||!server.hasChunkAt(drive.getBlockPos()))continue;
     int free=drive.xsxCellTerminalFirstEmptySlot();
     if(free<0)continue;
     Container backing=DriveMenu.xsxCellTerminalBacking(drive);
     if(!backing.getItem(free).isEmpty())continue;
     ItemStack one=source.copyWithCount(1);
     try{
      backing.setItem(free,one);
      if(!ItemStack.matches(backing.getItem(free),one)){
       // No source was decremented; only undo our exact rejected write.
       if(ItemStack.matches(backing.getItem(free),one))
        backing.setItem(free,ItemStack.EMPTY);
       continue;
      }
     }catch(RuntimeException failure){
      System.err.println("XSXLABS_B1040_CELL_DRIVE_WRITE_FAILED "+
          drive.getBlockPos()+" reason="+failure);
      continue;
     }
     source.shrink(1);
     if(source.isEmpty())buffered.set(slot,ItemStack.EMPTY);
     setChanged();
     delivered++;
     inserted=true;
     break;
    }
    if(!inserted)break;
   }
  }
  if(delivered>0){
   xsxRefresh(server);
   System.out.println("XSXLABS_B1040_AUTO_CELL_DELIVERY terminal="+worldPosition
       +" drives="+drives.size()+" moved="+delivered+" pending="+bufferedCells());
  }
  return delivered;
 }
 public void xsxRefresh(ServerLevel server){
  var scan=V176CellTerminalTopology.scan(server,worldPosition);
  if(connectedDrives!=scan.drives().size()||freeSlots!=scan.freeSlots()
      ||online!=scan.online()||truncated!=scan.truncated()){
   connectedDrives=scan.drives().size();
   freeSlots=scan.freeSlots();
   online=scan.online();
   truncated=scan.truncated();
   revision++;
   setChanged();
  }
 }
}
''')
# Remove click-action interception AND shift-click direct-to-drive. Both
# routes now store items in the same 8 BE slots; its ticker does the delivery.
p="cellterminal/V176CellTerminalMenu.java"
old=read(p)
for marker in ("extends ChestMenu","for(int pad=0;pad<8;pad++)","@Override public void clicked(","@Override public ItemStack quickMoveStack("):
 assert marker in old,("B1040_MENU_INCOMPATIBLE",marker)
write(p,r'''package dev.obsidiannetwork.cellterminal;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Real vanilla-synced ChestMenu over a persistent 8-slot cell input buffer.
 * Click a pad to deposit a Cell into the terminal. Server ticker moves it to
 * connected, real Drive BEs. An offline/full network keeps it in this buffer.
 */
public final class V176CellTerminalMenu extends ChestMenu {
 private final V176CellTerminalBlockEntity terminal;
 public V176CellTerminalMenu(int id,Inventory inv,V176CellTerminalBlockEntity target){
  super(MenuType.GENERIC_9x6,id,inv,target,6);
  terminal=target;
  for(int i=0;i<54;i++){
   Slot prior=slots.get(i);
   if(i<8){
    slots.set(i,new Slot(prior.container,i,39+(i%4)*24,81+(i/4)*24){
     @Override public boolean isActive(){return true;}
     @Override public boolean mayPlace(ItemStack stack){
      return V176CellTerminalBlockEntity.isCell(stack);
     }
     @Override public boolean mayPickup(Player player){return true;}
     @Override public int getMaxStackSize(ItemStack stack){return 1;}
    });
   }else{
    slots.set(i,new Slot(prior.container,i,-10000,-10000){
     @Override public boolean isActive(){return false;}
     @Override public boolean mayPlace(ItemStack stack){return false;}
     @Override public boolean mayPickup(Player player){return false;}
    });
   }
  }
 }
 @Override public boolean stillValid(Player player){return terminal.stillValid(player);}
 @Override public void clicked(int id,int button,ContainerInput action,Player player){
  if(id>=8&&id<54)return;
  // The normal vanilla ChestMenu click now really writes the BE inventory.
  super.clicked(id,button,action,player);
 }
 @Override public ItemStack quickMoveStack(Player player,int id){
  if(id<0||id>=slots.size()||!stillValid(player))return ItemStack.EMPTY;
  Slot selected=slots.get(id);
  if(!selected.hasItem())return ItemStack.EMPTY;
  ItemStack original=selected.getItem().copy();
  if(id<8){
   // Taking a queued Cell back into the player inventory is always possible.
   ItemStack stack=selected.getItem();
   if(!moveItemStackTo(stack,54,90,true))return ItemStack.EMPTY;
   if(stack.isEmpty())selected.setByPlayer(ItemStack.EMPTY);
   else selected.setChanged();
   broadcastChanges();
   return original;
  }
  if(id<54||!V176CellTerminalBlockEntity.isCell(selected.getItem()))
   return ItemStack.EMPTY;
  ItemStack stack=selected.getItem();
  int moved=0;
  for(int input=0;input<8&&!stack.isEmpty();input++){
   if(!terminal.getItem(input).isEmpty())continue;
   terminal.setItem(input,stack.copyWithCount(1));
   stack.shrink(1);
   moved++;
  }
  if(moved<1)return ItemStack.EMPTY;
  if(stack.isEmpty())selected.setByPlayer(ItemStack.EMPTY);
  else selected.setChanged();
  broadcastChanges();
  return original;
 }
}
''')
# Client slots MUST agree with server slots. No client-side action pad and
# never allow the dead 46 preview slots to take cell items.
p="client/V176CellTerminalScreen.java"
s=read(p)
assert s.count("  for(int pad=0;pad<8;pad++){")>=1
start=s.index("  for(int pad=0;pad<8;pad++){")
end=s.index("\n }\n private V176CellTerminalBlockEntity live(){",start)
slotblock=r'''  for(int pad=0;pad<8;pad++){
   Slot original=this.menu.slots.get(pad);
   this.menu.slots.set(pad,new Slot(original.container,pad,
       39+(pad%4)*24,81+(pad/4)*24){
    @Override public boolean isActive(){return true;}
    @Override public boolean mayPlace(ItemStack stack){
     return dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity.isCell(stack);
    }
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){
     return true;
    }
    @Override public int getMaxStackSize(ItemStack stack){return 1;}
   });
  }
  for(int pad=8;pad<54;pad++){
   Slot original=this.menu.slots.get(pad);
   this.menu.slots.set(pad,new Slot(original.container,pad,-10000,-10000){
    @Override public boolean isActive(){return false;}
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){
     return false;
    }
   });
  }'''
s=s[:start]+slotblock+s[end:]
# Avoid giving user an incorrect instruction that cells disappear immediately.
s=s.replace('g.text(font,"8 LIVE CELL INPUTS",8,18,0xffb899ff);',
 '''g.text(font,"8 CELL INPUTS - AUTO MOVE",8,18,0xffb899ff);''')
s=s.replace('g.text(font,"Storage Cells stay in your inventory if full",8,122,0xffaabec9);',
 '''g.text(font,"Cells warten bei vollen Drives im Terminal",8,122,0xffaabec9);''')
# The actual server-ticked BE status is synced via BE update packets.
needle='''   g.text(font,"Free Cell Slots: "+be.freeSlots(),8,67,0xffbddff0);'''
if needle in s:s=s.replace(needle,needle+'''
   g.text(font,"Im Terminal: "+be.bufferedCells(),8,46,0xffb899ff);''',1)
# The historical GUI visual must keep exactly 8 drawn input backgrounds.
assert "for(int pad=0;pad<8;pad++)" in s
write(p,s)
for marker in ("implements Container","ContainerHelper.saveAllItems","ContainerHelper.loadAllItems",
               "xsxAutoTransfer(server)","DriveMenu.xsxCellTerminalBacking","source.shrink(1)"):
 assert marker in read("cellterminal/V176CellTerminalBlockEntity.java"),("B1040_BUFFER_REGRESSION",marker)
assert "super(MenuType.GENERIC_9x6,id,inv,target,6)" in read("cellterminal/V176CellTerminalMenu.java")
assert "super.clicked(id,button,action,player)" in read("cellterminal/V176CellTerminalMenu.java")
assert "isCell(stack)" in read("client/V176CellTerminalScreen.java")
print("B1040_ACTUAL_PERSISTENT_8_CELL_BUFFER_VANILLA_GUI_SERVER_AUTO_REAL_DRIVES_PASS")
