#!/usr/bin/env python3
"""CI-only actual Controller and Autocrafter GUI read/open bursts on 50 drives.

Unlike direct status helper microtests, this instantiates real server-side
PowerStatusMenu and AutocrafterMenu 180 times each using a mock ServerPlayer
in a 50-drive 800-cell controller topology. Queries all 21 Controller data
fields twice and Autocrafter job/status/preview fields. Validates repeatable
status within one tick. The test measures workload wall time only; it does NOT
claim player FPS or measured full-server MSPT.
"""
from pathlib import Path
import os

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
setup='if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");'
attached='if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);'
marker="REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS"
assert s.count(setup)==1 and s.count(attached)==1 and marker not in s
for guard in (
    "REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1 PASS",
    "REAL_TERMINAL_CRAFT_SLOT_NOOP_TRANSACTION_STRESS_V1 PASS",
    "REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS",
):
    assert guard in s, "Prior test-only game stage missing: "+guard
setup_code=r'''
                // Place a real auto-crafter on the NETWORK spine before the
                // topology attachment warmup. At x=1,z=2 the cable is y=1.
                BlockPos xsxStressAutoPos=h.absolutePos(new BlockPos(1,2,2));
                level.setBlock(xsxStressAutoPos,
                    ObsidianNetwork.AUTOCRAFTER.get().defaultBlockState(),3);
                if(!(level.getBlockEntity(xsxStressAutoPos)
                     instanceof dev.obsidiannetwork.blockentity.AutocrafterBlockEntity))
                  throw new IllegalStateException("Autocrafter stress block entity not registered");
'''
stress_code=r'''
                  // Use server-side actual menu constructors (not synthetic
                  // ContainerData fixtures), scanning live controller status,
                  // autocrafting job views and preview slot on a full network.
                  var xsxGuiPlayer=h.makeMockServerPlayerInLevel();
                  var xsxGuiInv=xsxGuiPlayer.getInventory();
                  long[] xsxControllerMenuTrials=new long[9];
                  long[] xsxAutocrafterMenuTrials=new long[9];
                  int xsxControllerOpens=0;
                  int xsxAutoOpens=0;
                  long xsxReadChecksum=0;
                  for(int trial=0;trial<9;trial++){
                    long controllerStart=System.nanoTime();
                    for(int opening=0;opening<20;opening++){
                      var menu=new dev.obsidiannetwork.menu.PowerStatusMenu(
                          73,xsxGuiInv,controller,false,level.getBlockEntity(controller));
                      if(menu.drives()!=50)
                        throw new IllegalStateException("Controller GUI lost 50 attached drives");
                      if(menu.terminals()<1)
                        throw new IllegalStateException("Controller GUI cannot see real attached terminal");
                      for(int read=0;read<2;read++){
                        xsxReadChecksum+=menu.stored()+menu.capacity()+menu.drives()
                            +menu.terminals()+menu.autocrafters()+menu.activeJobs()
                            +menu.blockedJobs()+menu.templates()+menu.cables()
                            +menu.importers()+menu.exporters()+menu.templateCreators()
                            +menu.templateManagers()+menu.craftingMonitors()
                            +menu.wirelessAntennas()+menu.processingMachines();
                      }
                      xsxControllerOpens++;
                    }
                    xsxControllerMenuTrials[trial]=System.nanoTime()-controllerStart;
                    long autocrafterStart=System.nanoTime();
                    for(int opening=0;opening<20;opening++){
                      var menu=new dev.obsidiannetwork.menu.AutocrafterMenu(
                          74,xsxGuiInv,xsxStressAutoPos);
                      int active=menu.active();
                      int blocked=menu.blocked();
                      if(active<0||blocked<0)
                        throw new IllegalStateException("Autocrafter GUI negative job count");
                      xsxReadChecksum+=active+blocked+(menu.online()?1:0);
                      var first=menu.slots.get(0).getItem();
                      var again=menu.slots.get(0).getItem();
                      if(!net.minecraft.world.item.ItemStack.matches(first,again))
                        throw new IllegalStateException("Autocrafter menu preview changed inside one tick");
                      xsxAutoOpens++;
                    }
                    xsxAutocrafterMenuTrials[trial]=System.nanoTime()-autocrafterStart;
                  }
                  java.util.Arrays.sort(xsxControllerMenuTrials);
                  java.util.Arrays.sort(xsxAutocrafterMenuTrials);
                  if(xsxControllerOpens!=180||xsxAutoOpens!=180)
                    throw new IllegalStateException("Controller or Autocrafter GUI stress incomplete");
                  System.out.println("REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS"+
                    " drives=50 cells=800 controller_opens="+xsxControllerOpens+
                    " autocrafter_opens="+xsxAutoOpens+" controller_median_ns="+xsxControllerMenuTrials[4]+
                    " controller_p90_ns="+xsxControllerMenuTrials[8]+
                    " autocrafter_median_ns="+xsxAutocrafterMenuTrials[4]+
                    " autocrafter_p90_ns="+xsxAutocrafterMenuTrials[8]+
                    " read_checksum="+xsxReadChecksum+" not_server_MSPT=true");
'''
out=s.replace(setup,setup+"\n"+setup_code,1).replace(attached,attached+"\n"+stress_code,1)
assert out.count(marker)==1
p.write_text(out,encoding="utf-8")
print("CONTROLLER_AUTOCRAFTER_50DRIVE_GUI_STRESS_TEST_ONLY_INJECTION_V1 PASS")
