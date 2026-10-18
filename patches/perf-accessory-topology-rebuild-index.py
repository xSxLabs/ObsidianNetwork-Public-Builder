#!/usr/bin/env python3
"""Index active accessory -> controller position during real topology rebuild.

Spark: ImporterBlockEntity.serverTick -> WorldTopologyBridge.runtimeForAccessory
walks the network's graph twice (stateAt and component) for every importer
cycle. Build one immutable controller-position index only after a SUCCESSFUL
topology rebuild; lookup is O(1) during steady state.

Fail-safe: when a topology batch is open, revision differs, a rebuild fails,
or the runtime-to-controller mapping is unexpectedly absent, fall back to the
unaltered live stateAt+component traversal. Never cache NetworkRuntime or
skip conflict/offline/cross-world consistency checks.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
manager = root/"core/TopologyBindingManager.java"
bridge = root/"network/WorldTopologyBridge.java"
m = manager.read_text(encoding="utf-8")
w = bridge.read_text(encoding="utf-8")
marker = "XSXLABS_ACCESSORY_TOPOLOGY_REBUILD_INDEX_V1"

def replace_once(src, old, new, tag):
    n=src.count(old)
    assert n==1, "Topology index source drift " + tag + ": " + str(n)
    return src.replace(old,new,1)

assert marker not in m and marker not in w
assert m.count("public void rebuild() {")==1
assert m.count("this.rebuildCount++;")==1
assert m.count("this.graph.component(start)")==1
assert m.count("this.conflictingControllers = Set.copyOf(conflicts);")==1
assert m.count("this.graph.revision()")==1
assert m.count("this.batchDepth++")==1
assert m.count("this.rebuildPending")==3
assert w.count("public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {")==1

old_method="""   public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {
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
   }"""
assert w.count(old_method)==1, "Accessor must be exactly the verified #273 baseline"

anchor="""   private int batchDepth;
   private boolean rebuildPending;"""
extra="""   private int batchDepth;
   private boolean rebuildPending;

   // XSXLABS_ACCESSORY_TOPOLOGY_REBUILD_INDEX_V1
   // Values are controller POSITIONS, not NetworkRuntime references.
   // A fresh immutable map is published ONLY after a successful rebuild.
   private Map<NetworkGraph.Pos,NetworkGraph.Pos> activeAccessoryControllers = Map.of();
   private long accessoryIndexGraphRevision = -1L;
   private long accessoryIndexRebuildCount = -1L;

   public boolean accessoryIndexReady() {
      return this.batchDepth == 0 && !this.rebuildPending
         && this.accessoryIndexGraphRevision == this.graph.revision()
         && this.accessoryIndexRebuildCount == this.rebuildCount;
   }
   public NetworkGraph.Pos activeAccessoryController(NetworkGraph.Pos pos) {
      return this.activeAccessoryControllers.get(pos);
   }"""
m=replace_once(m,anchor,extra,"class fields")
m=replace_once(m,
  """      HashSet<NetworkGraph.Pos> visited = new HashSet<>();

      for (NetworkGraph.Pos start : this.graph.nodes()) {""",
  """      HashSet<NetworkGraph.Pos> visited = new HashSet<>();
      HashMap<NetworkGraph.Pos,NetworkGraph.Pos> pendingAccessoryControllers = new HashMap<>();

      for (NetworkGraph.Pos start : this.graph.nodes()) {""","rebuild index allocation")
m=replace_once(m,
  """               for (NetworkGraph.Pos nodexx : component) {
                  if (this.drives.containsKey(nodexx)) {""",
  """               for (NetworkGraph.Pos nodexx : component) {
                  pendingAccessoryControllers.put(nodexx,onlyController);
                  if (this.drives.containsKey(nodexx)) {""","one active controller component")
m=replace_once(m,
  """      this.conflictingControllers = Set.copyOf(conflicts);
   }""",
  """      this.conflictingControllers = Set.copyOf(conflicts);
      // Publishing this last also invalidates the old cache after a failed
      // rebuild (rebuildCount incremented before trying to rebuild).
      this.activeAccessoryControllers = Map.copyOf(pendingAccessoryControllers);
      this.accessoryIndexGraphRevision = this.graph.revision();
      this.accessoryIndexRebuildCount = this.rebuildCount;
   }""","publish only after success")

# Retain exact slow path for interim topology changes and unusual controller
# runtime registration timing. The branch must not expose a stale network.
new_method="""   public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {
      WorldTopologyBridge.LevelTopology s = LEVELS.get(level);
      if (s == null) {
         return null;
      } else {
         NetworkGraph.Pos p = toCore(pos);
         // XSXLABS_ACCESSORY_TOPOLOGY_REBUILD_INDEX_V1
         if (s.manager.accessoryIndexReady()) {
            NetworkGraph.Pos controller = s.manager.activeAccessoryController(p);
            if (controller == null) return null; // offline / conflict / absent
            NetworkRuntime cachedOwner = s.controllerRuntimes.get(controller);
            if (cachedOwner != null) return cachedOwner;
            // Unexpected runtime registration gap: use the original live scan.
         }
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
   }"""
w=replace_once(w,old_method,new_method,"bridge method")
assert m.count(marker)==1 and w.count(marker)==1
assert "this.graph.component(start)" in m and "this.rebuildCount++" in m
assert "this.graph.revision()" in m and "this.conflictingControllers = Set.copyOf(conflicts)" in m
assert w.count(new_method)==1, "Patched accessor must occur exactly once"
assert new_method.count("s.manager.stateAt(p)")==1 and new_method.count("s.manager.graph().component(p)")==1
assert "activeAccessoryController(p)" in w
# Mutate neither source unless ALL gates have succeeded.
manager.write_text(m,encoding="utf-8")
bridge.write_text(w,encoding="utf-8")
print("XSXLABS_ACCESSORY_TOPOLOGY_REBUILD_INDEX_V1 PASS: indexed steady-state lookup, live fallback on mutation")
