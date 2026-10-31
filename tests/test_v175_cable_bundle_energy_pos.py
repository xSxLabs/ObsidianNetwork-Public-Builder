#!/usr/bin/env python3
"""B624 Cable Bundle energy hot-path shape, rejection and equivalence tests."""
import os, random, subprocess, sys, tempfile, unittest
from pathlib import Path

PATCH=Path(__file__).resolve().parents[1]/"patches/v175-cable-bundle-node-position-fastpath.py"
SOURCE="""public final class EnergyConduitTicker implements ConduitTicker {
 // XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1
 // XSXLABS_SPARK_CONDUIT_STATIC_DIRECTIONS_V1
 // XSXLABS_SPARK_TICKER_NEIGHBOR_POS_REUSE_V1
 public void tick(ServerLevel level,ConduitNetwork network){
  if(network.type()!=ConduitType.ENERGY||level.getGameTime()%5!=0)return;
  java.util.ArrayList<ConduitRuntime.Endpoint> connected=new java.util.ArrayList<>();
  for(var node:network.nodes()){
   ConduitBundleBlockEntity bundle=ConduitRuntime.bundle(level,node.pos(),ConduitType.ENERGY);
   if(bundle==null)continue;
   for(net.minecraft.core.Direction d:CONDUIT_SCAN_SIDES){
    net.minecraft.core.BlockPos neighborPos=bundle.getBlockPos().relative(d);
    if(ConduitRuntime.bundle(level,neighborPos,ConduitType.ENERGY)!=null)continue;
    EnergyHandler candidate=level.getCapability(Capabilities.Energy.BLOCK,neighborPos,d.getOpposite());
    if(candidate==null)continue;
    connected.add(new ConduitRuntime.Endpoint(bundle,d,node.config(d)));
   }
  }
  if(connected.size()<2)return;
  try(Transaction tx=Transaction.openRoot()){
   int got=from.extract(1000,tx);
   int put=to.insert(got,tx);
   from.insert(got-put,tx);
   tx.commit();return;
  }
 }
}
"""

def apply(source=SOURCE):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"dev/obsidiannetwork/conduit/EnergyConduitTicker.java"
        p.parent.mkdir(parents=True)
        p.write_text(source,encoding="utf-8")
        r=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=d),text=True,capture_output=True)
        return r,p.read_text(encoding="utf-8")

class BundleEnergyNodeFastPath(unittest.TestCase):
    def test_shape_and_live_checks_intact(self):
        r,s=apply()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("V175_B624_CABLE_BUNDLE_NODE_POSITION_HOIST",s)
        self.assertIn("xsxBundleNodePos=bundle.getBlockPos()",s)
        self.assertIn("neighborPos=xsxBundleNodePos.relative(d)",s)
        for t in ("network.nodes()","ConduitRuntime.bundle(level,node.pos(),ConduitType.ENERGY)",
                  "ConduitRuntime.bundle(level,neighborPos,ConduitType.ENERGY)",
                  "getCapability(Capabilities.Energy.BLOCK,neighborPos,d.getOpposite())",
                  "from.extract(1000,tx)","to.insert(got,tx)",
                  "from.insert(got-put,tx)","tx.commit();return;"):
            self.assertIn(t,s)
    def test_fail_closed_after_mutation(self):
        for before,after in (
          ("from.extract(1000,tx)","from.extract(2000,tx)"),
          ("to.insert(got,tx)","to.insert(got*2,tx)"),
          ("if(connected.size()<2)return;","if(connected.size()<1)return;"),
          ("getCapability(Capabilities.Energy.BLOCK,","getCapability(Capabilities.ItemHandler.BLOCK,"),
          ("CONDUIT_SCAN_SIDES","Direction.values()"),
        ):
            mod=SOURCE.replace(before,after,1)
            r,s=apply(mod)
            self.assertNotEqual(r.returncode,0,before)
            self.assertEqual(s,mod)
    def test_200000_node_face_positions_identical(self):
        rnd=random.Random(20261031)
        dirs=((0,-1,0),(0,1,0),(0,0,-1),(0,0,1),(-1,0,0),(1,0,0))
        for _ in range(200000):
            pos=(rnd.randrange(-3000,3000),rnd.randrange(-64,321),rnd.randrange(-3000,3000))
            face=rnd.randrange(6)
            old=tuple(pos[k]+dirs[face][k] for k in range(3))
            reused=pos
            new=tuple(reused[k]+dirs[face][k] for k in range(3))
            self.assertEqual(old,new)
    def test_cannot_double_apply(self):
        a,s=apply()
        self.assertEqual(a.returncode,0,a.stderr)
        b,t=apply(s)
        self.assertNotEqual(b.returncode,0)
        self.assertEqual(t,s)

if __name__=="__main__":unittest.main()
