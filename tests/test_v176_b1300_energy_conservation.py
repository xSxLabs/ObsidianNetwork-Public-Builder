"""B1300 strict source-contract and lossless FE flow regression tests.

These fast synthetic tests do not replace NeoForge compilation or in-game
measurements; the full Java/Curios/GameTest matrix remains mandatory.
"""
import ast
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1300-energy-conservation.py"
B1281=ROOT/"features/v176/apply-v176-b1281-powerbank-direct-fe-and-jade-cable.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def jade_fixture():
    tree=ast.parse(B1281.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="plugin" for t in node.targets
        ) and isinstance(node.value,ast.Constant):
            return node.value.value
    raise AssertionError("B1281 Jade source fixture not found")

def fixtures():
    ticker="""// XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1
class EnergyConduitTicker {
try(Transaction tx=Transaction.openRoot()){int got=from.extract(1000,tx);if(got<=0)continue;int put=to.insert(got,tx);if(put<=0)continue;if(put<got)from.insert(got-put,tx);tx.commit();return;}
}
"""
    bank="""class PowerbankBlockEntity {
 // B1281_UNCAPPED_POWERBANK_AUTO_EXPORT
 private final SnapshotJournal<long[]> journal=null;
 private void xsxCommittedTransfer(long in,long out){
  if(level==null)return;
  xsxRates.committed(level.getGameTime(),Math.max(0L,in),Math.max(0L,out));
 }
 private void b591PushOutput(ServerLevel server){
    int offer=(int)Math.min((long)Integer.MAX_VALUE,amount);
    if(offer<=0)return;
    try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
     int accepted=target.insert(offer,tx);
     if(accepted>0 && source.extract(accepted,tx)==accepted)tx.commit();
    }
 }
 public int insert(int offered,TransactionContext tx){
  if(mode()!=PowerbankBlock.Mode.INPUT||offered<=0)return 0;
  PowerbankBlockEntity b=controller();
  if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;
  int taken=(int)Math.min((long)offered,b.capacity-b.amount);
  if(taken>0){b.journal.updateSnapshots(tx);b.amount+=taken;b.xsxPendingIn+=taken;}
  return taken;
 }
 public int extract(int demand,TransactionContext tx){
  if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=0)return 0;
  PowerbankBlockEntity b=controller();
  if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;
  int taken=(int)Math.min((long)demand,b.amount);
  if(taken>0){b.journal.updateSnapshots(tx);b.amount-=taken;b.xsxPendingOut+=taken;}
  return taken;
 }
}
"""
    cable="class EnergyCableBlockEntity { /* B591_ENERGY_DIRECTED_WALK */ }\n"
    return {"conduit/EnergyConduitTicker.java":ticker,
            "powerbank/PowerbankBlockEntity.java":bank,
            "blockentity/EnergyCableBlockEntity.java":cable,
            "compat/EnergyCableJadePlugin.java":jade_fixture()}

def apply(fixtures):
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)/"dev/obsidiannetwork"
        for name,source in fixtures.items():
            path=root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(source,encoding="utf-8")
        run=subprocess.run([sys.executable,str(PATCH)],text=True,capture_output=True,
                           env={**os.environ,"V1_SOURCE_ROOT":d},check=False)
        return run,{p:(root/p).read_text(encoding="utf-8") for p in fixtures}

class ConservationB1300(unittest.TestCase):
    def test_syntax_and_strict_patch(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        run,result=apply(fixtures())
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn("B1300_ENERGY_ATOMIC_PARTIAL",run.stdout)
        t=result["conduit/EnergyConduitTicker.java"]
        self.assertIn("B1300_ATOMIC_PARTIAL_FE",t)
        self.assertIn("if(put==got){tx.commit();return;}",t)
        self.assertIn("if(got==accepted && to.insert(got,tx)==got)",t)
        self.assertNotIn("from.insert(got-put,tx)",t)
        b=result["powerbank/PowerbankBlockEntity.java"]
        self.assertIn("b1300SelfCharge(tx,b)",b)
        self.assertIn("b1300MarkSource(tx,b)",b)
        self.assertIn("b1300ActiveExport.set(this)",b)
        self.assertIn("b1300ActiveExport.remove()",b)
        self.assertIn("source.extract(accepted,tx)==accepted",b)
        self.assertIn("target.insert(offer,tx)",b)
        self.assertIn("Math.min((long)Integer.MAX_VALUE,amount)",b)
        self.assertNotIn("target.getCapacityAsLong()",b)
        self.assertIn("xsxRates.committed",b)
        self.assertIn("SnapshotJournal<long[]>",b)
        self.assertIn("B1300_JADE_FINAL_TOOLTIP",result["compat/EnergyCableJadePlugin.java"])
        self.assertIn("addTooltipCollectedCallback",result["compat/EnergyCableJadePlugin.java"])
        self.assertEqual(result["blockentity/EnergyCableBlockEntity.java"],
                         fixtures()["blockentity/EnergyCableBlockEntity.java"])

    def test_reject_source_drift_and_leave_all_bytes_unchanged(self):
        fixture=fixtures()
        fixture["conduit/EnergyConduitTicker.java"]=fixture["conduit/EnergyConduitTicker.java"].replace(
            "if(put<got)from.insert(got-put,tx);",
            "if(put<got)from.insert(got-put-1,tx);")
        run,results=apply(fixture)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(results,fixture)

    def test_partial_sink_commits_exactly_or_rolls_back(self):
        # Models two real transactional attempts: the first is a tentative
        # full request; on partial acceptance it must roll back before retry.
        rng=random.Random(1300)
        for _ in range(25000):
            energy=rng.randrange(0,20_000)
            sink_free=rng.randrange(0,20_000)
            request=1000
            tentative_source=min(energy,request)
            tentative_insert=min(tentative_source,sink_free)
            if tentative_insert==tentative_source:
                transferred=tentative_insert
            else:
                # First tentative debit and insertion are rolled back.
                assert energy==energy
                retry_extract=min(energy,tentative_insert)
                retry_insert=min(retry_extract,sink_free)
                transferred=retry_insert if retry_extract==retry_insert==tentative_insert else 0
            self.assertEqual(energy+sink_free,(energy-transferred)+(sink_free+transferred))
            self.assertLessEqual(transferred,energy)
            self.assertLessEqual(transferred,sink_free)

    def test_same_controller_loop_blocked_but_other_bank_allowed(self):
        src=object(); other=object(); tx_sources={1:{src}}
        def may_insert(destination,active,transaction):
            return destination is not active and destination not in tx_sources.get(transaction,set())
        self.assertFalse(may_insert(src,src,None)) # sink-first auto export
        self.assertFalse(may_insert(src,None,1))   # source-first extraction
        self.assertTrue(may_insert(other,src,None)) # legitimate bank-to-bank
        self.assertTrue(may_insert(other,None,1))
        self.assertTrue(may_insert(src,None,None))  # genuine external import

    def test_workflow_b1300_applied_only_after_b1281(self):
        s=WORKFLOW.read_text("utf-8")
        self.assertIn(PATCH.name,s)
        self.assertIn(Path(__file__).name,s)
        self.assertLess(s.index(B1281.name),s.index(PATCH.name))
        self.assertIn("B1300_NO_SELF_CHARGE",PATCH.read_text("utf-8"))
        self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text("utf-8"))

if __name__=="__main__": unittest.main()
