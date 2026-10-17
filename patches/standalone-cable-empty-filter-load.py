#!/usr/bin/env python3
"""Do not deserialize empty ghost-slot placeholders as cable filter IDs.

The v1.6 cable filter writer deliberately saves 18 strings per face, using ""
for an unoccupied ghost slot. In Minecraft 26.1.2 Identifier.tryParse("") may
yield an Identifier instead of null; this inserts a bogus whitelist entry and
turns an unfiltered IMPORT cable into a rejecting one after a server restart.

Preserve nonempty user-configured filters and positional ghost slots.
Do not alter GUI modes, transfer cadence, endpoints or serialized schema.
"""
from pathlib import Path
import os

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
p = root / "blockentity/LogisticsCableBlockEntity.java"
s = p.read_text()
assert s.count("XSXLABS_CABLE_INDEXED_GHOSTS_V3") == 1, "18-slot filter layout changed"
assert s.count("XSXLABS_CABLE_FILTERS_LOAD") == 1, "filter deserializer missing"
old = """                   net.minecraft.resources.Identifier key =
                       net.minecraft.resources.Identifier.tryParse(ids.get(i));
                   if (key != null && allowed.add(key))
                      this.cableSlotIds[face.ordinal()][i]=key;"""
new = """                   // Empty ghost positions must never become allowlist entries.
                   // Reject malformed historical empty-path placeholders too.
                   String rawFilterId = ids.get(i);
                   net.minecraft.resources.Identifier key =
                       rawFilterId.isEmpty() ? null :
                       net.minecraft.resources.Identifier.tryParse(rawFilterId);
                   if (key != null && !key.getPath().isEmpty() && allowed.add(key))
                      this.cableSlotIds[face.ordinal()][i]=key;"""
assert s.count(old) == 1, "filter load loop anchor changed, refusing unsafe patch"
assert s.count('return key == null ? "" : key.toString();') == 1, "ghost-slot save format changed"
assert s.count("return this.mode(side) != Mode.IMPORT || allowed.isEmpty() || allowed.contains(id);") == 1, "filter semantics changed"
s = s.replace(old, new, 1)
assert s.count("rawFilterId.isEmpty() ? null") == 1
assert s.count("!key.getPath().isEmpty()") == 1
p.write_text(s)
print("STANDALONE_CABLE_EMPTY_FILTER_LOAD_V1 PASS")
