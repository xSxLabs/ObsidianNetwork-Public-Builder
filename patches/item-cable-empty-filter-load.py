#!/usr/bin/env python3
"""Do not deserialize blank ghost-filter slots as real ITEM allowlist entries.

A cable saves eighteen string slots per side. Unoccupied slots are serialized
as empty strings. They must remain null, regardless of whether Identifier
tryParse("") happens to return a non-null identifier in a Minecraft version.
Apply after the private v1.6 features, fail-closed on unexpected source.
"""
from pathlib import Path
import os

root = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
p = root / "dev/obsidiannetwork/blockentity/LogisticsCableBlockEntity.java"
s = p.read_text(encoding="utf-8")
assert "XSXLABS_CABLE_INDEXED_GHOSTS_V3" in s, "18-slot filters not installed"
assert "XSXLABS_CABLE_FILTERS_LOAD" in s, "filter load method missing"

anchor = (
    "                   net.minecraft.resources.Identifier key =\n"
    "                       net.minecraft.resources.Identifier.tryParse(ids.get(i));"
)
assert s.count(anchor) == 1, "indexed filter parsing source changed; fail closed"
replacement = (
    "                   // Empty strings represent EMPTY ghost slots, never a whitelist entry.\n"
    "                   String storedFilterId = ids.get(i);\n"
    "                   if (storedFilterId == null || storedFilterId.isEmpty()) continue;\n"
    "                   net.minecraft.resources.Identifier key =\n"
    "                       net.minecraft.resources.Identifier.tryParse(storedFilterId);"
)
s = s.replace(anchor, replacement, 1)
assert s.count("if (storedFilterId == null || storedFilterId.isEmpty()) continue;") == 1
assert "this.cableSlotIds[face.ordinal()][i]=key;" in s
assert 'return this.mode(side) != Mode.IMPORT || allowed.isEmpty() || allowed.contains(id);' in s
p.write_text(s, encoding="utf-8")
print("ITEM_GHOST_EMPTY_SLOT_LOAD_FIX_V1 PASS")
