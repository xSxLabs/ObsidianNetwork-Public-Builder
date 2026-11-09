#!/usr/bin/env python3
"""Replace O(network-size) Conduit position-index rebuild on node removal.

Preserve duplicate-position semantics using reference counts. All topology,
live physical connectivity, and FE transactions remain unchanged.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit/ConduitNetwork.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_V1771_CONDUIT_POSITION_REFCOUNTS_V1"
assert marker not in s
assert s.count("XSXLABS_SPARK_CONDUIT_TOPOLOGY_POSITION_INDEX_V1")==1
def replace(old,new,label):
    global s
    assert s.count(old)==1, f"Conduit source drift {label}: {s.count(old)}"
    s=s.replace(old,new,1)

replace(
 "private final java.util.HashSet<net.minecraft.core.BlockPos> indexedPositions=new java.util.HashSet<>();",
 "// "+marker+"\n private final java.util.HashMap<net.minecraft.core.BlockPos,Integer> positionCounts=new java.util.HashMap<>();\n"
 " private void indexPosition(net.minecraft.core.BlockPos pos){pos=pos.immutable();positionCounts.merge(pos,1,Integer::sum);}\n"
 " private void unindexPosition(net.minecraft.core.BlockPos pos){Integer count=positionCounts.get(pos);"
 "if(count==null)throw new IllegalStateException(\"Conduit position index desynchronized\");"
 "if(count==1)positionCounts.remove(pos);else positionCounts.put(pos,count-1);}",
 "index field")
replace("indexedPositions.add(first.pos().immutable());","indexPosition(first.pos());","first node")
assert s.count("indexedPositions.add(n.pos().immutable());")==2, "Conduit source drift node add" 
s=s.replace("indexedPositions.add(n.pos().immutable());","indexPosition(n.pos());",1)
replace("if(nodes.remove(n)){indexedPositions.clear();for(var current:nodes)indexedPositions.add(current.pos().immutable());}dirty=true;",
        "if(nodes.remove(n))unindexPosition(n.pos());dirty=true;","node removal")
replace("nodes.clear();indexedPositions.clear();for(var n:copy)",
        "nodes.clear();positionCounts.clear();for(var n:copy)","split reset")
replace("nodes.add(n);indexedPositions.add(n.pos().immutable());n.network(this);",
        "nodes.add(n);indexPosition(n.pos());n.network(this);","split rebuild")
replace("return indexedPositions.contains(pos);","return positionCounts.containsKey(pos);","membership")
assert "indexedPositions" not in s
assert len(__import__("re").findall(r"(?<![A-Za-z])indexPosition\(",s))==4
assert s.count("unindexPosition(")==2
p.write_text(s,encoding="utf-8")
print("V1771_CONDUIT_POSITION_REFCOUNTS PASS: O(1) node removal, duplicate-safe position membership")
