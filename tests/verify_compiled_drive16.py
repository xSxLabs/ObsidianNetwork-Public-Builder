#!/usr/bin/env python3
"""Fail closed if final distributable JAR regresses 16 real Drive slots.

Server backing size AND client menu/screen 2x8 are inspected in compiled
bytecode, not in a pre-optimization source fixture. This is in addition
to the real Minecraft GameTests, not a substitute for a client GUI test.
"""
import argparse
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile

NEEDED = [
    "dev/obsidiannetwork/core/StorageDriveRuntime.class",
    "dev/obsidiannetwork/menu/DriveMenu.class",
    "dev/obsidiannetwork/menu/DriveMenu$DriveContainer.class",
    "dev/obsidiannetwork/client/DriveScreen.class",
    "dev/obsidiannetwork/blockentity/StorageDriveBlockEntity.class",
]


def javap(jar: Path, name: str, *args: str) -> str:
    return subprocess.run(["javap", *args, "-classpath", str(jar), name],
                          check=True, text=True, capture_output=True).stdout


def method_code(text: str, method: str) -> str:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines)
              if line.startswith("  ") and line.strip().endswith(method)]
    assert len(starts) == 1, (method, starts)
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("  ") and not lines[i].startswith("    ")
                and not re.match(r"  \d+: ", lines[i])), len(lines))
    return "\n".join(lines[start:end])


def verify(jar: Path):
    assert jar.is_file(), "Missing final JAR: " + str(jar)
    with ZipFile(jar) as archive:
        names = set(archive.namelist())
        for needed in NEEDED:
            assert needed in names, "Compiled class missing: " + needed
        assert not any(name.startswith("dev/obsidiannetwork/build103/")
                       for name in names), "CI-only test code leaked into JAR"

    runtime = javap(jar, "dev.obsidiannetwork.core.StorageDriveRuntime", "-p", "-constants")
    assert re.search(r"public static final int SLOTS = 16;", runtime)

    backing = javap(jar, "dev.obsidiannetwork.menu.DriveMenu$DriveContainer", "-c", "-p")
    size = method_code(backing, "getContainerSize();")
    assert re.search(r"\b0:\s+bipush\s+16\b", size), "Server Drive container truncated"
    assert re.search(r"\b2:\s+ireturn", size), "Unexpected Drive size implementation"
    read = method_code(backing, "getItem(int);")
    assert re.search(r"\bbipush\s+16\b", read), "Cell read bounds truncated"
    assert "StorageDriveBlockEntity.cellStack:" in read, "Cell backing detached"
    for name in ("removeItem(int, int);", "removeItemNoUpdate(int);",
                 "setItem(int, net.minecraft.world.item.ItemStack);"):
        assert "invalidate:()V" in method_code(backing, name), "Stale GUI cache: " + name

    menu = javap(jar, "dev.obsidiannetwork.menu.DriveMenu", "-c", "-p")
    client = method_code(menu, "DriveMenu(int, net.minecraft.world.entity.player.Inventory, net.minecraft.network.RegistryFriendlyByteBuf);")
    assert re.search(r"\bbipush\s+16\b", client) and "SimpleContainer" in client, "Client menu size != 16"
    main = method_code(menu, "DriveMenu(int, net.minecraft.world.entity.player.Inventory, net.minecraft.core.BlockPos, net.minecraft.world.Container);")
    assert all(v in main for v in ("iconst_2", "bipush        8", "bipush        24")), "Menu must be two 8-cell rows"

    screen = javap(jar, "dev.obsidiannetwork.client.DriveScreen", "-c", "-p")
    ctor = method_code(screen, "DriveScreen(dev.obsidiannetwork.menu.DriveMenu, net.minecraft.world.entity.player.Inventory, net.minecraft.network.chat.Component);")
    assert all(v in ctor for v in ("sipush        176", "sipush        194")), "GUI height may hide slots"
    draw = method_code(screen, "extractBackground(net.minecraft.client.gui.GuiGraphicsExtractor, int, int, float);")
    assert all(v in draw for v in ("iconst_2", "bipush        8", "bipush        24")), "Client 2x8 drawing lost"

    entity = javap(jar, "dev.obsidiannetwork.blockentity.StorageDriveBlockEntity", "-c", "-p")
    assert entity.count("cell_inventory") >= 2, "Drive inventory save/load key missing"
    print("COMPILED_DRIVE16_CLIENT_SERVER_NO_TRUNCATION_V1 PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jar", type=Path)
    verify(parser.parse_args().jar)
