#!/usr/bin/env python3
"""Use packed world coordinates for primitive BFS visit membership.

Minecraft BlockPos.asLong is unique within the standard world border and
height limits. The queue keeps the original BlockPos and traversal ordering.
No live state/capability checks, transactions, or cut rules are cached.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_BFS_PRIMITIVE_VISITED_V1"
assert marker not in s, "Already patched"
assert "XSXLABS_SPARK_BFS_POSITION_REUSE_V1" in s, "Wrong patch order"
assert "XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1" in s
assert s.count("private final class CableEnergyHandler implements EnergyHandler")==1
old_set="HashSet visited = new HashSet();"
origin="visited.add(EnergyCableBlockEntity.this.worldPosition);"
neighbor="visited.add(next)"
for token in (old_set,origin,neighbor,"BlockPos next = cable.relative(side);","cableBudget-- > 0"):
    assert s.count(token)==3, "Unexpected energy traversal shape: "+token
assert "visited.contains(" not in s
s=s.replace(old_set,"it.unimi.dsi.fastutil.longs.LongOpenHashSet visited = new it.unimi.dsi.fastutil.longs.LongOpenHashSet();")
s=s.replace(origin,"visited.add(EnergyCableBlockEntity.this.worldPosition.asLong());")
s=s.replace(neighbor,"visited.add(next.asLong())")
s="// "+marker+"\n"+s
assert s.count("visited.add(next.asLong())")==3
assert s.count("visited.add(EnergyCableBlockEntity.this.worldPosition.asLong());")==3
p.write_text(s,encoding="utf-8")
print("SPARK_BFS_PRIMITIVE_VISITED_V1 PASS; same visits, no per-node boxed/object hash key")
