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
                  if(xsx1040Be.xsxAutoTransfer(level)!=1
                       ||xsx1040Be.bufferedCells()!=0
                       ||!net.minecraft.world.item.ItemStack.matches(
                          xsx1040Backing.getItem(0),xsx1040Cell))
                   throw new IllegalStateException("B1040 real automatic ticker failed to move buffered Cell into Drive");
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
                  if(xsx1040Be.xsxAutoTransfer(level)!=1||xsx1040Be.bufferedCells()!=0
                    ||!net.minecraft.world.item.ItemStack.matches(
                         xsx1040Backing.getItem(0),xsx1040Cell))
                   throw new IllegalStateException("B1040 reconnect did not deliver queued Cell");
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
                  // Restore fixture: no generated Cells, no lost original Cells.
                  xsx1040Be.clearContent();
                  if(!xsx1040Be.isEmpty())throw new IllegalStateException("B1040 clear failed");
                  System.out.println("V176_B1040_REAL_BUFFER_AUTOTICK_CABLE_DRIVE_PASS"+
                    " drives=50 input_slots=8 actual_click=true real_buffer_nbt=true"+
                    " full_drive_queues=true drive_readback=true shift_queues_first=true"+
                    " disconnected_hold=true reconnect_auto_delivers=true");
'''
s=s.replace(anchor,anchor+"\n"+test,1)
assert s.count(marker)==1
p.write_text(s,encoding="utf-8")
print(marker+" INJECTED")
