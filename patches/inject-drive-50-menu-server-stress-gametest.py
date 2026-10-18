#!/usr/bin/env python3
"""CI-only: repeatedly open the real DriveMenu backing container for 50 drives.

Runs strictly POST-optimization on the 50-drive GameTest. This probes
actual compiled server Menu-backed reads of all 800 occupied cell slots,
including 8..15, without fabricating a client renderer or claiming MSPT.
No production classes or persistence files are changed. Does NOT by itself
prove real player GUI latency or solve rapid crafting/terminal deposits.
"""
from pathlib import Path
import os

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
source=path.read_text(encoding="utf-8")
anchor='if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);'
marker="REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1"
assert source.count(anchor)==1, "50-drive attached fixture changed"
assert marker not in source, "Duplicate menu stress probe"
assert source.count('if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");')==1
assert 'DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS' in source, "Run AFTER 16-slot menu patch/test injection"
assert 'DRIVE_GUI_LOWER_EIGHT_CELL_ROUNDTRIP_V1 PASS' in source
assert "rt.storage().cells().size()!=800" in source, "Full real storage binding missing"

addition=r'''
                  // Server-side GUI backing stress (not FPS / full MSPT).
                  // Each distinct menu allocates its own read cache. Verify
                  // 16 physical slots and two repeated reads per slot,
                  // including the previously lost lower eight slots.
                  try {
                    var klass=Class.forName("dev.obsidiannetwork.menu.DriveMenu$DriveContainer");
                    var construct=klass.getDeclaredConstructor(
                        dev.obsidiannetwork.blockentity.StorageDriveBlockEntity.class);
                    construct.setAccessible(true);
                    long[] menuTrials=new long[9];
                    int menuOpens=0;
                    int menuReads=0;
                    for(int trial=0;trial<menuTrials.length;trial++){
                      long begin=System.nanoTime();
                      for(int z=1;z<=10;z++)for(int x=2;x<=6;x++){
                        var be=(dev.obsidiannetwork.blockentity.StorageDriveBlockEntity)
                            level.getBlockEntity(h.absolutePos(new BlockPos(x,2,z)));
                        if(be==null)throw new IllegalStateException("50-drive backing missing at "+x+","+z);
                        var backing=(net.minecraft.world.Container)construct.newInstance(be);
                        if(backing.getContainerSize()!=16)
                          throw new IllegalStateException("50-drive menu exposed "+backing.getContainerSize()+" slots");
                        menuOpens++;
                        for(int slot=0;slot<16;slot++){
                          var first=backing.getItem(slot);
                          var again=backing.getItem(slot);
                          if(first.isEmpty()||!net.minecraft.world.item.ItemStack.matches(first,again))
                            throw new IllegalStateException("50-drive repeated GUI read changed slot "+slot);
                          menuReads+=2;
                        }
                        if(be.occupiedSlots()!=16)
                          throw new IllegalStateException("50-drive server GUI read corrupted occupancy");
                      }
                      menuTrials[trial]=System.nanoTime()-begin;
                    }
                    java.util.Arrays.sort(menuTrials);
                    if(menuOpens!=450||menuReads!=14400)
                      throw new IllegalStateException("Incomplete 50-drive GUI stress probe: "+menuOpens+"/"+menuReads);
                    System.out.println("REAL_50_DRIVE_MENU_SERVER_READ_STRESS_V1 PASS drives=50 slots=800"+
                        " opens=450 reads=14400 trials=9 median_ns="+menuTrials[4]+
                        " p90_ns="+menuTrials[8]+" no_client_renderer=true not_server_MSPT=true");
                  }catch(ReflectiveOperationException e){
                    throw new IllegalStateException("Cannot exercise the real 16-slot DriveContainer",e);
                  }
'''
updated=source.replace(anchor,anchor+"\n"+addition,1)
assert updated.count(marker)==2, "Expected one source marker and one log marker"
assert updated.count('if(attached!=50)throw new IllegalStateException("Expected 50 real drives, got "+attached);')==1
path.write_text(updated, encoding="utf-8")
print("DRIVE_50_MENU_SERVER_STRESS_TEST_ONLY_INJECTION_V1 PASS")
