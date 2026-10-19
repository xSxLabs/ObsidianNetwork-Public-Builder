#!/usr/bin/env python3
"""Mutation/fail-closed plus 6000 chunk boundary and 4000 registry equivalence cases."""
import os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"patches/perf-spark-batched-live-chunk-registry-guards.py"
BRIDGE="""class WorldTopologyBridge {
 // XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1
 // XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1
 public static int autocrafterCount(ServerLevel level, NetworkRuntime runtime) {
 for(var px:s.manager.graph().nodes()) {
 BlockPos bp = new BlockPos(px.x(), px.y(), px.z());
 if (level.hasChunkAt(bp) && level.getBlockState(bp).is((Block)ObsidianNetwork.AUTOCRAFTER.get())) {seen.add(px);}
 for(Direction d:Direction.values()){
 BlockPos q=bp.relative(d);
 if (level.hasChunkAt(q) && level.getBlockState(q).is((Block)ObsidianNetwork.AUTOCRAFTER.get())) {seen.add(toCore(q));}
 } }
 return seen.size();
 }
 public static int autoChiselerCount(ServerLevel level, NetworkRuntime runtime) {return 0;}
 public static WorldTopologyBridge.DeviceCounts connectedDeviceCounts(ServerLevel level, NetworkRuntime runtime) {
 for(var node:component) {
 BlockPos p = new BlockPos(node.x(), node.y(), node.z());
 for(Direction d:Direction.values()){
 BlockPos q=p.relative(d);
 if (level.hasChunkAt(q) && !component.contains(toCore(q)) && checkedExternal.add(q.immutable())) {
 external.add(q.immutable());}
 } }
 return null;
 }
 public static List<BlockPos> externalCandidates(ServerLevel level, NetworkRuntime runtime) {return null;}
}"""
CONDUIT="""class ConduitRuntime {
 // XSXLABS_SPARK_CONDUIT_RUNTIME_REUSE_V1
 public static List<Endpoint> scanEndpoints(ServerLevel level,ConduitNetwork network,boolean extract){
 ArrayList<Endpoint> out=new ArrayList<>();ConduitType type=network.type();var layer=layer(type);
 for(var node:network.nodes()){
 for(var d:Direction.values()){
 BlockPos neighborPos=node.pos().relative(d);
 if(!level.hasChunkAt(neighborPos))continue;
 if(traversable(level,neighborPos,type))continue;
 String adjacentId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(level.getBlockState(neighborPos).getBlock()).getPath();
 if(adjacentId.endsWith("_cable")||adjacentId.equals("conduit_bundle")||adjacentId.equals("multi_cable"))continue;
 } } return out;
 }
 public static List<Endpoint> endpoints(boolean extract){return null;}
}"""
def run(w=BRIDGE,c=CONDUIT):
 with tempfile.TemporaryDirectory() as folder:
  base=Path(folder)/"dev/obsidiannetwork"
  (base/"network").mkdir(parents=True)
  (base/"conduit").mkdir(parents=True)
  wp=base/"network/WorldTopologyBridge.java"
  cp=base/"conduit/ConduitRuntime.java"
  wp.write_text(w);cp.write_text(c)
  r=subprocess.run([sys.executable,str(SCRIPT)],env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
  return r,wp.read_text(),cp.read_text()
class ScanGuards(unittest.TestCase):
 def test_source_gates_and_atomic_mutation_failures(self):
  r,w,c=run()
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual(w.count("XSXLABS_SPARK_LIVE_SCAN_GUARDS_V1"),2)
  self.assertEqual(c.count("XSXLABS_SPARK_LIVE_SCAN_GUARDS_V1"),1)
  for s in ("xsxCenterChunkLoaded=level.hasChunkAt(bp)","xsxCenterChunkLoaded=level.hasChunkAt(p)",
            "level.hasChunkAt(q)","checkedExternal.add(q.immutable())"):
   self.assertIn(s,w)
  for s in ("java.util.IdentityHashMap","xsxPathMemo.put(xsxNeighborBlock,adjacentId)",
            "level.getBlockState(neighborPos)","adjacentId.endsWith(\"_cable\")"):
   self.assertIn(s,c)
  second,w2,c2=run(w,c)
  self.assertNotEqual(second.returncode,0)
  self.assertEqual((w2,c2),(w,c))
  for badw,badc in (
   (BRIDGE.replace("checkedExternal.add(q.immutable())","checkedExternal.clear()"),CONDUIT),
   (BRIDGE.replace("level.hasChunkAt(bp)","true"),CONDUIT),
   (BRIDGE,CONDUIT.replace("adjacentId.endsWith(\"_cable\")","false")),
   (BRIDGE,CONDUIT.replace("level.hasChunkAt(neighborPos)","true"))):
   r,afterw,afterc=run(badw,badc)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual((afterw,afterc),(badw,badc))
 def test_6000_random_chunk_boundaries(self):
  rng=random.Random(30619)
  dirs=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
  for _ in range(6000):
   x,y,z=(rng.randrange(-256,257),rng.randrange(-63,321),rng.randrange(-256,257))
   cx,cz=x>>4,z>>4
   positions={(cx,cz)}|{((x+dx)>>4,(z+dz)>>4) for dx,dy,dz in dirs}
   loaded={p for p in positions if rng.randrange(2)}
   for dx,dy,dz in dirs:
    q=(x+dx,z+dz); qc=(q[0]>>4,q[1]>>4)
    baseline=qc in loaded
    patched=((cx,cz) in loaded) if qc==(cx,cz) else (qc in loaded)
    self.assertEqual(baseline,patched)
 def test_4000_immutable_block_registry_memo_cases(self):
  rng=random.Random(30620)
  paths=("conduit_bundle","multi_cable","energy_cable","another_cable","furnace","machine","auto_chiseler")
  for _ in range(4000):
   blocks=[rng.choice(paths) for i in range(rng.randrange(1,80))]
   seen={}
   for block in blocks:
    direct=block.endswith("_cable") or block in ("conduit_bundle","multi_cable")
    path=seen.setdefault(block,block)
    memo=path.endswith("_cable") or path in ("conduit_bundle","multi_cable")
    self.assertEqual(direct,memo)
if __name__=="__main__":
 unittest.main()
