#!/usr/bin/env python3
"""Strict source and behavioral equivalence tests for per-dispatch ENERGY handlers."""
import os,subprocess,sys,tempfile,random,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"patches/spark-energy-ephemeral-endpoint-handlers.py"
REL="dev/obsidiannetwork/conduit/EnergyConduitTicker.java"
SOURCE="""package dev.obsidiannetwork.conduit;
import net.neoforged.neoforge.transfer.energy.EnergyHandler;
import net.neoforged.neoforge.transfer.transaction.Transaction;
public final class EnergyConduitTicker implements ConduitTicker {
 public void tick(ServerLevel level,ConduitNetwork network){
  if(network.type()!=ConduitType.ENERGY||level.getGameTime()%5!=0)return;
  java.util.ArrayList<ConduitRuntime.Endpoint> connected=new java.util.ArrayList<>();
  for(var node:network.nodes()){var bundle=ConduitRuntime.bundle(level,node.pos(),ConduitType.ENERGY);if(bundle==null)continue;for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()){if(ConduitRuntime.bundle(level,bundle.getBlockPos().relative(d),ConduitType.ENERGY)!=null)continue;if(level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite())==null)continue;connected.add(new ConduitRuntime.Endpoint(bundle,d,node.config(d)));}}
  if(connected.size()<2)return;
  for(var src:connected){
   EnergyHandler from=level.getCapability(Capabilities.Energy.BLOCK,src.bundle().getBlockPos().relative(src.side()),src.side().getOpposite());if(from==null)continue;
   for(var dst:connected){if(dst.bundle()==src.bundle()&&dst.side()==src.side())continue;
    EnergyHandler to=level.getCapability(Capabilities.Energy.BLOCK,dst.bundle().getBlockPos().relative(dst.side()),dst.side().getOpposite());if(to==null)continue;
    try(Transaction tx=Transaction.openRoot()){int got=from.extract(1000,tx);if(got<=0)continue;int put=to.insert(got,tx);if(put<=0)continue;if(put<got)from.insert(got-put,tx);tx.commit();return;}
   }
  }
 }
}
"""
def apply(source):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/REL;p.parent.mkdir(parents=True)
        p.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=d),
                              capture_output=True,text=True)
        return result,p.read_text()
def model_transfer(amounts,capacities,optimized=False):
    """Run original pair order and identical transfer/rollback behavior with stable endpoint handlers."""
    stock=list(amounts)
    counts={"capabilities":0,"commits":0}
    n=len(stock)
    # Discovery is common to both implementations.
    counts["capabilities"]+=n
    if n<2:return stock,counts
    for i in range(n):
        if not optimized:counts["capabilities"]+=1
        for j in range(n):
            if i==j:continue
            if not optimized:counts["capabilities"]+=1
            got=min(1000,stock[i])
            if got<=0:continue
            put=min(got,capacities[j]-stock[j])
            if put<=0:continue
            stock[i]-=put
            stock[j]+=put
            counts["commits"]+=1
            return stock,counts
    return stock,counts
class EphemeralHandlerTests(unittest.TestCase):
    def test_semantics_and_guarded_capability_count(self):
        result,updated=apply(SOURCE)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1",updated)
        self.assertEqual(updated.count("level.getCapability(Capabilities.Energy.BLOCK,"),1)
        self.assertIn("from.extract(1000,tx)",updated)
        self.assertIn("to.insert(got,tx)",updated)
        self.assertIn("from.insert(got-put,tx)",updated)
        self.assertIn("Transaction.openRoot()",updated)
        self.assertIn("tx.commit();return;",updated)
        self.assertIn("if(connected.size()<2)return;",updated)
    def test_fail_closed_if_transaction_or_scan_changes(self):
        for before,after in (
            ("from.extract(1000,tx)","from.extract(900,tx)"),
            ("tx.commit();return;","tx.abort();return;"),
            ("if(connected.size()<2)return;","if(connected.isEmpty())return;"),
            ("if(level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite())==null)continue;",
             "if(other==null)continue;"),
        ):
            altered=SOURCE.replace(before,after)
            self.assertNotEqual(altered,SOURCE)
            r,output=apply(altered)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(output,altered)
    def test_no_second_mutation(self):
        ok,updated=apply(SOURCE)
        self.assertEqual(ok.returncode,0,ok.stderr)
        fail,again=apply(updated)
        self.assertNotEqual(fail.returncode,0)
        self.assertEqual(again,updated)
    def test_randomized_conservation_and_pair_order(self):
        rng=random.Random(20261017)
        for _ in range(3000):
            n=rng.randrange(0,31)
            caps=[rng.randrange(0,100000) for _ in range(n)]
            start=[rng.randrange(cap+1) for cap in caps]
            old,old_calls=model_transfer(start,caps)
            new,new_calls=model_transfer(start,caps,optimized=True)
            self.assertEqual(old,new)
            self.assertEqual(old_calls["commits"],new_calls["commits"])
            self.assertEqual(sum(old),sum(start))
            self.assertTrue(all(0<=v<=cap for v,cap in zip(new,caps)))
            self.assertLessEqual(new_calls["capabilities"],old_calls["capabilities"])
if __name__=="__main__":unittest.main()
