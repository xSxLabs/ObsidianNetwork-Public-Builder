#!/usr/bin/env python3
"""Fail-closed patch fixture + randomized equivalence of autocrafter counting.

Model checks the OLD per-node runtimeForNode traversal and the new single-
component traversal against thousands of graph/node/world combinations.
These Python checks are additive to compiled Java GameTests with 50 drives.
"""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/perf-autocrafter-count-component-once.py"
OLD=r'''   public static int autocrafterCount(ServerLevel level, NetworkRuntime runtime) {
      WorldTopologyBridge.LevelTopology s = LEVELS.get(level);
      if (s != null && runtime != null) {
         HashSet<NetworkGraph.Pos> seen = new HashSet<>();

         for (NetworkGraph.Pos p : s.autocrafters) {
            if (runtimeForNode(s, p) == runtime) {
               seen.add(p);
            }
         }

         for (NetworkGraph.Pos px : s.manager.graph().nodes()) {
            if (!seen.contains(px) && runtimeForNode(s, px) == runtime) {
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
      } else {
         return 0;
      }
   }

   '''
TAIL="   public static int autoChiselerCount(ServerLevel level, NetworkRuntime runtime) { return 0; }"
DIRECTIONS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))


def neighbors(p):
    return [(p[0]+dx,p[1]+dy,p[2]+dz) for dx,dy,dz in DIRECTIONS]


def old_count(components, controllers, registered, blocks, loaded, runtime):
    # Reference: runtimeForNode checks that precisely one owning controller
    # belongs to the node's live component, then walks that whole component.
    nodes=set().union(*components) if components else set()
    def node_runtime(p):
        if p not in nodes:
            return None
        for comp in components:
            if p in comp:
                owners=[controllers[q] for q in comp if q in controllers]
                return owners[0] if len(owners)==1 else None
        return None
    seen={p for p in registered if node_runtime(p)==runtime}
    for p in nodes:
        if p not in seen and node_runtime(p)==runtime:
            if p in loaded and p in blocks:
                seen.add(p)
            for q in neighbors(p):
                if q in loaded and q in blocks:
                    seen.add(q)
    return len(seen)


def new_count(components, controllers, registered, blocks, loaded, runtime):
    # Same as patched Java: live runtime identity and ACTIVE owner components;
    # never memoizes a previous tick or persists component membership.
    owner_nodes=set()
    for controller, identity in controllers.items():
        if identity!=runtime:
            continue
        for comp in components:
            if controller in comp and sum(x in controllers for x in comp)==1:
                owner_nodes.update(comp)
    if not owner_nodes:
        return 0
    seen=registered & owner_nodes
    # Original graph.nodes() enumeration order matters: seen may contain
    # neighboring graph nodes before reaching them. Preserve it exactly.
    nodes=set().union(*components) if components else set()
    for p in nodes:
        if p not in seen and p in owner_nodes:
            if p in loaded and p in blocks:
                seen.add(p)
            for q in neighbors(p):
                if q in loaded and q in blocks:
                    seen.add(q)
    return len(seen)


def run_patch(source):
    with tempfile.TemporaryDirectory() as folder:
        file=Path(folder)/"dev/obsidiannetwork/network/WorldTopologyBridge.java"
        file.parent.mkdir(parents=True)
        file.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
            env={**os.environ,"V1_SOURCE_ROOT":folder})
        return result,file.read_text()


class RuntimeComponentCountTests(unittest.TestCase):
    def test_actual_patch_applies_exactly_once_and_rejects_drift(self):
        fixture="class WorldTopologyBridge {\n"+OLD+TAIL+"\n}"
        p,after=run_patch(fixture)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        self.assertEqual(after.count("XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1"),1)
        self.assertIn("ownerNodes.addAll(s.manager.graph().component(controllerPos))",after)
        self.assertIn("if (ownerNodes.isEmpty()) return 0;",after)
        self.assertIn("if (ownerNodes.contains(p))",after)
        self.assertIn("for (NetworkGraph.Pos px : s.manager.graph().nodes())",after)
        self.assertIn("!seen.contains(px) && ownerNodes.contains(px)",after)
        self.assertIn("level.hasChunkAt(q)",after)
        self.assertIn("seen.add(qp);",after)
        self.assertNotIn("runtimeForNode(s, px) == runtime",after)
        repeat,same=run_patch(after)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual(same,after)
        for old,new in (
            ("seen.add(qp);","seen.clear();"),
            ("level.hasChunkAt(q)","true"),
            ("s.autocrafters","s.invalid"),
            ("runtimeForNode(s, px) == runtime","true"),
        ):
            broken=fixture.replace(old,new)
            failure,unchanged=run_patch(broken)
            self.assertNotEqual(failure.returncode,0,old)
            self.assertEqual(unchanged,broken)

    def test_randomized_exact_count_equivalence_loaded_neighbors_and_conflicts(self):
        rng=random.Random(30017)
        for iteration in range(4000):
            # Nonoverlapping 3D components model disconnected cables/drives,
            # network splits, active/conflicting controllers and same runtime
            # owner on independently active components.
            components=[]
            all_nodes=set()
            base=0
            for _ in range(rng.randrange(1,7)):
                size=rng.randrange(1,25)
                comp={(base+i,0,0) for i in range(size)}
                base+=size+10
                components.append(comp); all_nodes.update(comp)
            controllers={}
            for comp in components:
                for p in rng.sample(sorted(comp),rng.randrange(0,min(4,len(comp))+1)):
                    controllers[p]=rng.choice(("A","B"))
            available=set(all_nodes)
            for p in all_nodes:
                available.update(neighbors(p))
            registered=set(rng.sample(sorted(available),rng.randrange(0,min(12,len(available))+1)))
            blocks=set(rng.sample(sorted(available),rng.randrange(0,min(40,len(available))+1)))
            loaded=set(rng.sample(sorted(available),rng.randrange(0,len(available)+1)))
            for identity in ("A","B","NONE"):
                a=old_count(components,controllers,registered,blocks,loaded,identity)
                b=new_count(components,controllers,registered,blocks,loaded,identity)
                self.assertEqual(a,b,(iteration,identity,a,b,components,controllers))

    def test_same_tick_topology_changes_do_not_retain_results(self):
        a={(0,0,0),(1,0,0),(2,0,0)}
        b={(50,0,0),(51,0,0)}
        comps=[a,b]
        owner={(0,0,0):"A"}
        registered={(1,0,0)}
        blocks={(2,0,0),(51,0,0)}
        loaded=a|b
        for state in (
            (comps,owner,registered,blocks,loaded),
            (comps,{**owner,(50,0,0):"A"},registered,blocks,loaded),
            (comps,{**owner,(1,0,0):"B"},registered,blocks,loaded),
            ([a|b],owner,registered,blocks,loaded),
            (comps,owner,registered,blocks,loaded-{(2,0,0)}),
        ):
            self.assertEqual(old_count(*state,"A"),new_count(*state,"A"))


if __name__=="__main__":
    unittest.main()
