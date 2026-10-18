#!/usr/bin/env python3
"""Eliminate repeated full-graph BFS from WorldTopologyBridge.autocrafterCount.

The original scanned every graph node, calling runtimeForNode() for each one,
which traversed a component repeatedly. This is especially costly when
Controller menus query the count on a 50-drive network.

Derive exactly the runtime's ACTIVE component(s) once per call from the
live controllerRuntimes identity map; preserve registered autocrafters,
unregistered-block discovery, adjacent non-graph autocrafters, chunk checks,
conflicting controllers, cross-network isolation and all item/FE operations.

No inter-tick cache: topology changes inside the same tick are observed.
"""
import os
from pathlib import Path

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/network/WorldTopologyBridge.java"
source=path.read_text(encoding="utf-8")
start="   public static int autocrafterCount(ServerLevel level, NetworkRuntime runtime) {"
end="   public static int autoChiselerCount(ServerLevel level, NetworkRuntime runtime) {"
assert source.count(start)==1 and source.count(end)==1, "autocrafterCount method anchors drift"
a=source.index(start)
b=source.index(end,a)
old=source[a:b]
for token in (
    "WorldTopologyBridge.LevelTopology s = LEVELS.get(level);",
    "HashSet<NetworkGraph.Pos> seen = new HashSet<>();",
    "for (NetworkGraph.Pos p : s.autocrafters)",
    "if (runtimeForNode(s, p) == runtime)",
    "for (NetworkGraph.Pos px : s.manager.graph().nodes())",
    "!seen.contains(px) && runtimeForNode(s, px) == runtime",
    "level.hasChunkAt(bp)",
    "level.getBlockState(bp)",
    "level.hasChunkAt(q)",
    "level.getBlockState(q)",
    "seen.add(qp);",
    "return seen.size();",
):
    assert old.count(token)==1, ("protected existing semantics missing",token,old.count(token))
assert "XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1" not in source
new="""   public static int autocrafterCount(ServerLevel level, NetworkRuntime runtime) {
      WorldTopologyBridge.LevelTopology s = LEVELS.get(level);
      if (s == null || runtime == null) return 0;

      // XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1: compute owner nodes ONCE for
      // this lookup; no cache survives block edits, splits, reloads or ticks.
      // An ACTIVE component has exactly one owning controller; exclude
      // offline/conflicting components exactly as runtimeForNode did.
      HashSet<NetworkGraph.Pos> ownerNodes = new HashSet<>();
      for (var entry : s.controllerRuntimes.entrySet()) {
         if (entry.getValue() != runtime) continue;
         NetworkGraph.Pos controllerPos = entry.getKey();
         if (s.manager.stateAt(controllerPos) == TopologyBindingManager.ComponentState.ACTIVE) {
            ownerNodes.addAll(s.manager.graph().component(controllerPos));
         }
      }
      if (ownerNodes.isEmpty()) return 0;

      HashSet<NetworkGraph.Pos> seen = new HashSet<>();
      for (NetworkGraph.Pos p : s.autocrafters) {
         if (ownerNodes.contains(p)) {
            seen.add(p);
         }
      }

      // Keep the original scan and neighboring-block discovery semantics,
      // but visit only the ACTIVE component(s) of the requested runtime.
      // Iterate graph.nodes() in its ORIGINAL iteration order. Scanning
      // ownerNodes directly can change which neighboring machine nodes get
      // skipped by seen, and therefore alter the exact final count.
      for (NetworkGraph.Pos px : s.manager.graph().nodes()) {
         if (!seen.contains(px) && ownerNodes.contains(px)) {
            BlockPos bp = new BlockPos(px.x(), px.y(), px.z());
            if (level.hasChunkAt(bp) && level.getBlockState(bp).is((Block)ObsidianNetwork.AUTOCRAFTER.get())) {
               seen.add(px);
            }

            for (Direction d : Direction.values()) {
               BlockPos q = bp.relative(d);
               NetworkGraph.Pos qp = toCore(q);
               if (level.hasChunkAt(q) && level.getBlockState(q).is((Block)ObsidianNetwork.AUTOCRAFTER.get())) {
                  seen.add(qp);
               }
            }
         }
      }
      return seen.size();
   }

   """
assert new.count("XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1")==1
assert new.count("s.manager.graph().component(controllerPos)")==1
assert "runtimeForNode(s, px)" not in new
assert "return seen.size();" in new
path.write_text(source[:a]+new+source[b:],encoding="utf-8")
print("XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1 PASS; runtime-specific active graph scan; no persistent cache")
