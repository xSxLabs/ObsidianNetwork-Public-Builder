#!/usr/bin/env python3
"""Replace the Solar FE endpoint EnumMap with six fixed enum-indexed slots.

This is strictly a lookup/allocation optimization ON TOP of the existing
NeoForge BlockCapabilityCache implementation. Each side still gets the same
opposite-face capability, onLoad/setRemoved/server-change invalidation and
the same stored-energy budget, round-robin order, transaction and rollback.
Fail closed if the previous safety patch or source shape changes.
"""
import os
import re
from pathlib import Path

path = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
source = path.read_text(encoding="utf-8")
marker = "XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1"
assert marker not in source, "Solar fixed cache already installed"
assert source.count("XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1") == 1, "Safe NeoForge cache patch missing"
assert source.count("private EnergyHandler neighborEnergy(ServerLevel server,Direction side)") == 1
assert source.count("net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(") == 1
assert source.count("() -> !isRemoved() && level==server") == 1
assert source.count("be.neighborEnergy(server, side)") == 1
assert source.count("energyNeighbors.clear();") == 3, "Solar lifecycle invalidation changed"
assert source.count("energyNeighbors.get(side)") == 1
assert source.count("energyNeighbors.put(side,cache)") == 1
for invariant in ("be.energyJournal.updateSnapshots(tx);", "tx.commit();",
                  "budget -= accepted;", "int start = be.nextSide++ % sides.length;"):
    assert source.count(invariant) == 1, "FE transfer/rotation changed: " + invariant
field_pattern = re.compile(
    r"private\s+final\s+java\.util\.EnumMap<Direction,\s*"
    r"net\.neoforged\.neoforge\.capabilities\.BlockCapabilityCache<EnergyHandler,Direction>>"
    r"\s+energyNeighbors\s*=\s*new java\.util\.EnumMap<>\(Direction\.class\);"
)
replacement = """// XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1: Direction.get3DDataValue() is 0..5.
 @SuppressWarnings("unchecked")
 private final net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[]
  energyNeighbors=(net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[])
   new net.neoforged.neoforge.capabilities.BlockCapabilityCache[6];"""
updated, count = field_pattern.subn(lambda match: replacement, source)
assert count == 1, "Unexpected solar cache field shape"
updated = updated.replace(
    "energyNeighbors.clear();",
    "java.util.Arrays.fill(energyNeighbors,null);"
)
updated = updated.replace(
    "var cache=energyNeighbors.get(side);",
    "int slot=side.get3DDataValue();\n  var cache=energyNeighbors[slot];",
    1
)
updated = updated.replace(
    "energyNeighbors.put(side,cache);",
    "energyNeighbors[slot]=cache;",
    1
)
assert updated.count("java.util.Arrays.fill(energyNeighbors,null);") == 3
assert updated.count("energyNeighbors[slot]") == 2
assert "energyNeighbors.clear()" not in updated and "EnumMap" not in updated
assert updated.count("net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(") == 1
assert updated.count("() -> !isRemoved() && level==server") == 1
assert updated.count("be.neighborEnergy(server, side)") == 1
assert updated.count("tx.commit();") == source.count("tx.commit();")
assert updated.count("budget -= accepted;") == source.count("budget -= accepted;")
path.write_text(updated, encoding="utf-8")
print("SOLAR_FIXED_SIX_FACE_CACHE_V1 PASS: same lifecycle, FE transfers and sided NeoForge invalidation")
