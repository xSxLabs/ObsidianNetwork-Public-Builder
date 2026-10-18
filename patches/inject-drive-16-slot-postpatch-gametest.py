#!/usr/bin/env python3
"""Add the real 16-slot DriveMenu check only to post-patch GameTests.

The baseline intentionally tests original code, which still has an 8-slot GUI.
Never change stored inventory data or shipped runtime classes.
"""
import os
from pathlib import Path

path = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/build103/Build103GameTests.java"
source = path.read_text(encoding="utf-8")
anchor = "if(insertedCells!=800)throw new IllegalStateException(\"Expected 800 real cells\");"
assert source.count(anchor) == 1, "50-drive fixture changed"
assert "DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1" not in source, "duplicate drive assertion"
assert "h.startSequence().thenExecuteAfter(50,()->{" in source, "50-drive continuation missing"
addition = "                // #274 regression: 16 real occupied slots are readable via the\n                // actual private DriveMenu backing Container, not only via BE.\n                // Old GUI-cache regression reported 8 and concealed slots 8..15.\n                try {\n                  var first=(dev.obsidiannetwork.blockentity.StorageDriveBlockEntity)\n                     level.getBlockEntity(h.absolutePos(new BlockPos(2,2,1)));\n                  if(first==null)throw new IllegalStateException(\"Missing complete drive fixture\");\n                  Class<?> cls=Class.forName(\"dev.obsidiannetwork.menu.DriveMenu$DriveContainer\");\n                  var ctr=cls.getDeclaredConstructor(dev.obsidiannetwork.blockentity.StorageDriveBlockEntity.class);\n                  ctr.setAccessible(true);\n                  var backing=(net.minecraft.world.Container)ctr.newInstance(first);\n                  if(backing.getContainerSize()!=16)\n                     throw new IllegalStateException(\"Drive GUI backing container truncated to \"+backing.getContainerSize());\n                  for(int slot=0;slot<16;slot++){\n                     var visible=backing.getItem(slot);\n                     if(visible.isEmpty())throw new IllegalStateException(\"Drive cell invisible at \"+slot);\n                  }\n                  if(first.occupiedSlots()!=16)throw new IllegalStateException(\"Reading GUI lost original cell\");\n                  System.out.println(\"DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS\");\n                }catch(ReflectiveOperationException ex){\n                  throw new IllegalStateException(\"Cannot inspect actual drive GUI 16-slot container\",ex);\n                }\n"
assert addition.count("DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS") == 1
assert "backing.getContainerSize()!=16" in addition
assert "for(int slot=0;slot<16;slot++)" in addition
source = source.replace(anchor, anchor + "\n" + addition.rstrip("\n"), 1)
assert source.count("DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS") == 1
path.write_text(source, encoding="utf-8")
print("DRIVE_POSTPATCH_16_CELL_GAMETEST_INJECTION_V1 PASS")
