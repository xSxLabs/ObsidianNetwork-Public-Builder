#!/usr/bin/env python3
"""CI-only actual Controller and Autocrafter GUI read/open bursts on 50 drives.

Unlike direct status helper microtests, this instantiates real server-side
PowerStatusMenu and AutocrafterMenu 180 times each using a headless NeoForge FakePlayer
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
                  var xsxGuiPlayer=// Headless Curios tests must avoid GameTestHelper's login/network sync.
                  // NeoForge FakePlayer has a local inventory, but no client handshake.
                  net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level);
                  var xsxGuiInv=xsxGuiPlayer.getInventory();
                  long[] xsxControllerMenuTrials=new long[9];
                  long[] xsxAutocrafterMenuTrials=new long[9];
                  // Segment test timings; separate actual constructor cost from
                  // first snapshot reading and repeated cached status reads.
                  // No runtime modification, no synthetic MSPT attribution.
                  long[] xsxControllerCtorTrials=new long[9];
                  long[] xsxControllerStatusTrials=new long[9];
                  long[] xsxAutocrafterCtorTrials=new long[9];
                  long[] xsxAutocrafterStatusTrials=new long[9];
                  int xsxControllerOpens=0;
                  int xsxAutoOpens=0;
                  long xsxReadChecksum=0;
                  for(int trial=0;trial<9;trial++){
                    long controllerStart=System.nanoTime();
                    long constructorWork=0L, statusWork=0L;
                    for(int opening=0;opening<20;opening++){
                      long ctorBegin=System.nanoTime();
                      var menu=new dev.obsidiannetwork.menu.PowerStatusMenu(
                          73,xsxGuiInv,controller,false,level.getBlockEntity(controller));
                      constructorWork+=System.nanoTime()-ctorBegin;
                      long readBegin=System.nanoTime();
                      if(menu.drives()!=50)
                        throw new IllegalStateException("Controller GUI lost 50 attached drives");
                      if(menu.terminals()<1)
                        throw new IllegalStateException("Controller GUI cannot see real attached terminal");
                      if(menu.autocrafters()!=1)
                        throw new IllegalStateException("Controller GUI must see exactly one attached autocrafter");
                      for(int read=0;read<2;read++){
                        xsxReadChecksum+=menu.stored()+menu.capacity()+menu.drives()
                            +menu.terminals()+menu.autocrafters()+menu.activeJobs()
                            +menu.blockedJobs()+menu.templates()+menu.cables()
                            +menu.importers()+menu.exporters()+menu.templateCreators()
                            +menu.templateManagers()+menu.craftingMonitors()
                            +menu.wirelessAntennas()+menu.processingMachines();
                      }
                      statusWork+=System.nanoTime()-readBegin;
                      xsxControllerOpens++;
                    }
                    xsxControllerMenuTrials[trial]=System.nanoTime()-controllerStart;
                    xsxControllerCtorTrials[trial]=constructorWork;
                    xsxControllerStatusTrials[trial]=statusWork;
                    long autocrafterStart=System.nanoTime();
                    long autocrafterCtorWork=0L, autocrafterStatusWork=0L;
                    for(int opening=0;opening<20;opening++){
                      long autoCtorBegin=System.nanoTime();
                      var menu=new dev.obsidiannetwork.menu.AutocrafterMenu(
                          74,xsxGuiInv,xsxStressAutoPos);
                      autocrafterCtorWork+=System.nanoTime()-autoCtorBegin;
                      long autoReadBegin=System.nanoTime();
                      int active=menu.active();
                      int blocked=menu.blocked();
                      if(active<0||blocked<0)
                        throw new IllegalStateException("Autocrafter GUI negative job count");
                      xsxReadChecksum+=active+blocked+(menu.online()?1:0);
                      var first=menu.slots.get(0).getItem();
                      var again=menu.slots.get(0).getItem();
                      if(!net.minecraft.world.item.ItemStack.matches(first,again))
                        throw new IllegalStateException("Autocrafter menu preview changed inside one tick");
                      autocrafterStatusWork+=System.nanoTime()-autoReadBegin;
                      xsxAutoOpens++;
                    }
                    xsxAutocrafterMenuTrials[trial]=System.nanoTime()-autocrafterStart;
                    xsxAutocrafterCtorTrials[trial]=autocrafterCtorWork;
                    xsxAutocrafterStatusTrials[trial]=autocrafterStatusWork;
                  }
                  java.util.Arrays.sort(xsxControllerMenuTrials);
                  java.util.Arrays.sort(xsxAutocrafterMenuTrials);
                  java.util.Arrays.sort(xsxControllerCtorTrials);
                  java.util.Arrays.sort(xsxControllerStatusTrials);
                  java.util.Arrays.sort(xsxAutocrafterCtorTrials);
                  java.util.Arrays.sort(xsxAutocrafterStatusTrials);
                  if(xsxControllerOpens!=180||xsxAutoOpens!=180)
                    throw new IllegalStateException("Controller or Autocrafter GUI stress incomplete");
                  System.out.println("REAL_50_DRIVE_CONTROLLER_AUTOCRAFTER_GUI_OPEN_STRESS_V1 PASS"+
                    " drives=50 cells=800 controller_opens="+xsxControllerOpens+
                    " autocrafter_opens="+xsxAutoOpens+" controller_median_ns="+xsxControllerMenuTrials[4]+
                    " controller_p90_ns="+xsxControllerMenuTrials[8]+
                    " autocrafter_median_ns="+xsxAutocrafterMenuTrials[4]+
                    " autocrafter_p90_ns="+xsxAutocrafterMenuTrials[8]+
                    " read_checksum="+xsxReadChecksum+" not_server_MSPT=true");
                  // Individual trial elapsed times are for 20 menu opens, not
                  // full-server tick or client render timings.
                  System.out.println("REAL_50_DRIVE_GUI_PHASE_BREAKDOWN_V1 PASS"+
                    " controller_ctor_median_ns="+xsxControllerCtorTrials[4]+
                    " controller_ctor_p90_ns="+xsxControllerCtorTrials[8]+
                    " controller_status_median_ns="+xsxControllerStatusTrials[4]+
                    " controller_status_p90_ns="+xsxControllerStatusTrials[8]+
                    " autocrafter_ctor_median_ns="+xsxAutocrafterCtorTrials[4]+
                    " autocrafter_status_median_ns="+xsxAutocrafterStatusTrials[4]+
                    " batch_size=20 trials=9 uncontrolled=true not_server_MSPT=true");
                  // CI-only decomposition of the real Controller snapshot's
                  // public helper calls. No changes to production status logic
                  // or device power/FE budget. These are uncontrolled wall
                  // timings per 20 calls and should not be added to MSPT.
                  long[][] xsxSubcallTrials=new long[6][9];
                  long xsxSubcallCheck=0L;
                  for(int trial=0;trial<9;trial++){
                    for(int iteration=0;iteration<20;iteration++){
                      long begin=System.nanoTime();
                      var probeRt=dev.obsidiannetwork.network.WorldTopologyBridge
                          .runtimeForController(level,controller);
                      xsxSubcallTrials[0][trial]+=System.nanoTime()-begin;
                      if(probeRt!=rt)
                        throw new IllegalStateException("Controller subcall lost active runtime");
                      begin=System.nanoTime();
                      xsxSubcallCheck+=probeRt.drives().size();
                      xsxSubcallTrials[1][trial]+=System.nanoTime()-begin;
                      begin=System.nanoTime();
                      xsxSubcallCheck+=dev.obsidiannetwork.network.WorldTopologyBridge
                          .autocrafterCount(level,probeRt);
                      xsxSubcallTrials[2][trial]+=System.nanoTime()-begin;
                      begin=System.nanoTime();
                      xsxSubcallCheck+=dev.obsidiannetwork.network.WorldTopologyBridge
                          .autocraftingActiveJobs(level,probeRt);
                      xsxSubcallTrials[3][trial]+=System.nanoTime()-begin;
                      begin=System.nanoTime();
                      xsxSubcallCheck+=dev.obsidiannetwork.network.WorldTopologyBridge
                          .autocraftingBlockedJobs(level,probeRt);
                      xsxSubcallTrials[4][trial]+=System.nanoTime()-begin;
                      begin=System.nanoTime();
                      xsxSubcallCheck+=dev.obsidiannetwork.network.WorldTopologyBridge
                          .templatesForRuntime(level,probeRt).size();
                      xsxSubcallTrials[5][trial]+=System.nanoTime()-begin;
                    }
                  }
                  for(long[] probe:xsxSubcallTrials)java.util.Arrays.sort(probe);
                  if(xsxSubcallCheck<9000L)
                    throw new IllegalStateException("Controller subcall probe did not see 50 drives");
                  System.out.println("REAL_50_DRIVE_CONTROLLER_STATUS_SUBCALLS_V1 PASS"+
                    " runtime_lookup_median_ns="+xsxSubcallTrials[0][4]+
                    " drives_median_ns="+xsxSubcallTrials[1][4]+
                    " autocrafter_count_median_ns="+xsxSubcallTrials[2][4]+
                    " active_jobs_median_ns="+xsxSubcallTrials[3][4]+
                    " blocked_jobs_median_ns="+xsxSubcallTrials[4][4]+
                    " templates_median_ns="+xsxSubcallTrials[5][4]+
                    " sum_check="+xsxSubcallCheck+
                    " batch_size=20 trials=9 uncontrolled=true not_server_MSPT=true");
'''
out=s.replace(setup,setup+"\n"+setup_code,1).replace(attached,attached+"\n"+stress_code,1)
assert out.count(marker)==1
p.write_text(out,encoding="utf-8")
print("CONTROLLER_AUTOCRAFTER_50DRIVE_GUI_STRESS_TEST_ONLY_INJECTION_V1 PASS")
