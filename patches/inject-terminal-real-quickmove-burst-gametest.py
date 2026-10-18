#!/usr/bin/env python3
"""CI-only real StorageTerminalMenu quick-move burst on 50-drive 800-cell network.

Compared with direct StorageNetwork.insert() microbenchmarks this invokes the
actual ServerPlayer inventory slot, ItemStackCodec, descriptor registry and
StorageTerminalMenu.quickMoveStack 80 times. Every cycle checks source zero,
exact destination delta and full recovery after network extraction. The GameTest
runs postpatch only; it is not a player FPS or p95/p99 tick benchmark.
"""
from pathlib import Path
import os

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
setup='if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");'
attached='if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);'
marker="REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS"
assert s.count(setup)==1 and s.count(attached)==1 and marker not in s
for guard in ("REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS",
              "REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS",
              "DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS"):
    assert guard in s, "Expected postpatch real-game gate missing: "+guard
setup_code=r'''
                // Connect the REAL Crafting Terminal to the existing NETWORK cable
                // at x=1,z=1; do not create a synthetic StorageNetwork.
                BlockPos xsxlabsBurstTerminalPos=h.absolutePos(new BlockPos(1,2,1));
                level.setBlock(xsxlabsBurstTerminalPos,
                    ObsidianNetwork.CRAFTING_TERMINAL.get().defaultBlockState(),3);
                if(!(level.getBlockEntity(xsxlabsBurstTerminalPos)
                     instanceof dev.obsidiannetwork.blockentity.TerminalInventoryBlockEntity))
                  throw new IllegalStateException("Crafting Terminal game BE not registered");
'''
burst_code=r'''
                  // ServerPlayer inventory -> real menu -> exact codec -> full
                  // 50-drive storage -> extraction/rollback. Never accept partial
                  // or duplicated insertions as success.
                  var xsxTerminalRt=dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForTerminal(
                      level,xsxlabsBurstTerminalPos);
                  if(xsxTerminalRt!=rt)
                    throw new IllegalStateException("Actual Crafting Terminal not attached to full network");
                  var xsxBurstPlayer=h.makeMockServerPlayerInLevel();
                  var xsxPlayerInv=xsxBurstPlayer.getInventory();
                  var xsxMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu(
                      61,xsxPlayerInv,xsxlabsBurstTerminalPos,1L,1L);
                  // Use the exact same canonical descriptor as StorageTerminalMenu.quickMoveStack.
                  // ItemKey.simple() need not equal an ItemStackCodec key, even for vanilla items.
                  var xsxBurstKey=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(
                      level.registryAccess()).describe(new net.minecraft.world.item.ItemStack(
                          net.minecraft.world.item.Items.COBBLESTONE,64)).key();
                  long xsxBefore=rt.storage().cells().stream().mapToLong(c->c.amount(xsxBurstKey)).sum();
                  // The headless test network has no generator: power only the
                  // test fixture; normal energy policy / 20Hz ticks stay intact.
                  rt.energy().load(rt.energy().capacity());
                  // ControllerRuntime.powered is a tick-updated state, not a direct EnergyBuffer read.
                  rt.tick();
                  if(!rt.powered())throw new IllegalStateException("Full test network did not power up");
                  long[] xsxBurstTimes=new long[9];
                  int xsxOperations=0;
                  for(int trial=0;trial<xsxBurstTimes.length;trial++){
                    long beginBurst=System.nanoTime();
                    for(int cycle=0;cycle<80;cycle++){
                      var stack=new net.minecraft.world.item.ItemStack(
                          net.minecraft.world.item.Items.COBBLESTONE,64);
                      xsxPlayerInv.setItem(0,stack);
                      // PLAYER_START=10, main inventory slots 9..35 followed by hotbar 0..8.
                      var moved=xsxMenu.quickMoveStack(xsxBurstPlayer,37);
                      if(moved.isEmpty()||moved.getCount()!=64||!xsxPlayerInv.getItem(0).isEmpty())
                        throw new IllegalStateException("Terminal quick-move did not deposit all 64 at "+
                          trial+":"+cycle);
                      long inStorage=rt.storage().cells().stream()
                          .mapToLong(c->c.amount(xsxBurstKey)).sum();
                      if(inStorage!=xsxBefore+64)
                        throw new IllegalStateException("Terminal quick-move item loss/duplication at "+
                          trial+":"+cycle+" got "+inStorage+" before="+xsxBefore);
                      if(rt.storage().extract(xsxBurstKey,64L)!=64L)
                        throw new IllegalStateException("Terminal test rollback extract lost items");
                      xsxOperations++;
                    }
                    xsxBurstTimes[trial]=System.nanoTime()-beginBurst;
                  }
                  java.util.Arrays.sort(xsxBurstTimes);
                  if(xsxOperations!=720||rt.storage().cells().stream()
                         .mapToLong(c->c.amount(xsxBurstKey)).sum()!=xsxBefore)
                    throw new IllegalStateException("720 real quick moves failed complete conservation");
                  System.out.println("REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS"+
                      " moves=720 exact_items=46080 drives=50 cells=800"+
                      " median_trial_ns="+xsxBurstTimes[4]+" p90_trial_ns="+xsxBurstTimes[8]+
                      " true_server_menu=true not_server_MSPT=true");
'''
updated=s.replace(setup,setup+"\n"+setup_code,1).replace(attached,attached+"\n"+burst_code,1)
assert updated.count(marker)==1
assert updated.count("var xsxMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu(")==1
p.write_text(updated,encoding="utf-8")
print("REAL_CRAFTING_TERMINAL_QUICKMOVE_BURST_TEST_ONLY_INJECTION_V1 PASS")
