#!/usr/bin/env python3
"""CI-only real 15-tick shift-crafting burst on 50-drive Crafting Terminal.

Exercises 1x1 oak log -> 4 oak planks vanilla crafting via live server menu
clicked(RESULT_SLOT, QUICK_MOVE) with a ServerPlayer every game tick, rather
than directly invoking recipe match or storage insert. Count every consumed
log and returned plank; fail closed for missing earlier quick-move/GUI probes.
Not a replacement for full Spark p95/p99 server metrics or client rendering.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
attached='if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);'
marker="REAL_50_DRIVE_TERMINAL_SHIFT_CRAFT_15_TICKS_V1 PASS"
assert s.count(attached)==1 and marker not in s
for need in (
   "REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS",
   "REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS",
   "REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS",
   "xsxlabsBurstTerminalPos"
):
    assert need in s, "Required existing GameTest fixture missing "+need

code=r'''
                  // Actual Shift-click crafting (not synthetic recipe matching).
                  // Vanilla oak log -> four planks, 16 crafts = 64 planks/tick.
                  // Run on 15 separate real server ticks to exercise the
                  // menu's intended per-tick 64-item shift output limit.
                  var xsxCraftPlayer=h.makeMockServerPlayerInLevel();
                  var xsxCraftInv=xsxCraftPlayer.getInventory();
                  var xsxCraftMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu(
                      93,xsxCraftInv,xsxlabsBurstTerminalPos,2L,2L);
                  rt.energy().load(rt.energy().capacity());
                  if(!rt.powered())throw new IllegalStateException("Shift crafting test network unpowered");
                  final int[] xsxCraftTicks={0};
                  final long[] xsxCraftWorkNs=new long[15];
                  final int[] xsxLogsConsumed={0};
                  final int[] xsxPlanksReceived={0};
                  var xsxCraftSequence=h.startSequence();
                  for(int tick=0;tick<15;tick++){
                    xsxCraftSequence.thenExecuteAfter(1,()->{
                      long begin=System.nanoTime();
                      xsxCraftMenu.slots.get(1).set(new net.minecraft.world.item.ItemStack(
                          net.minecraft.world.item.Items.OAK_LOG,16));
                      var preview=xsxCraftMenu.slots.get(0).getItem();
                      if(preview.isEmpty()||preview.getItem()!=net.minecraft.world.item.Items.OAK_PLANKS
                          ||preview.getCount()!=4)
                        throw new IllegalStateException("Vanilla log recipe missing on full terminal grid");
                      xsxCraftMenu.clicked(0,0,
                          net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
                      if(!xsxCraftMenu.slots.get(1).getItem().isEmpty())
                        throw new IllegalStateException("Shift craft failed to consume all sixteen input logs");
                      int planks=0;
                      for(int slot=0;slot<36;slot++){
                        var present=xsxCraftInv.getItem(slot);
                        if(!present.isEmpty()){
                          if(present.getItem()!=net.minecraft.world.item.Items.OAK_PLANKS)
                            throw new IllegalStateException("Unexpected shift-crafted inventory item at "+slot);
                          planks+=present.getCount();
                          xsxCraftInv.setItem(slot,net.minecraft.world.item.ItemStack.EMPTY);
                        }
                      }
                      if(planks!=64)
                        throw new IllegalStateException("Shift craft expected 64 planks, got "+planks);
                      xsxCraftTicks[0]++;
                      xsxLogsConsumed[0]+=16;
                      xsxPlanksReceived[0]+=planks;
                      xsxCraftWorkNs[xsxCraftTicks[0]-1]=System.nanoTime()-begin;
                    });
                  }
                  xsxCraftSequence.thenExecute(()->{
                    if(xsxCraftTicks[0]!=15||xsxLogsConsumed[0]!=240||xsxPlanksReceived[0]!=960)
                      throw new IllegalStateException("Terminal 15-tick shift-craft item conservation failed");
                    java.util.Arrays.sort(xsxCraftWorkNs);
                    System.out.println("REAL_50_DRIVE_TERMINAL_SHIFT_CRAFT_15_TICKS_V1 PASS"+
                        " ticks=15 input_logs=240 output_planks=960"+
                        " median_craft_work_ns="+xsxCraftWorkNs[7]+
                        " p95_craft_work_ns="+xsxCraftWorkNs[14]+
                        " true_server_menu=true not_server_MSPT=true");
                  });
'''
out=s.replace(attached,attached+"\n"+code,1)
assert out.count(marker)==1
p.write_text(out,encoding="utf-8")
print("SHIFT_CRAFT_TRUE_MENU_15_TICK_STRESS_TEST_ONLY_INJECTION_V1 PASS")
