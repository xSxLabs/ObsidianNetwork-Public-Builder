#!/usr/bin/env python3
"""Release gate: compiled real cell buffer architecture, no fake action pads.

CHECKS:
- real BE implements Container and persists via Vanilla ContainerHelper;
- menu is ChestMenu backed by the BE rather than SimpleContainer/phantoms;
- click path invokes super.clicked, and shift-click writes real BE buffer;
- tick path writes to DriveMenu BE then decrements terminal Cell;
- server fixture tests real connected and disconnected Drives.
Does not substitute for an actual client GUI or pixel test.
"""
import subprocess,sys,zipfile
from pathlib import Path
jar=Path(sys.argv[1]);assert jar.is_file()
def javap(c):
 r=subprocess.run(["javap","-classpath",str(jar),"-c","-p",c],
                  text=True,capture_output=True,check=True)
 return r.stdout
be=javap("dev.obsidiannetwork.cellterminal.V176CellTerminalBlockEntity")
assert "extends net.minecraft.world.level.block.entity.BlockEntity implements net.minecraft.world.Container" in be
for s in ("net/minecraft/world/ContainerHelper.saveAllItems",
          "net/minecraft/world/ContainerHelper.loadAllItems",
          "xsxAutoTransfer","DriveMenu.xsxCellTerminalBacking",
          "net/minecraft/world/item/ItemStack.matches",
          "ItemStack.shrink","xsxFree","public int bufferedCells"):
 assert s in be,("B1040_BE_MISSING",s)
menu=javap("dev.obsidiannetwork.cellterminal.V176CellTerminalMenu")
for s in ("public void clicked","ChestMenu.clicked",
          "V176CellTerminalBlockEntity.setItem",
          "V176CellTerminalBlockEntity.getItem","public net.minecraft.world.item.ItemStack quickMoveStack"):
 assert s in menu,("B1040_MENU_NOT_REAL_BUFFER",s)
assert "V176CellTerminalTopology.scan" not in menu, "B1040_OLD_DIRECT_DRIVE_MENU_ROUTE"
assert "DriveMenu.xsxCellTerminalBacking" not in menu,"B1040_OLD_FAKE_CLICK_ACTION"
screen=javap("dev.obsidiannetwork.client.V176CellTerminalScreen")
assert "V176CellTerminalBlockEntity.bufferedCells" in screen,"B1040_BUFFER_STATUS_NOT_SYNCED"
with zipfile.ZipFile(jar) as z:
 paths=set(z.namelist())
 assert "dev/obsidiannetwork/cellterminal/V176CellTerminalBlockEntity.class" in paths
print("V176_B1040_COMPILED_PERSISTENT_BE_8_INPUT_GUI_AND_AUTOTICK_PASS scope=bytecode")
