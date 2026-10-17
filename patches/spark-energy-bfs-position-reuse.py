#!/usr/bin/env python3
"""Reuse the immutable BlockPos already produced by relative() in three energy BFS traversals."""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s = p.read_text(encoding="utf-8")
marker = "XSXLABS_SPARK_BFS_POSITION_REUSE_V1"
expected = {
    "BlockPos next = cable.relative(side);": 3,
    "visited.add(next.immutable())": 3,
    "queue.addLast(next.immutable());": 3,
}
assert marker not in s, "Patch applied already"
for token, count in expected.items():
    assert s.count(token) == count, "Unrecognized BFS source: " + token
s = s.replace("visited.add(next.immutable())", "visited.add(next)")
s = s.replace("queue.addLast(next.immutable());", "queue.addLast(next);")
s = "// " + marker + "\n" + s
p.write_text(s, encoding="utf-8")
print("SPARK_BFS_POSITION_REUSE PASS")
