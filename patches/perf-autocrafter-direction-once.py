#!/usr/bin/env python3
"""Fail-closed reduction of per-node Direction.values() allocations.

Apply after perf-autocrafter-count-component-once.py and
perf-spark-batched-live-chunk-registry-guards.py to reconstructed Java sources.
No FE, item, topology, permission, persistence, or neighbor order changes.
"""
import os
import re
from pathlib import Path

source_root = os.environ.get('V1_SOURCE_ROOT')
if not source_root:
    raise SystemExit('V1_SOURCE_ROOT is required')
path = Path(source_root) / 'dev/obsidiannetwork/network/WorldTopologyBridge.java'
source = path.read_text(encoding='utf-8')
marker = 'XSXLABS_SPARK_AUTOCRAFTER_DIRECTIONS_ONCE_V1'
start = re.compile(r'public\s+static\s+int\s+autocrafterCount\s*\(\s*ServerLevel\s+level\s*,\s*NetworkRuntime\s+runtime\s*\)\s*\{')
end = re.compile(r'public\s+static\s+int\s+autoChiselerCount\s*\(')
starts = list(start.finditer(source))
ends = list(end.finditer(source))
assert len(starts) == len(ends) == 1, 'Autocrafter method boundary drift'
a = starts[0].start()
b = ends[0].start()
assert a < b, 'Autocrafter method order drift'
method = source[a:b]
assert marker not in source, 'Patch already applied'
assert method.count('XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1') == 1, 'Owner component guard absent'
assert method.count('XSXLABS_SPARK_LIVE_SCAN_GUARDS_V1') == 1, 'Live chunk guard absent'
assert 'xsxCenterChunkLoaded' in method and 'level.hasChunkAt(q)' in method
assert method.count('return seen.size();') == 1, 'Autocrafter count semantics drift'

graph_loop = re.compile(r'for\s*\(\s*NetworkGraph\.Pos\s+px\s*:\s*s\.manager\.graph\(\)\.nodes\(\)\s*\)\s*\{')
direction_loop = re.compile(r'for\s*\(\s*Direction\s+d\s*:\s*Direction\.values\(\)\s*\)\s*\{')
graphs = list(graph_loop.finditer(method))
directions = list(direction_loop.finditer(method))
assert len(graphs) == len(directions) == 1, 'Autocrafter graph/direction loop drift'
assert graphs[0].start() < directions[0].start(), 'Direction loop not inside graph traversal'
assert method.count('Direction.values()') == 1, 'Unexpected additional direction enumeration'

method = direction_loop.sub('for (Direction d : xsxDirections) {', method, count=1)
method = graph_loop.sub(
    'Direction[] xsxDirections = Direction.values();\n'
    '      // ' + marker + ': one enum array per status call, not per graph node.\n'
    '      for (NetworkGraph.Pos px : s.manager.graph().nodes()) {',
    method, count=1)
assert method.count(marker) == 1
assert method.count('Direction.values()') == 1
assert method.count('for (Direction d : xsxDirections) {') == 1
assert method.count('level.hasChunkAt(q)') == 1
assert method.count('return seen.size();') == 1
path.write_text(source[:a] + method + source[b:], encoding='utf-8')
print(marker + ' PASS: 6-direction order unchanged; enum array allocated once per count')
