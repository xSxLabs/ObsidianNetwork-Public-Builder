#!/usr/bin/env python3
"""Test-only exercise real NeoForge BE craft-slot handler + 9-slot no-op stress.

Does not modify production classes. Executed after the TerminalInventoryBlockEntity
no-op patch on a real dedicated GameTest server; no claim about client GUI FPS.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);'
marker="REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS"
assert s.count(anchor)==1 and marker not in s
assert "REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS" in s, "Must inject after #287 menu test"
body=r'''
                  // Real NeoForge ItemStacksResourceHandler path behind the
                  // terminal BE setter: 9 slots, live components, changed
                  // counts and repeated identical grid persistence writes.
                  var persistenceProbe=new dev.obsidiannetwork.blockentity.TerminalInventoryBlockEntity(
                      controller,ObsidianNetwork.CRAFTING_TERMINAL.get().defaultBlockState());
                  for(int slot=0;slot<9;slot++){
                    var stack=new net.minecraft.world.item.ItemStack(
                        net.minecraft.world.item.Items.COBBLESTONE,slot+1);
                    persistenceProbe.setCraftItem(slot,stack);
                    if(!net.minecraft.world.item.ItemStack.matches(persistenceProbe.getCraftItem(slot),stack))
                      throw new IllegalStateException("Terminal probe initial slot mismatch "+slot);
                  }
                  var special=new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND_PICKAXE);
                  special.set(net.minecraft.core.component.DataComponents.DAMAGE,9);
                  persistenceProbe.setCraftItem(8,special);
                  long persistStart=System.nanoTime();
                  int exactNoops=0;
                  for(int round=0;round<500;round++)for(int slot=0;slot<9;slot++){
                    var original=persistenceProbe.getCraftItem(slot);
                    var exact=original.copy();
                    persistenceProbe.setCraftItem(slot,exact);
                    if(!net.minecraft.world.item.ItemStack.matches(original,persistenceProbe.getCraftItem(slot)))
                      throw new IllegalStateException("Repeated terminal write changed slot "+slot+" at "+round);
                    exactNoops++;
                  }
                  var changedCount=new net.minecraft.world.item.ItemStack(
                      net.minecraft.world.item.Items.COBBLESTONE,43);
                  persistenceProbe.setCraftItem(0,changedCount);
                  if(!net.minecraft.world.item.ItemStack.matches(changedCount,persistenceProbe.getCraftItem(0)))
                    throw new IllegalStateException("Terminal changed count was incorrectly treated as no-op");
                  var changedComponent=special.copy();
                  changedComponent.set(net.minecraft.core.component.DataComponents.DAMAGE,10);
                  persistenceProbe.setCraftItem(8,changedComponent);
                  if(!net.minecraft.world.item.ItemStack.matches(changedComponent,persistenceProbe.getCraftItem(8)))
                    throw new IllegalStateException("Terminal changed tool components were incorrectly treated as no-op");
                  for(int slot=1;slot<8;slot++){
                    if(persistenceProbe.getCraftItem(slot).getCount()!=slot+1)
                      throw new IllegalStateException("Terminal unrelated craft slot mutated "+slot);
                  }
                  persistenceProbe.setCraftItem(7,net.minecraft.world.item.ItemStack.EMPTY);
                  if(!persistenceProbe.getCraftItem(7).isEmpty())
                    throw new IllegalStateException("Terminal clear-to-empty was incorrectly suppressed");
                  System.out.println("REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS"+
                      " identical_calls="+exactNoops+" slots=9"+
                      " changed_count=true changed_components=true clear=true"+
                      " total_ns="+(System.nanoTime()-persistStart)+" not_server_MSPT=true");
'''
new=s.replace(anchor,anchor+"\n"+body,1)
assert new.count(marker)==1
p.write_text(new,encoding="utf-8")
print("TERMINAL_CRAFT_SLOT_REAL_BESTACK_TEST_ONLY_INJECTION_V1 PASS")
