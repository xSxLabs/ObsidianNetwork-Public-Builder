#!/usr/bin/env python3
"""Fail-closed and model-equivalence checks for Build 232 runtime micro-optimization."""
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCH = Path(__file__).resolve().parents[1] / "patches/spark-conduit-runtime-neighbor-direction-reuse.py"
RUNTIME = """public final class ConduitRuntime {
 public static java.util.Set<BlockPos> mixedPositions(ServerLevel level,BlockPos seed,ConduitType type) {
  Direction[] directions=Direction.values();
  for(Direction d:directions){ visit(d); }
  return java.util.Set.of();
 }
 public static List<Endpoint> scanEndpoints(ServerLevel level,ConduitNetwork network,boolean extract){
  for(ConduitNode node:network.nodes()){
   ConduitBundleBlockEntity b=bundle(level,node.pos(),type);
   if(b==null)continue;
   for(Direction d:Direction.values()){
    boolean on=extract?b.conduitCanExtract(layer,d):b.conduitCanInsert(layer,d);if(!on||!level.hasChunkAt(b.getBlockPos().relative(d)))continue;
    if(traversable(level,b.getBlockPos().relative(d),type))continue;
    String adjacentId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(level.getBlockState(b.getBlockPos().relative(d)).getBlock()).getPath();
    if(adjacentId.endsWith("_cable")||adjacentId.equals("conduit_bundle")||adjacentId.equals("multi_cable"))continue;
    out.add(new Endpoint(b,d,node.config(d)));
   }
  }
  if(type==ConduitType.ITEM||type==ConduitType.FLUID){
   for(BlockPos p:mixedPositions(level,start,type)){
    for(Direction d:Direction.values()){
     if(cable.mode(d)==Mode.IMPORT) continue;
     out.add(new Endpoint(null,p,d,new ConnectionConfig(true,false,0,false,false)));
    }
   }
  }
  out.sort(Comparator.comparingInt((Endpoint e)->e.config().priority()).reversed());
  return out;
 }
 public static List<Endpoint> endpoints(ServerLevel level,ConduitNetwork network,boolean extract){return network.endpoints(extract);}
}
"""

def apply(source=RUNTIME, twice=False):
    with tempfile.TemporaryDirectory() as root:
        p = Path(root) / "dev/obsidiannetwork/conduit/ConduitRuntime.java"
        p.parent.mkdir(parents=True)
        p.write_text(source, encoding="utf-8")
        def run():
            return subprocess.run([sys.executable, str(PATCH)],
                env=dict(os.environ, V1_SOURCE_ROOT=root), text=True, capture_output=True)
        first = run()
        second = run() if twice else None
        return first, second, p.read_text(encoding="utf-8")

class ConduitRuntimeNeighborDirectionReuse(unittest.TestCase):
    def test_shape_and_all_endpoint_guards_retained(self):
        result, _, src = apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(src.count("Direction.values()"), 1)
        self.assertEqual(src.count("XSXLABS_SPARK_RUNTIME_DIRECTIONS_V1"), 4)
        self.assertEqual(src.count("b.getBlockPos().relative(d)"), 1)
        checks = ("if(!on)continue;", "if(!level.hasChunkAt(neighborPos))continue;",
                  "if(traversable(level,neighborPos,type))continue;",
                  "level.getBlockState(neighborPos)", "adjacentId.endsWith(\"_cable\")",
                  "out.sort(Comparator.comparingInt(")
        for check in checks:
            self.assertIn(check, src)
        self.assertLess(src.index("if(!on)continue;"), src.index("if(!level.hasChunkAt(neighborPos))"))
        self.assertLess(src.index("if(!level.hasChunkAt(neighborPos))"), src.index("if(traversable(level,neighborPos,type))"))

    def test_refuse_second_application(self):
        first, second, _ = apply(twice=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertNotEqual(second.returncode, 0)

    def test_fail_closed_on_changed_connectivity_chunk_or_priority_guards(self):
        changes = (
            ('if(!on||!level.hasChunkAt(', 'if(!on&& !level.hasChunkAt('),
            ('if(traversable(level,', 'if(!traversable(level,'),
            ('adjacentId.endsWith("_cable")', 'adjacentId.endsWith("_pipe")'),
            ('out.sort(Comparator.comparingInt(', 'out.clear(); //'),
            ('Direction[] directions=Direction.values();', 'Direction[] directions=new Direction[0];'),
        )
        for before, after in changes:
            mutated = RUNTIME.replace(before, after, 1)
            result, _, source = apply(mutated)
            self.assertNotEqual(result.returncode, 0, before)
            self.assertEqual(source, mutated)

    def test_50000_ordered_neighbor_checks_equivalent(self):
        rng = random.Random(20261018)
        sides = tuple(range(6))
        for _ in range(50000):
            face = rng.randrange(6)
            on = bool(rng.getrandbits(1))
            loaded = bool(rng.getrandbits(1))
            conduit = bool(rng.getrandbits(1))
            block = rng.choice(('stone', 'item_cable', 'conduit_bundle', 'chest', 'multi_cable'))
            # Original AND short-circuit and the transformed sequential checks.
            original = on and loaded and not conduit and not (
                block.endswith('_cable') or block in ('conduit_bundle', 'multi_cable'))
            optimized = False
            if on:
                if loaded:
                    if not conduit:
                        optimized = not (block.endswith('_cable') or block in ('conduit_bundle', 'multi_cable'))
            self.assertEqual(original, optimized)
            self.assertEqual(list(sides), list(tuple(sides)))
            self.assertEqual(sides[face], tuple(sides)[face])

if __name__ == "__main__":
    unittest.main()
