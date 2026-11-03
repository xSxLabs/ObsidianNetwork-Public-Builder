#!/usr/bin/env python3
"""B1038 REQUIRED real-server regression: Cell Terminal BEHIND a NETWORK wire,
not just directly adjacent to Crafting Terminal (B1037's false-green fixture).

Reuse the fully populated real 50-drive, 800-cell powered game network, create
a remote Cell Terminal one NETWORK cable away, perform actual ChestMenu server
clicks at all eight slots plus player shift-click, and check the real Drive
backing + exact NBT conservation. Also reject disconnected ENERGY-only cable.
"""
from pathlib import Path
import os
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='''                    " real_drive_nbt=true no_virtual_storage=true");'''
assert s.count(anchor)==1,("B1038_EXACT_B1037_FIXTURE_MISSING",s.count(anchor))
marker="V176_B1038_REAL_CABLE_CELL_MENU_8_PADS_PASS"
assert marker not in s
injected=r'''
                  // Replace direct Cell-Terminal-to-Crafting-Terminal adjacency
                  // by a REAL NETWORK CABLE. The original B1037 test never
                  // covered this path; only this path matches a remote build.
                  BlockPos xsxCablePos=xsxCellPos;
                  BlockPos xsxRemotePos=xsxCablePos.above();
                  if(!level.isEmptyBlock(xsxRemotePos))
                   throw new IllegalStateException("B1038 remote test space is occupied");
                  level.setBlock(xsxCablePos,ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState(),3);
                  level.setBlock(xsxRemotePos,ObsidianNetwork.V176_CELL_TERMINAL.get().defaultBlockState(),3);
                  if(!dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(level,xsxCablePos))
                   throw new IllegalStateException("B1038 physically placed cable lacks NETWORK signal");
                  var xsxRemoteScan=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(level,xsxRemotePos);
                  if(!xsxRemoteScan.online()||xsxRemoteScan.drives().size()!=50)
                   throw new IllegalStateException("B1038 remote Cell Terminal failed NETWORK cable path: online="+
                     xsxRemoteScan.online()+" drives="+xsxRemoteScan.drives().size()+
                     " free="+xsxRemoteScan.freeSlots());
                  if(!(level.getBlockEntity(xsxRemotePos)
                       instanceof dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity xsxRemoteBe))
                   throw new IllegalStateException("B1038 missing remote BE");
                  xsxBurstPlayer.setPos(xsxRemotePos.getX()+0.5D,
                    xsxRemotePos.getY()+0.5D,xsxRemotePos.getZ()+0.5D);
                  var xsxRemoteMenu=new dev.obsidiannetwork.cellterminal.V176CellTerminalMenu(
                       101,xsxPlayerInv,xsxRemoteBe);
                  // All 8 server-action pads must be real click targets, not
                  // phantom cells, while preserving the exact inserted Cell.
                  for(int pad=0;pad<8;pad++){
                   xsxBacking.setItem(xsxSlot,net.minecraft.world.item.ItemStack.EMPTY);
                   var liveScan=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(
                     level,xsxRemotePos);
                   if(!liveScan.online()||liveScan.freeSlots()!=1)
                    throw new IllegalStateException("B1038 connected free-slot disappeared pad="+pad+
                        " free="+liveScan.freeSlots()+" online="+liveScan.online());
                   if(!xsxRemoteMenu.slots.get(pad).isActive()
                     ||!xsxRemoteMenu.slots.get(pad).mayPlace(xsxOriginalCell)
                     ||xsxRemoteMenu.slots.get(pad).mayPickup(xsxBurstPlayer))
                    throw new IllegalStateException("B1038 GUI pad not an active Cell input "+pad);
                   xsxRemoteMenu.setCarried(xsxOriginalCell.copyWithCount(1));
                   xsxRemoteMenu.clicked(pad,0,net.minecraft.world.inventory.ContainerInput.PICKUP,xsxBurstPlayer);
                   if(!xsxRemoteMenu.getCarried().isEmpty()
                       ||!net.minecraft.world.item.ItemStack.matches(xsxBacking.getItem(xsxSlot),xsxOriginalCell)
                       ||!xsxRemoteMenu.slots.get(pad).getItem().isEmpty())
                    throw new IllegalStateException("B1038 real cable-linked cursor insert lost cell pad="+pad);
                  }
                  // Shift-click through same cable-connected route.
                  xsxBacking.setItem(xsxSlot,net.minecraft.world.item.ItemStack.EMPTY);
                  xsxPlayerInv.setItem(0,xsxOriginalCell.copyWithCount(1));
                  var xsxCableQuickMove=xsxRemoteMenu.quickMoveStack(xsxBurstPlayer,81);
                  if(xsxCableQuickMove.isEmpty()||!xsxPlayerInv.getItem(0).isEmpty()
                      ||!net.minecraft.world.item.ItemStack.matches(xsxBacking.getItem(xsxSlot),xsxOriginalCell))
                   throw new IllegalStateException("B1038 cable-shift-click failed");
                  // The source cell never appears in the virtual menu backing.
                  for(int i=0;i<54;i++)
                   if(!xsxRemoteMenu.slots.get(i).getItem().isEmpty())
                    throw new IllegalStateException("B1038 phantom Cell Terminal slot "+i);
                  // A physically disconnected ENERGY-only cable does not
                  // connect a cell network. Its attempted deposit must be
                  // rejected without consuming a player cell or filling drive.
                  level.setBlock(xsxCablePos,ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState(),3);
                  xsxBacking.setItem(xsxSlot,net.minecraft.world.item.ItemStack.EMPTY);
                  var xsxDisconnectedScan=dev.obsidiannetwork.cellterminal.V176CellTerminalTopology.scan(
                      level,xsxRemotePos);
                  if(xsxDisconnectedScan.online())
                   throw new IllegalStateException("B1038 ENERGY cable incorrectly joined NETWORK graph");
                  xsxRemoteMenu.setCarried(xsxOriginalCell.copyWithCount(1));
                  xsxRemoteMenu.clicked(0,0,net.minecraft.world.inventory.ContainerInput.PICKUP,xsxBurstPlayer);
                  if(!net.minecraft.world.item.ItemStack.matches(xsxRemoteMenu.getCarried(),xsxOriginalCell)
                      ||!xsxBacking.getItem(xsxSlot).isEmpty())
                   throw new IllegalStateException("B1038 disconnected cable consumed or installed a Cell");
                  // Restore the NETWORK wire and original real Drive slot so
                  // existing later 50-drive tests remain unchanged.
                  level.setBlock(xsxCablePos,ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState(),3);
                  xsxBacking.setItem(xsxSlot,xsxOriginalCell);
                  System.out.println("V176_B1038_REAL_CABLE_CELL_MENU_8_PADS_PASS"+
                    " connected_drives=50 pads=8 remote_cable=true shift_click=true"+
                    " disconnected_denied=true real_nbt=true no_phantom=true");
'''
s=s.replace(anchor,anchor+"\n"+injected,1)
assert s.count(marker)==1
p.write_text(s,encoding="utf-8")
print(marker+" INJECTED")
