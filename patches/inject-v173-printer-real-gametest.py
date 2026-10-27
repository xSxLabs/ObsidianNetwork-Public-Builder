#!/usr/bin/env python3
"""CI-only real BE Printer material extraction: exact and legacy 800-cell stacks."""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='                  // V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST: no mock cells.'
marker='V173_PRINTER_REAL_CANONICAL_MATERIALS_GAME_TEST PASS'
if s.count(anchor)!=1 or marker in s:
 raise RuntimeError("Printer live fixture drift or repeated injection")
java=r'''
                  // V173_PRINTER_REAL_CANONICAL_MATERIALS_GAME_TEST: real 800 cells,
                  // real printer BE + world placement. Validate both item key types.
                  try{
                   BlockPos xsxPrinterPos=h.absolutePos(new BlockPos(1,2,3));
                   BlockPos xsxPrinterCable=xsxPrinterPos.below();
                   BlockPos xsxPrinterDest=h.absolutePos(new BlockPos(1,3,3));
                   if(!level.getBlockState(xsxPrinterPos).isAir())
                     throw new IllegalStateException("Printer fixture position occupied: "+level.getBlockState(xsxPrinterPos));
                   if(!level.getBlockState(xsxPrinterDest).isAir())
                     throw new IllegalStateException("Printer fixture output occupied: "+level.getBlockState(xsxPrinterDest));
                   if(!level.getBlockState(xsxPrinterCable).is(ObsidianNetwork.CONDUIT_BUNDLE.get()))
                     throw new IllegalStateException("Printer fixture NETWORK bundle block missing");
                   if(dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForAccessory(level,xsxPrinterCable)!=rt)
                     throw new IllegalStateException("Printer fixture runtime mismatch on NETWORK bundle");
                   if(!level.setBlock(xsxPrinterPos,ObsidianNetwork.NETWORK_PRINTER.get().defaultBlockState(),3))
                     throw new IllegalStateException("Cannot place actual Network Printer");
                   if(!(level.getBlockEntity(xsxPrinterPos) instanceof
                         dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity xsxPrinter))
                     throw new IllegalStateException("Missing real Printer block entity");
                   var xsxPrinterCodec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
                   var xsxPrinterExact=xsxPrinterCodec.describe(new net.minecraft.world.item.ItemStack(
                         net.minecraft.world.item.Items.PURPUR_BLOCK));
                   var xsxPrinterLegacy=dev.obsidiannetwork.core.ItemKey.simple("minecraft:purpur_block");
                   if(xsxPrinterExact.key().equals(xsxPrinterLegacy)||
                      rt.storage().index().amount(xsxPrinterExact.key())!=0L||
                      rt.storage().index().amount(xsxPrinterLegacy)!=0L)
                     throw new IllegalStateException("Printer test expected empty, distinct PURPUR keys");
                   var xsxPrinterBlueprint=new net.minecraft.world.item.ItemStack(
                         ObsidianNetwork.NETWORK_BLUEPRINT.get());
                   dev.obsidiannetwork.item.NetworkBlueprintItem.write(
                     xsxPrinterBlueprint,"xsxlabs_blocks","minecraft:purpur_block");
                   dev.obsidiannetwork.item.NetworkBlueprintItem.write(
                     xsxPrinterBlueprint,"xsxlabs_size","1,1,1");
                   dev.obsidiannetwork.item.NetworkBlueprintItem.write(
                     xsxPrinterBlueprint,"xsxlabs_anchor",level.dimension().identifier()+"|"+
                     xsxPrinterDest.getX()+"|"+xsxPrinterDest.getY()+"|"+xsxPrinterDest.getZ());
                   var xsxEnergyField=dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity.class
                     .getDeclaredField("energyBuffer");
                   xsxEnergyField.setAccessible(true);
                   xsxEnergyField.setLong(xsxPrinter,249L);
                   var xsxPrint=dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity.class
                     .getDeclaredMethod("printer",net.minecraft.server.level.ServerLevel.class,
                                          dev.obsidiannetwork.core.NetworkRuntime.class);
                   xsxPrint.setAccessible(true);
                   // Negative gates on the actual BE: zero FE or missing network
                   // materials must never place blocks or consume even one FE.
                   xsxPrinter.setItem(0,xsxPrinterBlueprint.copy());
                   if(!xsxPrinter.control(0))
                     throw new IllegalStateException("Printer START rejected negative-gate Blueprint");
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(xsxEnergyField.getLong(xsxPrinter)!=249L||xsxPrinter.progress()!=0||
                      !xsxPrinter.status().contains("NO POWER")||
                      !level.getBlockState(xsxPrinterDest).isAir())
                     throw new IllegalStateException("Printer FE-starvation consumed power or altered world");
                   xsxEnergyField.setLong(xsxPrinter,1000L);
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(xsxEnergyField.getLong(xsxPrinter)!=1000L||xsxPrinter.progress()!=0||
                      !xsxPrinter.status().contains("MISSING")||
                      !level.getBlockState(xsxPrinterDest).isAir())
                     throw new IllegalStateException("Printer missing materials changed FE, world or progress");
                   rt.descriptors().registerKnown(xsxPrinterExact.key(),xsxPrinterExact.canonicalPayload());
                   if(rt.storage().insertExact(xsxPrinterExact.key(),xsxPrinterExact.canonicalPayload(),1L)!=1L)
                     throw new IllegalStateException("Failed to seed exact Printer material in real cells");
                   // Resume the previously started job when material arrives.
                   if(!xsxPrinter.status().contains("MISSING"))
                     throw new IllegalStateException("Printer missing-material pause did not persist");
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(!level.getBlockState(xsxPrinterDest).is(net.minecraft.world.level.block.Blocks.PURPUR_BLOCK)||
                      rt.storage().index().amount(xsxPrinterExact.key())!=0L||
                      rt.storage().index().amount(xsxPrinterLegacy)!=0L||
                      xsxEnergyField.getLong(xsxPrinter)!=750L||xsxPrinter.progress()!=1)
                     throw new IllegalStateException("Printer did not consume exact PURPUR item once and pay 250 FE");
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(!xsxPrinter.getItem(0).is(ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get()))
                     throw new IllegalStateException("Printer did not return Quill on successful completion");
                   level.removeBlock(xsxPrinterDest,false);
                   if(rt.storage().insert(xsxPrinterLegacy,1L)!=1L)
                     throw new IllegalStateException("Failed to seed pre-fix legacy Printer material");
                   // A protected/occupied target is NOT a skip. It must remain
                   // pending and must not consume the old-key material or FE.
                   if(!level.setBlock(xsxPrinterDest,
                         net.minecraft.world.level.block.Blocks.STONE.defaultBlockState(),3))
                     throw new IllegalStateException("Cannot stage blocked Printer target");
                   xsxPrinter.setItem(0,xsxPrinterBlueprint.copy());
                   if(!xsxPrinter.control(0))throw new IllegalStateException("Printer START rejected blocked Blueprint");
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(!level.getBlockState(xsxPrinterDest).is(net.minecraft.world.level.block.Blocks.STONE)||
                      !xsxPrinter.status().contains("BLOCKED")||xsxPrinter.progress()!=0||
                      rt.storage().index().amount(xsxPrinterLegacy)!=1L||
                      xsxEnergyField.getLong(xsxPrinter)!=750L)
                     throw new IllegalStateException("Printer blocked target skipped or consumed FE/material");
                   level.removeBlock(xsxPrinterDest,false);
                   System.out.println("V173_PRINTER_FAIL_CLOSED_GATES_GAME_TEST PASS"+
                       " no_power=true missing=true blocked=true FE_conserved=true items_conserved=true");
                   // Resume exactly the blocked operation on a now-empty target.
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(!level.getBlockState(xsxPrinterDest).is(net.minecraft.world.level.block.Blocks.PURPUR_BLOCK)||
                      rt.storage().index().amount(xsxPrinterExact.key())!=0L||
                      rt.storage().index().amount(xsxPrinterLegacy)!=0L||
                      xsxEnergyField.getLong(xsxPrinter)!=500L||xsxPrinter.progress()!=1)
                     throw new IllegalStateException("Printer legacy fallback duplicated, lost or refused item");
                   xsxPrint.invoke(xsxPrinter,level,rt);
                   if(!xsxPrinter.getItem(0).is(ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get()))
                     throw new IllegalStateException("Printer legacy completion failed");
                   xsxPrinter.setItem(0,net.minecraft.world.item.ItemStack.EMPTY);
                   level.removeBlock(xsxPrinterDest,false);
                   level.removeBlock(xsxPrinterPos,false);
                   System.out.println("V173_PRINTER_REAL_CANONICAL_MATERIALS_GAME_TEST PASS"+
                    " cells=800 physical_printer=true network_bundle=true exact=1 legacy=1"+
                    " FE_paid=500 no_duplication=true clean_fixture=true");
                  }catch(ReflectiveOperationException ex){
                   throw new IllegalStateException("Real Printer canonical material GameTest reflection failed",ex);
                  }
'''
p.write_text(s.replace(anchor,java+anchor,1),encoding="utf-8")
print("V173_PRINTER_REAL_CANONICAL_GAME_TEST_INJECTED")
