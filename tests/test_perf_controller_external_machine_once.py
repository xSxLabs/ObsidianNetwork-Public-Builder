#!/usr/bin/env python3
"""Verify Controller device summary patch and duplicate-neighbor equivalence."""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/perf-controller-external-machine-once.py"
FIXTURE=r'''class WorldTopologyBridge {
   public static WorldTopologyBridge.DeviceCounts connectedDeviceCounts(ServerLevel level, NetworkRuntime runtime) {
            int autocrafters = 0;
            Set<NetworkGraph.Pos> component = s.manager.graph().component(controller);
            HashSet<BlockPos> external = new HashSet<>();
            for (NetworkGraph.Pos node : component) {
               BlockPos p = new BlockPos(node.x(), node.y(), node.z());
               for (Direction d : Direction.values()) {
                  BlockPos q = p.relative(d);
                  if (level.hasChunkAt(q) && !component.contains(toCore(q))) {
                     Block b = level.getBlockState(q).getBlock();
                     boolean vanilla = b == Blocks.FURNACE || b == Blocks.BLAST_FURNACE || b == Blocks.SMOKER || b == Blocks.STONECUTTER;
                     boolean ironFurnaces = "ironfurnaces".equals(BuiltInRegistries.BLOCK.getKey(level.getBlockState(q).getBlock()).getNamespace());
                     boolean itemMachine = false;
                     if (!vanilla && !ironFurnaces) {
                        for (Direction side : Direction.values()) {
                           if (level.getCapability(Item.BLOCK, q, side) != null) {
                              itemMachine = true;
                              break;
                           }
                        }
                     }
                     if (vanilla || ironFurnaces || itemMachine) {
                        external.add(q.immutable());
                     }
                  }
               }
            }
            processing = external.size();
   }
   public static List<BlockPos> externalCandidates(ServerLevel level, NetworkRuntime runtime) {return null;}
}'''
DIRS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))


def apply(source):
    with tempfile.TemporaryDirectory() as root:
        p=Path(root)/"dev/obsidiannetwork/network/WorldTopologyBridge.java"
        p.parent.mkdir(parents=True)
        p.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
            env={**os.environ,"V1_SOURCE_ROOT":root})
        return result,p.read_text()


def summary(component, loaded, machines, skip_duplicates):
    visited=set()
    external=set()
    expensive_checks=0
    for x,y,z in component:
        for dx,dy,dz in DIRS:
            q=(x+dx,y+dy,z+dz)
            if q not in loaded or q in component:
                continue
            if skip_duplicates:
                if q in visited:
                    continue
                visited.add(q)
            expensive_checks+=1
            if q in machines:
                external.add(q)
    return external,expensive_checks


class ControllerExternalDedup(unittest.TestCase):
    def test_source_patch_is_fail_closed(self):
        ast.parse(PATCH.read_text())
        r,source=apply(FIXTURE)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertIn("XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1",source)
        self.assertIn("HashSet<BlockPos> checkedExternal = new HashSet<>();",source)
        self.assertIn("!component.contains(toCore(q)) && checkedExternal.add(q.immutable())",source)
        self.assertIn("for (Direction side : directions)",source)
        self.assertIn("BuiltInRegistries.BLOCK.getKey(b)",source)
        self.assertIn("level.getCapability(Item.BLOCK, q, side) != null",source)
        again,identical=apply(source)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(source,identical)
        for old,new in (
            ("external.add(q.immutable());","external.clear();"),
            ("processing = external.size();","processing = 0;"),
            ("level.getCapability(Item.BLOCK, q, side) != null","false"),
            ("!component.contains(toCore(q))","!component.contains(q)"),
        ):
            broken=FIXTURE.replace(old,new)
            bad,after=apply(broken)
            self.assertNotEqual(bad.returncode,0,old)
            self.assertEqual(broken,after)

    def test_4000_graphs_preserve_unique_processing_machine_positions(self):
        rng=random.Random(3018)
        saved_expensive=0
        for _ in range(4000):
            component={(rng.randrange(0,10),rng.randrange(0,4),rng.randrange(0,10))
                       for j in range(rng.randrange(1,65))}
            neighborhood=set(component)
            for x,y,z in component:
                neighborhood.update((x+dx,y+dy,z+dz) for dx,dy,dz in DIRS)
            neighborhood=sorted(neighborhood)
            loaded=set(rng.sample(neighborhood,rng.randrange(len(neighborhood)+1)))
            machines=set(rng.sample(neighborhood,rng.randrange(len(neighborhood)+1)))
            old,naive=summary(component,loaded,machines,False)
            new,deduped=summary(component,loaded,machines,True)
            self.assertEqual(old,new)
            self.assertLessEqual(deduped,naive)
            saved_expensive+=naive-deduped
        self.assertGreater(saved_expensive,0)


if __name__=="__main__":
    unittest.main()
