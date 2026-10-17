#!/usr/bin/env python3
"""Reuse immutable scan directions and the same live neighbor BlockPos in ConduitRuntime.

Keeps every chunk, connectivity and machine-endpoint rejection check in its
original order. Nothing is cached across ticks, network refreshes, or loads.
Fail closed on generated Java shape drift.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/conduit/ConduitRuntime.java"
src = p.read_text(encoding="utf-8")
marker = "XSXLABS_SPARK_CONDUIT_RUNTIME_REUSE_V1"
cls = "public final class ConduitRuntime {"
directions = "XSXLABS_SPARK_RUNTIME_DIRECTIONS_V1"
assert marker not in src and directions not in src, "Already patched"
assert src.count(cls) == 1, "Runtime class changed"
assert src.count("Direction.values()") == 3, "Unexpected direction-array sites"
assert src.count("Direction[] directions=Direction.values();") == 1, "Mixed BFS changed"
assert src.count("for(Direction d:Direction.values()){") == 2, "Endpoint loops changed"

first = " public static List<Endpoint> scanEndpoints("
last = " public static List<Endpoint> endpoints("
assert src.count(first) == 1 and src.count(last) == 1, "Endpoint methods changed"
prefix, tail = src.split(first, 1)
scan, suffix = tail.split(last, 1)
chunk = "boolean on=extract?b.conduitCanExtract(layer,d):b.conduitCanInsert(layer,d);if(!on||!level.hasChunkAt(b.getBlockPos().relative(d)))continue;"
cable = "if(traversable(level,b.getBlockPos().relative(d),type))continue;"
state = "level.getBlockState(b.getBlockPos().relative(d))"
for expected in (chunk, cable, state, "adjacentId.endsWith(\"_cable\")", "out.sort(Comparator.comparingInt("):
    assert scan.count(expected) == 1, "Endpoint guard changed: " + expected
assert scan.count("b.getBlockPos().relative(d)") == 3, "Unexpected bundle neighbor probes"
assert scan.count("for(Direction d:Direction.values()){") == 2
# Preserve initial mode rejection as the first check and one neighbor position per active face.
scan = scan.replace(chunk,
    "boolean on=extract?b.conduitCanExtract(layer,d):b.conduitCanInsert(layer,d);if(!on)continue;\n"
    "    // " + marker + "\n"
    "    BlockPos neighborPos=b.getBlockPos().relative(d);\n"
    "    if(!level.hasChunkAt(neighborPos))continue;", 1)
scan = scan.replace(cable, "if(traversable(level,neighborPos,type))continue;", 1)
scan = scan.replace(state, "level.getBlockState(neighborPos)", 1)
assert scan.count("b.getBlockPos().relative(d)") == 1, "Redundant bundle neighbor probe remained"
assert "if(!on)continue;" in scan and "if(!level.hasChunkAt(neighborPos))continue;" in scan
assert "if(traversable(level,neighborPos,type))continue;" in scan
assert "level.getBlockState(neighborPos)" in scan
combined = prefix + first + scan + last + suffix
assert combined.count("Direction.values()") == 3
combined = combined.replace("Direction.values()", directions)
combined = combined.replace(cls, cls + "\n private static final Direction[] " + directions + " = Direction.values();", 1)
assert combined.count("Direction.values()") == 1
assert combined.count(directions) == 4, "Three original iteration sites and private array required"
p.write_text(combined, encoding="utf-8")
print("SPARK_CONDUIT_RUNTIME_REUSE_V1 PASS; order/modes/chunk guards retained, one neighbor per bundle face")
