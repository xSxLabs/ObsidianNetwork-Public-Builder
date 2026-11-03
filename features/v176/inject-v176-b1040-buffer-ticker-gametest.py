#!/usr/bin/env python3
"""B1040 mandatory GameTest: real vanilla ChestMenu cell buffer + server ticks.
Asserts source BE actually holds cells, NBT saves them, drive remains unchanged
until server auto tick, then the item moves and persists in real Drive backing.
Tests player cursor, hotbar shift, full network, remote cable reconnection and
all 8 buffer slots. This test replaces B1037/B1038's wrong action-pad tests.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(!rt.powered())throw new IllegalStateException("Full test network did not power up");'
marker="V176_B1040_REAL_BUFFER_AUTOTICK_CABLE_DRIVE_PASS"
assert s.count(anchor)==1,("B1040_GAMETEST_FIXTURE_MISSING",s.count(anchor))
for guard in ("var xsxPlayerInv=xsxBurstPlayer.getInventory();",
              "BlockPos xsxlabsBurstTerminalPos=",
              "if(insertedCells!=800)throw new IllegalStateException",
              "var xsxMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu("):
 assert guard in s,("B1040_FIXTURE_INCOMPLETE",guard)
assert marker not in s
test=r'''
                  // Real 50-drive/800-cell game network with a NETWORK cable.
                  // The remote Cell Terminal's 8 slots are BE-backed, not
                  // virtual action buttons, and persist independently of Drives.
                  BlockPos xsx1040Cable=xsxlabsBurstTerminalPos.above();
                  if(!level.isEmptyBlock(xsx1040Cable))
                   throw new IllegalStateException("B1040 cable fixture obstructed");
                  BlockPos xsx1040Pos=null;
                  for(net.minecraft.core.Direction dir:new net.minecraft.core.Direction[]{
                    net.minecraft.core.Direction.NORTH,net.minecraft.core.Direction.SOUTH,
                    net.minecraft.core.Direction.EAST,net.minecraft.core.Direction.WEST}){
                   BlockPos candidate=xsx1040Cable.relative(dir);
                   if(level.hasChunkAt(candidate)&&level.isEmptyBlock(candidate)){
                    xsx1040Pos=candidate;break;
                   }
                  }
                  if(xsx1040Pos==null)
                   throw new IllegalStateException("B1040 cannot place real remote Cell Terminal");
                  level.setBlock(xsx1040Cable,ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState(),3);
                  level.setBlock(xsx1040Pos,ObsidianNetwork.V176_CELL_TERMINAL.get().defaultBlockState(),3);
                  if(!(level.getBlockEntity(xsx1040Pos)
                     instanceof dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity xsx1040Be))
                   throw new IllegalStateException("B1040 BlockEntity missing");
                  var xsx1040Scan=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(
                      level,xsx1040Pos);
                  if(!xsx1040Scan.online()||xsx1040Scan.drives().size()!=50)
                   throw new IllegalStateException("B1040 connected Cell Terminal cannot find 50 Drives: "+
                     xsx1040Scan.drives().size()+" online="+xsx1040Scan.online());
                  var xsx1040Drive=xsx1040Scan.drives().get(0);
                  var xsx1040Backing=dev.obsidiannetwork.menu.DriveMenu.xsxCellTerminalBacking(xsx1040Drive);
                  var xsx1040Cell=xsx1040Backing.getItem(0).copy();
                  if(xsx1040Cell.isEmpty()
                       ||!(xsx1040Cell.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem))
                   throw new IllegalStateException("B1040 missing real installed Cell item");
                  xsxBurstPlayer.setPos(xsx1040Pos.getX()+0.5D,
                    xsx1040Pos.getY()+0.5D,xsx1040Pos.getZ()+0.5D);
                  var xsx1040Menu=new dev.obsidiannetwork.cellterminal.V176CellTerminalMenu(
                      1040,xsxPlayerInv,xsx1040Be);
                  // A full network MUST NOT delete incoming Cells. The buffer
                  // is writable and persisted, even with zero drive capacity.
                  xsx1040Menu.setCarried(xsx1040Cell.copyWithCount(1));
                  xsx1040Menu.clicked(0,0,net.minecraft.world.inventory.ContainerInput.PICKUP,xsxBurstPlayer);
                  if(!xsx1040Menu.getCarried().isEmpty()
                       ||!net.minecraft.world.item.ItemStack.matches(xsx1040Be.getItem(0),xsx1040Cell))
                   throw new IllegalStateException("B1040 cursor click DID NOT deposit to actual Cell Terminal");
                  if(xsx1040Be.xsxAutoTransfer(level)!=0
                       ||xsx1040Be.bufferedCells()!=1)
                   throw new IllegalStateException("B1040 full Drives illegally consumed buffer Cell");
                  if(!xsx1040Be.getUpdateTag(level.registryAccess()).contains("Items"))
                   throw new IllegalStateException("B1040 buffer Cell not serialized in BE NBT");
                  // Free one existing real physical drive slot: the tick
                  // MUST remove buffered Cell and atomically write the Drive.
                  xsx1040Backing.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                  if(!xsx1040Backing.getItem(0).isEmpty())
                   throw new IllegalStateException("B1040 failed to free real drive slot");
                  int xsx1040BeforeTransfer=0;
                  for(var drive:xsx1040Scan.drives())
                   xsx1040BeforeTransfer+=drive.occupiedSlots();
                  int xsx1040Moved=xsx1040Be.xsxAutoTransfer(level);
                  int xsx1040AfterTransfer=0;
                  for(var drive:xsx1040Scan.drives())
                   xsx1040AfterTransfer+=drive.occupiedSlots();
                  System.out.println("XSXLABS_B1040_TRANSFER_COUNTS before="+xsx1040BeforeTransfer+
                      " after="+xsx1040AfterTransfer+" moved="+xsx1040Moved+
                      " pending="+xsx1040Be.bufferedCells()+
                      " originalSlot="+xsx1040Backing.getItem(0));
                  if(xsx1040Moved!=1||xsx1040Be.bufferedCells()!=0
                      ||xsx1040AfterTransfer!=xsx1040BeforeTransfer+1)
                   throw new IllegalStateException("B1040 automatic Cell did NOT enter any real Drive"+
                     " before="+xsx1040BeforeTransfer+" after="+xsx1040AfterTransfer+
                     " moved="+xsx1040Moved+" pending="+xsx1040Be.bufferedCells());
                  // Shift-click MUST queue to BE first, not bypass into a Drive.
                  xsx1040Backing.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                  xsxPlayerInv.setItem(0,xsx1040Cell.copyWithCount(1));
                  var xsx1040Quick=xsx1040Menu.quickMoveStack(xsxBurstPlayer,81);
                  if(xsx1040Quick.isEmpty()||!xsxPlayerInv.getItem(0).isEmpty()
                      ||!net.minecraft.world.item.ItemStack.matches(xsx1040Be.getItem(0),xsx1040Cell)
                      ||!xsx1040Backing.getItem(0).isEmpty())
                   throw new IllegalStateException("B1040 shift-click bypassed real incoming cell buffer");
                  // Disconnect the genuine NETWORK cable. Buffered Cell must
                  // survive offline ticks, then resume when reconnected.
                  level.setBlock(xsx1040Cable,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3);
                  if(dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(level,xsx1040Pos).online())
                   throw new IllegalStateException("B1040 disconnected buffer still reports ONLINE");
                  if(xsx1040Be.xsxAutoTransfer(level)!=0||xsx1040Be.bufferedCells()!=1)
                   throw new IllegalStateException("B1040 offline buffer destroyed pending Cell");
                  level.setBlock(xsx1040Cable,ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState(),3);
                  int xsx1040ReconnectMoved=xsx1040Be.xsxAutoTransfer(level);
                  int xsx1040ReconnectedOccupied=0;
                  for(var drive:xsx1040Scan.drives())
                   xsx1040ReconnectedOccupied+=drive.occupiedSlots();
                  if(xsx1040ReconnectMoved!=1||xsx1040Be.bufferedCells()!=0
                      ||xsx1040ReconnectedOccupied!=800)
                   throw new IllegalStateException("B1040 reconnect did not deliver to real Drive"+
                     " moved="+xsx1040ReconnectMoved+" occupied="+xsx1040ReconnectedOccupied);
                  // All 8 visible slots are genuine persisted BE inventory.
                  // Full Drives leave all 8 queued; no virtual slots ever own cells.
                  for(int i=0;i<8;i++){
                   if(!xsx1040Menu.slots.get(i).isActive()
                      ||!xsx1040Menu.slots.get(i).mayPlace(xsx1040Cell)
                      ||!xsx1040Menu.slots.get(i).mayPickup(xsxBurstPlayer))
                    throw new IllegalStateException("B1040 live Cell input not editable "+i);
                   xsx1040Be.setItem(i,xsx1040Cell.copyWithCount(1));
                  }
                  if(xsx1040Be.bufferedCells()!=8||xsx1040Be.xsxAutoTransfer(level)!=0
                      ||xsx1040Be.bufferedCells()!=8)
                   throw new IllegalStateException("B1040 full network removed one of 8 buffered Cells");
                  for(int i=8;i<54;i++)
                   if(!xsx1040Menu.slots.get(i).getItem().isEmpty())
                    throw new IllegalStateException("B1040 non-input slot stored a phantom cell "+i);
                  if(!xsx1040Be.getUpdateTag(level.registryAccess()).contains("Items"))
                   throw new IllegalStateException("B1040 eight buffered items missing from save");
                  // MULTI-DRIVE distribution regression: eight different,
                  // already-installed physical Cells are removed from eight
                  // different Drive BEs. Queue these exact NBT Items in the
                  // real Cell Terminal. One automatic server transfer must
                  // spread all 8 to the freed Drive slots, not just the first.
                  // First empty the eight temporary full-network probe
                  // cells; next use EIGHT genuine player shift-click packets'
                  // server menu handlers, not direct BE setters.
                  xsx1040Be.clearContent();
                  var xsx1040EightOriginal=new java.util.ArrayList<net.minecraft.world.item.ItemStack>();
                  var xsx1040EightBackings=new java.util.ArrayList<net.minecraft.world.Container>();
                  for(int i=0;i<8;i++){
                   var drive=xsx1040Scan.drives().get(i);
                   var backing=dev.obsidiannetwork.menu.DriveMenu.xsxCellTerminalBacking(drive);
                   var cell=backing.getItem(0).copy();
                   if(!dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity.isCell(cell))
                    throw new IllegalStateException("B1040 multibuffer fixture source missing "+i);
                   xsx1040EightOriginal.add(cell);
                   xsx1040EightBackings.add(backing);
                   backing.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                   xsxPlayerInv.setItem(i,cell.copy());
                   var movedShift=xsx1040Menu.quickMoveStack(xsxBurstPlayer,81+i);
                   if(movedShift.isEmpty()||!xsxPlayerInv.getItem(i).isEmpty()||
                       !net.minecraft.world.item.ItemStack.matches(xsx1040Be.getItem(i),cell))
                    throw new IllegalStateException("B1040 live eighth terminal SHIFT-CLICK failed "+i);
                  }
                  if(xsx1040Be.bufferedCells()!=8)
                   throw new IllegalStateException("B1040 8 shift-clicked Cells not in actual Terminal input buffer");
                  int xsx1040BatchMoved=xsx1040Be.xsxAutoTransfer(level);
                  if(xsx1040BatchMoved!=8||xsx1040Be.bufferedCells()!=0)
                   throw new IllegalStateException("B1040 multibuffer batch not completely delivered"+
                      " moved="+xsx1040BatchMoved+" remaining="+xsx1040Be.bufferedCells());
                  boolean[] xsx1040Matched=new boolean[8];
                  for(var backing:xsx1040EightBackings){
                   var delivered=backing.getItem(0);
                   boolean match=false;
                   for(int i=0;i<8;i++){
                    if(!xsx1040Matched[i]&&net.minecraft.world.item.ItemStack.matches(
                        xsx1040EightOriginal.get(i),delivered)){
                     xsx1040Matched[i]=true;
                     match=true;
                     break;
                    }
                   }
                   if(!match)throw new IllegalStateException(
                      "B1040 multi-Drive distribution changed/lost a real Cell");
                  }
                  System.out.println("XSXLABS_B1040_EIGHT_DISTINCT_DRIVES_AUTODISTRIBUTION_PASS count=8");
                  // B1044: The user's Cells often are NEW CRAFTED items. The
                  // previous GameTests recycled already-installed Cells and
                  // could miss a fresh/empty storage Cell not being accepted.
                  // Exercise pristine 1K Storage and 64K Equipment Cells
                  // through the actual GUI -> persistent buffer -> real Drive.
                  var xsx1040FreshBacking=dev.obsidiannetwork.menu.DriveMenu.xsxCellTerminalBacking(
                      xsx1040Scan.drives().get(0));
                  var xsx1040RestoreCell=xsx1040FreshBacking.getItem(0).copy();
                  if(!dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity.isCell(xsx1040RestoreCell))
                   throw new IllegalStateException("B1044 missing real original Cell for restoration");
                  for(var xsx1040FreshType:new net.minecraft.world.item.Item[]{
                       ObsidianNetwork.STORAGE_CELL_1K.get(),ObsidianNetwork.EQUIPMENT_CELL_64K.get()}){
                   xsx1040FreshBacking.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                   var xsx1040FreshCell=new net.minecraft.world.item.ItemStack(xsx1040FreshType);
                   xsx1040Menu.setCarried(xsx1040FreshCell.copy());
                   xsx1040Menu.clicked(0,0,net.minecraft.world.inventory.ContainerInput.PICKUP,xsxBurstPlayer);
                   if(!xsx1040Menu.getCarried().isEmpty()
                     ||!net.minecraft.world.item.ItemStack.matches(xsx1040Be.getItem(0),xsx1040FreshCell))
                    throw new IllegalStateException("B1044 pristine Cell not accepted by real Cell Terminal");
                   int xsx1040FreshMoved=xsx1040Be.xsxAutoTransfer(level);
                   if(xsx1040FreshMoved!=1||xsx1040Be.bufferedCells()!=0
                     ||!net.minecraft.world.item.ItemStack.matches(
                       xsx1040FreshBacking.getItem(0),xsx1040FreshCell))
                    throw new IllegalStateException("B1044 new uninstalled Cell rejected by connected Drive"+
                        " type="+xsx1040FreshType);
                  }
                  // Restore all original Drive Cells before returning to the
                  // remainder of the full-controller stress test.
                  xsx1040FreshBacking.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                  xsx1040FreshBacking.setItem(0,xsx1040RestoreCell);
                  if(!net.minecraft.world.item.ItemStack.matches(
                       xsx1040FreshBacking.getItem(0),xsx1040RestoreCell))
                   throw new IllegalStateException("B1044 original Drive Cell restoration failed");
                  System.out.println("XSXLABS_B1044_PRISTINE_STORAGE_AND_EQUIPMENT_CELL_AUTO_MOVE_PASS");
                  // Restore fixture: no generated Cells, no lost original Cells.
                  xsx1040Be.clearContent();
                  if(!xsx1040Be.isEmpty())throw new IllegalStateException("B1040 clear failed");
                  System.out.println("V176_B1040_REAL_BUFFER_AUTOTICK_CABLE_DRIVE_PASS"+
                    " drives=50 input_slots=8 actual_click=true real_buffer_nbt=true"+
                    " full_drive_queues=true drive_readback=true shift_queues_first=true"+
                    " disconnected_hold=true reconnect_auto_delivers=true"+
                    " eight_distinct_drive_cells=true eight_player_shift_clicks=true"+
                    " fresh_storage=true fresh_equipment=true");
'''
s=s.replace(anchor,anchor+"\n"+test,1)
assert s.count(marker)==1
p.write_text(s,encoding="utf-8")
print(marker+" INJECTED")
