#!/usr/bin/env python3
"""Compute each live physical conduit neighbor position once per direction.

Preserves the same ConduitRuntime.bundle lookup and indexed network membership,
including per-tick physical topology invalidation on placement/removal.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit/ConduitTopology.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_TOPOLOGY_NEIGHBOR_POS_REUSE_V1"
old="ConduitBundleBlockEntity other=ConduitRuntime.bundle(level,bundle.getBlockPos().relative(d),type);"
membership="network.containsPosition(bundle.getBlockPos().relative(d))"
assert marker not in s and "XSXLABS_SPARK_TOPOLOGY_DIRECTIONS_V1" in s
for token in (old,membership):
    assert s.count(token)==1,"Topology drift: "+token
# The compiled class has multiple independent topology invalidation call sites.
# This patch touches only the unique neighbor expression above, and must retain all call sites.
for token in ("physicallyConnected!=cachedConnected","network.nodeChanged(node)"):
    assert token in s,"Missing topology safety check: "+token
assert s.count("for(Direction d:XSXLABS_SPARK_TOPOLOGY_DIRECTIONS_V1)")==1
s=s.replace(old,"// "+marker+"\n   net.minecraft.core.BlockPos neighborPos=bundle.getBlockPos().relative(d);\n   ConduitBundleBlockEntity other=ConduitRuntime.bundle(level,neighborPos,type);",1)
s=s.replace(membership,"network.containsPosition(neighborPos)",1)
assert s.count("bundle.getBlockPos().relative(d)")==1
assert "physicallyConnected!=cachedConnected" in s
p.write_text(s,encoding="utf-8")
print("SPARK_TOPOLOGY_NEIGHBOR_POS_REUSE_V1 PASS; full live validation unchanged")
