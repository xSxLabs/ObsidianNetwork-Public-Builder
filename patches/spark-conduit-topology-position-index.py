#!/usr/bin/env python3
"""O(1) bundle neighbor membership while preserving live physical checks.

A position index is maintained for every ConduitNetwork node lifecycle
mutation. No block state, topology, capability or FE value is cached.
Both source files are validated in memory before either one is written.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit"
network=root/"ConduitNetwork.java"
topology=root/"ConduitTopology.java"
n=network.read_text(encoding="utf-8")
t=topology.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_CONDUIT_TOPOLOGY_POSITION_INDEX_V1"
assert marker not in n and marker not in t,"index already patched"
def one(source,old,new,name):
    count=source.count(old)
    assert count==1,"fail-closed topology source drift "+name+": "+str(count)
    return source.replace(old,new,1)
n=one(n,
 "private final Set<ConduitNode> nodes=new HashSet<>();",
 "private final Set<ConduitNode> nodes=new HashSet<>();\n // "+marker+"\n private final java.util.HashSet<net.minecraft.core.BlockPos> indexedPositions=new java.util.HashSet<>();",
 "network fields")
n=one(n,"this.type=type;nodes.add(first);",
        "this.type=type;nodes.add(first);indexedPositions.add(first.pos().immutable());",
        "constructor")
n=one(n,"nodes.add(n);n.network(this);dirty=true;",
        "nodes.add(n);indexedPositions.add(n.pos().immutable());n.network(this);dirty=true;",
        "node addition")
n=one(n,"nodes.remove(n);dirty=true;",
        "if(nodes.remove(n)){indexedPositions.clear();for(var current:nodes)indexedPositions.add(current.pos().immutable());}dirty=true;",
        "node removal including duplicate positions")
n=one(n,
 "nodes.clear();for(var n:copy){if(n.type()!=type)throw new IllegalArgumentException(\"type mismatch\");nodes.add(n);n.network(this);}dirty=true;",
 "nodes.clear();indexedPositions.clear();for(var n:copy){if(n.type()!=type)throw new IllegalArgumentException(\"type mismatch\");nodes.add(n);indexedPositions.add(n.pos().immutable());n.network(this);}dirty=true;",
 "component split merge")
n=one(n,"public void nodeChanged(ConduitNode n){dirty=true;}",
 "public boolean containsPosition(net.minecraft.core.BlockPos pos){return indexedPositions.contains(pos);}\n public void nodeChanged(ConduitNode n){dirty=true;}",
 "membership read")
t=one(t,
 "network.nodes().stream().anyMatch(n->n.pos().equals(bundle.getBlockPos().relative(d)))",
 "network.containsPosition(bundle.getBlockPos().relative(d))",
 "linear per-side membership")
assert n.count(marker)==1 and "network.nodes().stream().anyMatch" not in t
assert "physicallyConnected!=cachedConnected" in t
assert "network.nodeChanged(node)" in t
assert n.count("indexedPositions.add(n.pos().immutable())")==2
network.write_text(n,encoding="utf-8")
topology.write_text(t,encoding="utf-8")
print("SPARK_CONDUIT_TOPOLOGY_INDEX_V1 PASS (position index + unchanged physical invalidation)")
