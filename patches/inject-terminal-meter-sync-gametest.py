#!/usr/bin/env python3
"""Check actual menu-backed 64-bit capacity synchronization on the 50-drive fixture.

This is a GameTest-only assertion: uses the same real StorageTerminalMenu,
attached NetworkRuntime and player inventory as the existing quick-move burst.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(!rt.powered())throw new IllegalStateException("Full test network did not power up");'
marker="REAL_50_DRIVE_TERMINAL_STORAGE_METER_SYNC_V1"
assert s.count(anchor)==1,"Real full-network terminal opening moved"
assert "var xsxMenu=new dev.obsidiannetwork.menu.StorageTerminalMenu(" in s
assert marker not in s
check=r"""
                  // REAL_50_DRIVE_TERMINAL_STORAGE_METER_SYNC_V1
                  // Exercise menu ContainerData on actual server, including all
                  // 8 x 16-bit fields and 50 drives x 16 cells.
                  xsxMenu.broadcastChanges();
                  long[] expectedMeter=rt.storage().xsxStorageMeterTotals();
                  if(xsxMenu.xsxStorageUsed()!=expectedMeter[0] ||
                     xsxMenu.xsxStorageCapacity()!=expectedMeter[1] ||
                     expectedMeter[1]<=0L)
                    throw new IllegalStateException("Crafting Terminal synced used/total doesn't match attached 50-drive capacity "+
                      xsxMenu.xsxStorageUsed()+"/"+xsxMenu.xsxStorageCapacity()+
                      " expected "+expectedMeter[0]+"/"+expectedMeter[1]);
                  System.out.println("REAL_50_DRIVE_TERMINAL_STORAGE_METER_SYNC_V1 PASS used="+
                    expectedMeter[0]+" capacity="+expectedMeter[1]);
"""
p.write_text(s.replace(anchor,anchor+"\n"+check,1),encoding="utf-8")
print(marker+" INJECTED")
