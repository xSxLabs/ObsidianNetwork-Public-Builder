#!/usr/bin/env python3
"""Synthetic fail-closed contracts for manager-indexed importer topology.

This does not substitute for full Java compilation or an ingame split/merge
test; intentionally run in the ordinary regression suite before any JAR.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/perf-accessory-topology-rebuild-index.py"

MANAGER="""package dev.obsidiannetwork.core;
public final class TopologyBindingManager {
   private final NetworkGraph graph = new NetworkGraph();
   private final Map<NetworkGraph.Pos,NetworkRuntime> controllers = new HashMap<>();
   private Set<NetworkGraph.Pos> conflictingControllers = Set.of();
   private long rebuildCount;
   private int batchDepth;
   private boolean rebuildPending;

   public long rebuildCount() { return this.rebuildCount; }
   public void beginBatch() {
      this.batchDepth++;
   }
   public void endBatch() {
      if (this.batchDepth > 0 && this.rebuildPending) { this.rebuildPending = false; this.rebuild(); }
   }
   private void requestRebuild() {
      if (this.batchDepth > 0) { this.rebuildPending = true; }
      else this.rebuild();
   }
   public TopologyBindingManager.ComponentState stateAt(NetworkGraph.Pos pos) {
      Set<NetworkGraph.Pos> component = this.graph.component(pos);
      if(component.isEmpty())return TopologyBindingManager.ComponentState.OFFLINE;
      int count=0;
      for(NetworkGraph.Pos node:component) if(this.controllers.containsKey(node))count++;
      return count==1?ComponentState.ACTIVE:count==0?ComponentState.OFFLINE:ComponentState.CONFLICT;
   }
   public TopologyBindingManager.Snapshot snapshot() {
      return new TopologyBindingManager.Snapshot(this.graph.revision(), this.rebuildCount, Map.of(), this.conflictingControllers);
   }
   public void rebuild() {
      this.rebuildCount++;
      HashMap<NetworkGraph.Pos,NetworkGraph.Pos> desired = new HashMap<>();
      HashMap<NetworkGraph.Pos,NetworkGraph.Pos> desiredTerminals = new HashMap<>();
      HashSet<NetworkGraph.Pos> conflicts = new HashSet<>();
      HashSet<NetworkGraph.Pos> visited = new HashSet<>();

      for (NetworkGraph.Pos start : this.graph.nodes()) {
         if (!visited.contains(start)) {
            Set<NetworkGraph.Pos> component = this.graph.component(start);
            visited.addAll(component);
            NetworkGraph.Pos onlyController = null;
            int controllerCount = 0;
            for (NetworkGraph.Pos node : component) {
               if (this.controllers.containsKey(node)) {
                  controllerCount++;
                  onlyController = node;
               }
            }
            if (controllerCount > 1) {
               for (NetworkGraph.Pos node : component) if (this.controllers.containsKey(node)) conflicts.add(node);
            } else if (controllerCount == 1) {
               for (NetworkGraph.Pos nodexx : component) {
                  if (this.drives.containsKey(nodexx)) {
                     desired.put(nodexx, onlyController);
                  }
                  if (this.terminals.containsKey(nodexx)) desiredTerminals.put(nodexx,onlyController);
               }
            }
         }
      }
      this.conflictingControllers = Set.copyOf(conflicts);
   }
   public static enum ComponentState {OFFLINE,ACTIVE,CONFLICT}
}"""
BRIDGE="""package dev.obsidiannetwork.network;
public final class WorldTopologyBridge {
   public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {
      WorldTopologyBridge.LevelTopology s = LEVELS.get(level);
      if (s == null) {
         return null;
      } else {
         NetworkGraph.Pos p = toCore(pos);
         if (s.manager.stateAt(p) != TopologyBindingManager.ComponentState.ACTIVE) {
            return null;
         } else {
            for (NetworkGraph.Pos node : s.manager.graph().component(p)) {
               NetworkRuntime runtime = s.controllerRuntimes.get(node);
               if (runtime != null) {
                  return runtime;
               }
            }

            return null;
         }
      }
   }
}
"""

def prepare(root,manager=MANAGER,bridge=BRIDGE):
    for relative,text in {
      "core/TopologyBindingManager.java":manager,
      "network/WorldTopologyBridge.java":bridge
    }.items():
      file=root/"dev/obsidiannetwork"/relative
      file.parent.mkdir(parents=True,exist_ok=True)
      file.write_text(text)

def patch(root):
    return subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,env={
      **os.environ,"V1_SOURCE_ROOT":str(root)
    })

class TopologyRebuildIndex(unittest.TestCase):
    def test_patch_preserves_live_path_and_indexes_only_unambiguous_components(self):
        ast.parse(PATCH.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            prepare(root)
            result=patch(root)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            m=(root/"dev/obsidiannetwork/core/TopologyBindingManager.java").read_text()
            w=(root/"dev/obsidiannetwork/network/WorldTopologyBridge.java").read_text()
            self.assertIn("pendingAccessoryControllers.put(nodexx,onlyController);",m)
            self.assertIn("else if (controllerCount == 1)",m)
            self.assertIn("Map.copyOf(pendingAccessoryControllers)",m)
            self.assertLess(m.index("this.conflictingControllers = Set.copyOf(conflicts);"),
                            m.index("this.activeAccessoryControllers = Map.copyOf(pendingAccessoryControllers);"))
            self.assertIn("this.accessoryIndexGraphRevision == this.graph.revision()",m)
            self.assertIn("this.accessoryIndexRebuildCount == this.rebuildCount",m)
            self.assertIn("this.batchDepth == 0 && !this.rebuildPending",m)
            self.assertIn("s.manager.activeAccessoryController(p)",w)
            self.assertIn("s.controllerRuntimes.get(controller)",w)
            self.assertIn("s.manager.stateAt(p)",w)
            self.assertIn("s.manager.graph().component(p)",w)
            self.assertIn("if (controller == null) return null;",w)
            self.assertIn("if (cachedOwner != null) return cachedOwner;",w)
            self.assertNotIn("static Map<",m)
            self.assertNotEqual(patch(root).returncode,0)
    def test_wrong_revision_or_missing_live_fallback_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prepare(root,bridge=BRIDGE.replace("stateAt(p)","stateAtUnknown(p)"))
            before=(root/"dev/obsidiannetwork/core/TopologyBindingManager.java").read_text()
            self.assertNotEqual(patch(root).returncode,0)
            self.assertEqual(before,(root/"dev/obsidiannetwork/core/TopologyBindingManager.java").read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prepare(root,manager=MANAGER.replace("this.graph.revision()","this.graph.version()"))
            self.assertNotEqual(patch(root).returncode,0)
    def test_unchanged_revision_is_not_an_unconditional_global_cache(self):
        script=PATCH.read_text()
        for x in ["batchDepth", "rebuildPending", "this.graph.revision()", "this.rebuildCount",
                  "stateAt(p)", "graph().component(p)", "Map.copyOf(pendingAccessoryControllers)"]:
            self.assertIn(x,script)
        self.assertNotIn("ThreadLocal",script)
        self.assertNotIn("getGameTime()",script)

if __name__=="__main__":
    unittest.main()
