#!/usr/bin/env python3
"""Fail-closed final candidate guard for general crafting and cable hotpaths.

Runs on reconstructed, patched sources before compilation. It does not claim
Spark A/B improvement; it prevents a green CI build silently omitting fixes.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"

def check(relative, requirements):
    source = (root / relative).read_text(encoding="utf-8")
    for marker, count in requirements.items():
        actual = source.count(marker)
        assert actual == count, f"{relative}: {marker}: expected {count}, got {actual}"

check("menu/StorageTerminalMenu.java", {
    "XSXLABS_TERMINAL_DUPLICATE_BROADCAST_ELISION_V1": 1,
    "XSXLABS_JEI_ONCE_PER_RECIPE_KEYS_V1": 1,
})
check("blockentity/TerminalInventoryBlockEntity.java", {
    "XSXLABS_TERMINAL_UNCHANGED_CRAFT_SLOT_ELISION_V1": 1,
})
check("menu/AutocrafterMenu.java", {
    "XSXLABS_AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1": 1,
})
check("network/WorldTopologyBridge.java", {
    "XSXLABS_SPARK_AUTOCRAFTER_DIRECTIONS_ONCE_V1": 1,
    "XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1": 1,
})
check("blockentity/EnergyCableBlockEntity.java", {
    "XSXLABS_ENERGY_HELPER_DUPLICATE_BLOCKTYPE_ELISION_V1": 2,
})
check("blockentity/SolarGeneratorBlockEntity.java", {
    "XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1": 1,
})
check("core/StorageNetwork.java", {
    "XSXLABS_BULK_READONLY_PREVIEW_NO_SNAPSHOT_V1": 1,
    "XSXLABS_AUTOCRAFT_EXACT_SINGLE_PREFLIGHT_V1": 1,
})
check("platform/MinecraftAutocraftingService.java", {
    "XSXLABS_AUTOCRAFT_IDLE_RESERVATION_ELISION_V1": 1,
})
print("FINAL_CRAFTING_CABLE_SOURCE_GATE_V1 PASS: all 11 performance fix families present")
