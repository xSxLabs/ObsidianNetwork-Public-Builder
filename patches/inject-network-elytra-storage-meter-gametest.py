#!/usr/bin/env python3
"""Build-only runtime GameTest assertions for Network Elytra and 50-drive live storage totals.

This augments the existing 50-drive GameTest without changing stored cells,
reservations or attached topology. It must never be shipped inside the JAR.
"""
from pathlib import Path
import os

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(insertedCells!=800)throw new IllegalStateException("Expected 800 real cells");'
mark="NETWORK_ELYTRA_AND_LIVE_STORAGE_50_DRIVE_GAMETEST_V1"
assert s.count(anchor)==1,"50-drive exact attachment guard moved"
assert mark not in s,"feature gate injected twice"
# The fixture's rt is an actual powered network containing 50 real drives, 800
# actual attached storage cells, each with its own full 16-slot inventory.
code=r"""
                  // NETWORK_ELYTRA_AND_LIVE_STORAGE_50_DRIVE_GAMETEST_V1
                  {
                    long[] meter = rt.storage().xsxStorageMeterTotals();
                    long actualUsed=0L,actualTotal=0L;
                    int attached=0;
                    for(var cell : rt.storage().cells()) {
                      actualUsed+=cell.used();
                      actualTotal+=cell.used()+cell.free();
                      attached++;
                    }
                    if(attached!=800 || meter[0]!=actualUsed ||
                        meter[1]!=actualTotal || meter[1]<=0 ||
                        meter[0]>meter[1])
                       throw new IllegalStateException("Live terminal meter mismatch on 50 drives/800 cells: "+
                          attached+" "+meter[0]+"/"+meter[1]+" expected "+actualUsed+"/"+actualTotal);
                    var wings = new net.minecraft.world.item.ItemStack(ObsidianNetwork.NETWORK_ELYTRA.get());
                    if(!wings.has(net.minecraft.core.component.DataComponents.EQUIPPABLE) ||
                       !wings.has(net.minecraft.core.component.DataComponents.GLIDER) ||
                       !wings.has(net.minecraft.core.component.DataComponents.UNBREAKABLE))
                      throw new IllegalStateException("Network Elytra missing vanilla glider/chest/unbreakable component");
                    if(!dev.obsidiannetwork.core.EnergyTool.upgraded(wings) ||
                       dev.obsidiannetwork.core.EnergyTool.energy(wings)!=0L)
                      throw new IllegalStateException("Network Elytra initial FE marker/empty state incorrect");
                    long max=dev.obsidiannetwork.core.EnergyTool.capacity(wings);
                    if(max!=2000000L)throw new IllegalStateException("Network Elytra capacity "+max);
                    dev.obsidiannetwork.core.EnergyTool.setEnergy(wings,max);
                    if(!dev.obsidiannetwork.core.EnergyTool.consume(wings,1500L) ||
                       dev.obsidiannetwork.core.EnergyTool.energy(wings)!=max-1500L ||
                       wings.getDamageValue()!=0)
                      throw new IllegalStateException("Network Elytra FE consumption must not damage item");
                    System.out.println("NETWORK_ELYTRA_AND_LIVE_STORAGE_50_DRIVE_GAMETEST_V1 PASS cells="+attached+
                       " used="+meter[0]+" capacity="+meter[1]+" elytraFE="+max);
                  }
"""
p.write_text(s.replace(anchor,anchor+"\n"+code,1),encoding="utf-8")
print(mark+" INJECTED")
