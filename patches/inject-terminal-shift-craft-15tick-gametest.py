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
                  var xsxCraftPlayer=// Headless Curios tests must avoid GameTestHelper's login/network sync.
                  // NeoForge FakePlayer has a local inventory, but no client handshake.
                  net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level);
                  var xsxCraftInv=xsxCraftPlayer.getInventory();
                  var xsxCraftMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu(
                      93,xsxCraftInv,xsxlabsBurstTerminalPos,2L,2L);
                  rt.energy().load(rt.energy().capacity());
                  // ControllerRuntime.powered is a tick-updated state, not a direct EnergyBuffer read.
                  rt.tick();
                  if(!rt.powered())throw new IllegalStateException("Shift crafting test network unpowered");
                  final int[] xsxCraftTicks={0};
                  final long[] xsxCraftWorkNs=new long[15];
                  final int[] xsxLogsConsumed={0};
                  final int[] xsxPlanksReceived={0};
                  final int[] xsxBurstClicks={0};
                  final int[] xsxBurstReinserted={0};
                  final int[] xsxBurstUnspent={0};
                  // Keep craft-only timings independent from the additionally
                  // measured GUI work on each of the same 15 actual server ticks.
                  final long[] xsxMixedGuiNs=new long[15];
                  final int[] xsxMixedControllerOpens={0};
                  final int[] xsxMixedAutoOpens={0};
                  final long[] xsxMixedStatusChecksum={0L};
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
                          // The shared FakePlayer inventory may contain outputs from
                          // the nine-ingredient fixture; preserve unrelated stacks.
                          if(present.getItem()==net.minecraft.world.item.Items.OAK_PLANKS){
                            planks+=present.getCount();
                            xsxCraftInv.setItem(slot,net.minecraft.world.item.ItemStack.EMPTY);
                          }
                        }
                      }
                      if(planks!=64)
                        throw new IllegalStateException("Shift craft expected 64 planks, got "+planks);

                      // Try 24 more real result shift-clicks in the SAME tick.
                      // Reinsert eight additional logs so every attempt sees
                      // an available recipe. The per-tick cap must not make
                      // additional output, consume extra logs or duplicate it.
                      xsxCraftMenu.slots.get(1).set(new net.minecraft.world.item.ItemStack(
                          net.minecraft.world.item.Items.OAK_LOG,8));
                      var burstPreview=xsxCraftMenu.slots.get(0).getItem();
                      if(burstPreview.isEmpty()||burstPreview.getCount()!=4)
                        throw new IllegalStateException("Same-tick burst recipe was not available");
                      for(int burst=0;burst<24;burst++){
                        xsxCraftMenu.clicked(0,0,
                            net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
                      }
                      var unspent=xsxCraftMenu.slots.get(1).getItem();
                      if(unspent.isEmpty()||unspent.getItem()!=net.minecraft.world.item.Items.OAK_LOG
                          ||unspent.getCount()!=8)
                        throw new IllegalStateException("Same-tick shift-burst consumed extra logs");
                      for(int slot=0;slot<36;slot++){
                        if(xsxCraftInv.getItem(slot).getItem()==net.minecraft.world.item.Items.OAK_PLANKS)
                          throw new IllegalStateException("Same-tick shift-burst duplicated output");
                      }
                      int unspentCount=unspent.getCount();
                      xsxCraftMenu.slots.get(1).set(net.minecraft.world.item.ItemStack.EMPTY);
                      xsxBurstClicks[0]+=24;
                      xsxBurstReinserted[0]+=8;
                      xsxBurstUnspent[0]+=unspentCount;
                      xsxCraftTicks[0]++;
                      xsxLogsConsumed[0]+=16;
                      xsxPlanksReceived[0]+=planks;
                      xsxCraftWorkNs[xsxCraftTicks[0]-1]=System.nanoTime()-begin;

                      // XSXLABS_MIXED_CRAFT_GUI_15TICK_STRESS_V1: controller
                      // and autocrafter screens opened/queried under REAL
                      // shift-crafting + 24 extra same-tick shift-clicks.
                      // No synthetic storage, no test-only production patch.
                      long mixedStart=System.nanoTime();
                      for(int mix=0;mix<2;mix++){
                        var mixedController=new dev.obsidiannetwork.menu.PowerStatusMenu(
                            95,xsxCraftInv,controller,false,level.getBlockEntity(controller));
                        if(mixedController.drives()!=50||mixedController.terminals()<1||
                           mixedController.autocrafters()<1||
                           mixedController.activeJobs()<0||mixedController.blockedJobs()<0)
                          throw new IllegalStateException("Mixed GUI Controller network lost devices");
                        xsxMixedStatusChecksum[0]+=mixedController.drives()
                            +mixedController.terminals()+mixedController.autocrafters()
                            +mixedController.stored()+mixedController.capacity();
                        xsxMixedControllerOpens[0]++;
                        var mixedAuto=new dev.obsidiannetwork.menu.AutocrafterMenu(
                            96,xsxCraftInv,xsxStressAutoPos);
                        if(mixedAuto.active()<0||mixedAuto.blocked()<0)
                          throw new IllegalStateException("Mixed GUI Autocrafter status invalid");
                        var a=mixedAuto.slots.get(0).getItem();
                        var b=mixedAuto.slots.get(0).getItem();
                        if(!net.minecraft.world.item.ItemStack.matches(a,b))
                          throw new IllegalStateException("Mixed GUI preview mutated same tick");
                        xsxMixedStatusChecksum[0]+=mixedAuto.active()+mixedAuto.blocked()
                            +(mixedAuto.online()?1:0);
                        xsxMixedAutoOpens[0]++;
                      }
                      xsxMixedGuiNs[xsxCraftTicks[0]-1]=System.nanoTime()-mixedStart;
                    });
                  }
                  xsxCraftSequence.thenExecute(()->{
                    if(xsxCraftTicks[0]!=15||xsxLogsConsumed[0]!=240||xsxPlanksReceived[0]!=960)
                      throw new IllegalStateException("Terminal 15-tick shift-craft item conservation failed");
                    if(xsxBurstClicks[0]!=360||xsxBurstReinserted[0]!=120||
                       xsxBurstUnspent[0]!=120)
                      throw new IllegalStateException("Same-tick burst conservation/accounting mismatch");
                    if(xsxMixedControllerOpens[0]!=30||xsxMixedAutoOpens[0]!=30||
                       xsxMixedStatusChecksum[0]<=0L)
                      throw new IllegalStateException("Mixed craft+GUI count/checksum mismatch");
                    for(long elapsed : xsxMixedGuiNs)
                      if(elapsed<=0L)throw new IllegalStateException("Missing per-tick GUI work sample");
                    java.util.Arrays.sort(xsxMixedGuiNs);
                    java.util.Arrays.sort(xsxCraftWorkNs);
                    System.out.println("REAL_50_DRIVE_MIXED_CRAFT_GUI_15_TICKS_V1 PASS"+
                        " ticks=15 controller_opens="+xsxMixedControllerOpens[0]+
                        " autocrafter_opens="+xsxMixedAutoOpens[0]+
                        " controller_drive_count=50 cells=800"+
                        " gui_median_ns="+xsxMixedGuiNs[7]+
                        " gui_p95_ns="+xsxMixedGuiNs[14]+
                        " checksum="+xsxMixedStatusChecksum[0]+
                        " true_server_menu=true no_player_client=true not_server_MSPT=true");
                    System.out.println("REAL_50_DRIVE_TERMINAL_SAME_TICK_BURST_V1 PASS"+
                        " burst_clicks=360 reinserted_logs=120 unspent_logs=120"+
                        " no_duplicate_output=true true_server_menu=true not_server_MSPT=true");
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
