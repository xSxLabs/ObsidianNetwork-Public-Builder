#!/usr/bin/env python3
"""Hoist Direction.values() from physical conduit topology and manager validation loops."""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/conduit"
top = root / "ConduitTopology.java"
manager = root / "ConduitNetworkManager.java"
t = top.read_text(encoding="utf-8")
m = manager.read_text(encoding="utf-8")
tm = "XSXLABS_SPARK_TOPOLOGY_DIRECTIONS_V1"
mm = "XSXLABS_SPARK_MANAGER_DIRECTIONS_V1"
tc = "public final class ConduitTopology {"
mc = "public final class ConduitNetworkManager {"
tl = "for(Direction d:Direction.values())"
ml = "for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values())"
assert tm not in t and mm not in m, "Already patched"
for source,token in ((t,tc),(m,mc),(t,tl),(m,ml)):
    assert source.count(token) == 1, "Unexpected conduit source: " + token
for token in ("physicallyConnected!=cachedConnected", "network.nodeChanged(node)"):
    assert token in t, "Topology change detection missing: " + token
for token in ("current.shouldValidate(tick)", "current.nodes().contains(other.conduitNode(seed.type()))"):
    assert token in m, "Manager topology verification missing: " + token
t = t.replace(tc,tc + "\n private static final Direction[] " + tm + " = Direction.values();",1)
t = t.replace(tl,"for(Direction d:" + tm + ")",1)
m = m.replace(mc,mc + "\n private static final net.minecraft.core.Direction[] " + mm + " = net.minecraft.core.Direction.values();",1)
m = m.replace(ml,"for(net.minecraft.core.Direction d:" + mm + ")",1)
top.write_text(t,encoding="utf-8")
manager.write_text(m,encoding="utf-8")
print("SPARK_CONDUIT_TOPOLOGY_VALIDATION_DIRECTIONS PASS")
