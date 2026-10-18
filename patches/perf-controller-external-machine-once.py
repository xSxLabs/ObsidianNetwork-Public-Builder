#!/usr/bin/env python3
"""Deduplicate read-only external machine capability probes in Controller status.

The unoptimized connectedDeviceCounts revisits the same adjacent block once
per connected cable/drive, repeatedly checking all six Item capabilities even
though output is already a Set<BlockPos>. Avoid repeated observations per
synchronous call only; never cache across ticks or topology changes.

Preserve order of first encounters, unloaded checks, connected block counts,
every supported machine type and the final unique processing count.
"""
import os
from pathlib import Path

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/network/WorldTopologyBridge.java"
source=path.read_text(encoding="utf-8")
start="   public static WorldTopologyBridge.DeviceCounts connectedDeviceCounts(ServerLevel level, NetworkRuntime runtime) {"
end="   public static List<BlockPos> externalCandidates(ServerLevel level, NetworkRuntime runtime) {"
assert source.count(start)==1 and source.count(end)==1
a=source.index(start);b=source.index(end,a)
segment=source[a:b]
marker="XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1"
assert marker not in source
changes=(
    ("            HashSet<BlockPos> external = new HashSet<>();",
     """            HashSet<BlockPos> external = new HashSet<>();
            // XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1
            // Local to one synchronous read, never stale across block changes.
            HashSet<BlockPos> checkedExternal = new HashSet<>();
            Direction[] directions = Direction.values();"""),
    ("               for (Direction d : Direction.values()) {",
     "               for (Direction d : directions) {"),
    ("                  if (level.hasChunkAt(q) && !component.contains(toCore(q))) {",
     "                  if (level.hasChunkAt(q) && !component.contains(toCore(q)) && checkedExternal.add(q.immutable())) {"),
    ('"ironfurnaces".equals(BuiltInRegistries.BLOCK.getKey(level.getBlockState(q).getBlock()).getNamespace())',
     '"ironfurnaces".equals(BuiltInRegistries.BLOCK.getKey(b).getNamespace())'),
    ("                        for (Direction side : Direction.values()) {",
     "                        for (Direction side : directions) {"),
)
for old,new in changes:
    assert segment.count(old)==1, ("Drifted connectedDeviceCounts contract",old,segment.count(old))
    segment=segment.replace(old,new,1)
for anchor in (
    "Set<NetworkGraph.Pos> component = s.manager.graph().component(controller);",
    "external.add(q.immutable());",
    "processing = external.size();",
    "level.getCapability(Item.BLOCK, q, side) != null",
    "boolean vanilla = b == Blocks.FURNACE || b == Blocks.BLAST_FURNACE",
    "int autocrafters = 0;",
):
    assert segment.count(anchor)==1, ("Protected device counting missing",anchor)
assert segment.count(marker)==1
path.write_text(source[:a]+segment+source[b:],encoding="utf-8")
print("XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1 PASS: repeated neighbor capability checks elided")
