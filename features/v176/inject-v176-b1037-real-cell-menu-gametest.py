#!/usr/bin/env python3
"""B1037 actual Minecraft server GameTest for Cell Terminal -> real Drive.
Patches existing active 50-Drive/800-Cell GameTest after it's assembled, then
executes the menu's real server quickMoveStack AND 8-pad clicked routes.
No fake in-memory network, no static-only method-string assertions.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(!rt.powered())throw new IllegalStateException("Full test network did not power up");'
marker="V176_B1037_REAL_CELL_TERMINAL_2_ROUTES_PASS"
assert s.count(anchor)==1,("B1037_SERVER_TEST_ANCHOR",s.count(anchor))
assert marker not in s
for guard in ("var xsxPlayerInv=xsxBurstPlayer.getInventory();",
              "BlockPos xsxlabsBurstTerminalPos=",
              "if(insertedCells!=800)throw new IllegalStateException",
              "var xsxMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu("):
 assert guard in s,("B1037_REAL_NETWORK_FIXTURE_MISSING",guard)
test=r'''
                  // This is a real 50-Drive, 800-cell, powered controller.
                  // Place actual Cell Terminal directly on the already-bound
                  // Crafting Terminal, without overwriting any existing cable.
                  BlockPos xsxCellPos=xsxlabsBurstTerminalPos.above();
                  if(!level.isEmptyBlock(xsxCellPos))
                   throw new IllegalStateException("B1037 Cell Terminal fixture blocked at "+xsxCellPos);
                  level.setBlock(xsxCellPos,
                    ObsidianNetwork.V176_CELL_TERMINAL.get().defaultBlockState(),3);
                  if(!(level.getBlockEntity(xsxCellPos)
                       instanceof dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity xsxCellBe))
                   throw new IllegalStateException("B1037 real Cell Terminal BE absent");
                  var xsxScan=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(
                    level,xsxCellPos);
                  if(!xsxScan.online()||xsxScan.drives().size()!=50)
                   throw new IllegalStateException("B1037 connected terminal did not see 50 real Drives: online="+
                    xsxScan.online()+" drives="+xsxScan.drives().size()+" free="+xsxScan.freeSlots());
                  // Free exactly ONE real DriveContainer slot, then use the
                  // same GUI path the player uses. Restore it at end to avoid
                  // perturbing the existing 800-cell workload and performance.
                  var xsxCellDrive=xsxScan.drives().get(0);
                  var xsxBacking=dev.obsidiannetwork.menu.DriveMenu.xsxCellTerminalBacking(xsxCellDrive);
                  int xsxSlot=0;
                  var xsxOriginalCell=xsxBacking.getItem(xsxSlot).copy();
                  if(xsxOriginalCell.isEmpty()||
                       !(xsxOriginalCell.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem))
                   throw new IllegalStateException("B1037 expected real installed StorageCellItem");
                  xsxBacking.setItem(xsxSlot,net.minecraft.world.item.ItemStack.EMPTY);
                  var xsxOpened=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(
                     level,xsxCellPos);
                  if(!xsxOpened.online()||xsxOpened.freeSlots()<1)
                   throw new IllegalStateException("B1037 Cell Terminal did not see newly empty real Drive slot"+
                     " online="+xsxOpened.online()+" free="+xsxOpened.freeSlots());
                  xsxBurstPlayer.setPos(xsxCellPos.getX()+0.5D,
                     xsxCellPos.getY()+0.5D,xsxCellPos.getZ()+0.5D);
                  var xsxCellMenu=new dev.obsidiannetwork.cellterminal.V176CellTerminalMenu(
                      99,xsxPlayerInv,xsxCellBe);
                  // (A) Shift-click: player hotbar slot 0 is menu index 81.
                  xsxPlayerInv.setItem(0,xsxOriginalCell.copyWithCount(1));
                  var xsxShifted=xsxCellMenu.quickMoveStack(xsxBurstPlayer,81);
                  if(xsxShifted.isEmpty()||xsxShifted.getCount()!=1
                      ||!xsxPlayerInv.getItem(0).isEmpty()
                      ||!net.minecraft.world.item.ItemStack.matches(
                          xsxBacking.getItem(xsxSlot),xsxOriginalCell))
                   throw new IllegalStateException("B1037 real SHIFT-click did not install/consume cell");
                  // (B) Player cursor -> visible pad 0 via actual clicked().
                  xsxBacking.setItem(xsxSlot,net.minecraft.world.item.ItemStack.EMPTY);
                  xsxCellMenu.setCarried(xsxOriginalCell.copyWithCount(1));
                  xsxCellMenu.clicked(0,0,null,xsxBurstPlayer);
                  if(!xsxCellMenu.getCarried().isEmpty()
                      ||!net.minecraft.world.item.ItemStack.matches(
                         xsxBacking.getItem(xsxSlot),xsxOriginalCell))
                   throw new IllegalStateException("B1037 real cursor clicked(0) did not install/consume cell");
                  // Another click with no cursor cell cannot generate an item.
                  xsxCellMenu.clicked(0,0,null,xsxBurstPlayer);
                  if(!xsxCellMenu.getCarried().isEmpty()||
                      !net.minecraft.world.item.ItemStack.matches(
                         xsxBacking.getItem(xsxSlot),xsxOriginalCell))
                   throw new IllegalStateException("B1037 phantom pad duplicated real cell");
                  if(!xsxCellMenu.slots.get(0).getItem().isEmpty())
                   throw new IllegalStateException("B1037 fake pad retained cell rather than Drive");
                  // The 800 original full Drive slots are fully restored here.
                  System.out.println("V176_B1037_REAL_CELL_TERMINAL_2_ROUTES_PASS drives=50"+
                    " shift_click=true cursor_pad=true cursor_conservation=true"+
                    " real_drive_nbt=true no_virtual_storage=true");
'''
s=s.replace(anchor,anchor+"\n"+test,1)
assert s.count(marker)==1
p.write_text(s,encoding="utf-8")
print(marker+" INJECTED")
