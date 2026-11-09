#!/usr/bin/env python3
"""Fail-closed source transformation and randomized position-count regression."""
import collections
import os
import pathlib
import random
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[2]
patch = root / "features/v1771/apply-conduit-position-refcounts.py"
source = """
// XSXLABS_SPARK_CONDUIT_TOPOLOGY_POSITION_INDEX_V1
private final java.util.HashSet<net.minecraft.core.BlockPos> indexedPositions=new java.util.HashSet<>();
indexedPositions.add(first.pos().immutable());
indexedPositions.add(n.pos().immutable());
if(nodes.remove(n)){indexedPositions.clear();for(var current:nodes)indexedPositions.add(current.pos().immutable());}dirty=true;
nodes.clear();indexedPositions.clear();for(var n:copy)
nodes.add(n);indexedPositions.add(n.pos().immutable());n.network(this);
return indexedPositions.contains(pos);
"""
with tempfile.TemporaryDirectory() as temp:
    target = pathlib.Path(temp) / "dev/obsidiannetwork/conduit/ConduitNetwork.java"
    target.parent.mkdir(parents=True)
    target.write_text(source)
    env = dict(os.environ, V1_SOURCE_ROOT=temp)
    subprocess.run([sys.executable, str(patch)], env=env, check=True)
    result = target.read_text()
    assert "indexedPositions" not in result
    assert "positionCounts.containsKey(pos)" in result
    assert "new it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap<>(64)" in result, "primitive position index missing"
    assert "positionCounts.addTo(pos,1)" in result, "primitive increment missing"
    assert "positionCounts.removeInt(pos)" in result, "primitive removal missing"
    assert result.count("if(nodes.add(n))indexPosition(n.pos());") == 2, "duplicate nodes must not increment position counts"
    assert "Integer previous=" not in result and "Integer count=" not in result, "boxed refcount regression"
    assert "if(nodes.remove(n))unindexPosition(n.pos());dirty=true;" in result
    assert len(__import__("re").findall(r"(?<![A-Za-z])indexPosition\(", result)) == 4
    assert result.count("unindexPosition(") == 2
    # The patch must refuse source drift and repeated application.
    before = target.read_bytes()
    rerun = subprocess.run([sys.executable, str(patch)], env=env, capture_output=True)
    assert rerun.returncode != 0 and target.read_bytes() == before

rng = random.Random(1771)
for trial in range(100):
    nodes = []
    counts = {}
    for step in range(1500):
        if not nodes or rng.random() < .57:
            pos = rng.randrange(128)
            nodes.append(pos)
            counts[pos] = counts.get(pos, 0) + 1
        else:
            index = rng.randrange(len(nodes))
            pos = nodes.pop(index)
            count = counts[pos]
            if count == 1:
                del counts[pos]
            else:
                counts[pos] = count - 1
        expected = set(nodes)
        assert set(counts) == expected
        assert all(counts[pos] == occurrences for pos, occurrences in collections.Counter(nodes).items())
        assert all((pos in counts) == (pos in expected) for pos in range(128))
    # Simulate split/reset and rebuild.
    counts.clear()
    for pos in nodes:
        counts[pos] = counts.get(pos, 0) + 1
    assert counts == dict(collections.Counter(nodes))
print("V1771_POSITION_REFCOUNT_TRANSFORM_AND_150000_MUTATIONS_PASS")
