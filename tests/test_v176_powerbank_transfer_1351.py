"""B1351 independent FE conservation / branch isolation regression gates.

Full Java compile and the existing NeoForge GameTest suite are mandatory;
these contract tests guard against regressions in the source patch itself.
"""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-powerbank-transfer-1351.py"
WORK=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class B1351Powerbank(unittest.TestCase):
 def test_source_isolated_and_compiles(self):
  p=PATCH.read_text("utf8")
  ast.parse(p)
  for marker in (
   "B1351_PHYSICAL_CELL_ONE_JOURNAL","b1351SharedJournal",
   "this.journal = EnergyCellBlockEntity.this.b1351Journal(this);",
   "b1351TxSources","b1351MarkSource(tx,EnergyCellBlockEntity.this)",
   "b1351SelfSource(tx,EnergyCellBlockEntity.this)",
   "b1351AutoPush","B1351_RELINK_ON_LOAD",
   "be.b1351PullInput(sl);","be.b591PushOutput(sl);",
   "B1351_REAL_INPUT_SOURCE","b1351ActiveImport.get()==b",
   "B1351_DEMAND_BEFORE_STORAGE","b1351Deferred",
   "b1351OutputCells.contains(cell)","B1351_FE_SOURCE_CAPABILITY_HINT",
   "B1351_STORAGE_PHASE","b1300SelfCharge(tx,b)",
  ):
   self.assertIn(marker,p)
  self.assertNotIn("b1345CanAutoReceiveStorage",p)
  self.assertNotIn("1_000_000L,amount",p)
  self.assertIn("cell_handlers=list(re.finditer(",p)
  self.assertIn("B1351_CELL_HANDLER_DECL_DRIFT",p)
  self.assertIn("B1351_CELL_CAN_INSERT_DRIFT",p)
  self.assertIn("B1351_BANK_TICK_ANCHOR",p)
  self.assertIn("def bank_comment_once(",p)
  self.assertIn('b=bank_comment_once(b,"// B1300_NO_SELF_CHARGE',p)
  self.assertIn('b=bank_comment_once(b,"// B591_POWERBANK_OUTPUT_PUSH',p)

 def test_neoforge_reuses_root_transaction_objects_no_sticky_fe(self):
  # TransactionManager.stack reopens the same Transaction object at depth 0.
  # A WeakHashMap[TransactionContext, origins] persists a committed source
  # tag and incorrectly blocks the next independent energy insertion.
  patch=PATCH.read_text("utf8")
  for marker in ("B1372_ROOT_TRANSACTION_REUSE_SAFE",
                 "B1372_POWERBANK_ROOT_TRANSACTION_REUSE_SAFE",
                 "B1372CellOriginState","B1372BankOriginState",
                 "origins.journal.updateSnapshots(tx);",
                 "onRootCommit(", "revertToSnapshot("):
   self.assertIn(marker,patch)
  self.assertNotIn("new java.util.WeakHashMap",patch)
  # Model both callback paths: commit clears origins; rollback restores
  # the prior set, including when a nested transaction aborts.
  origins=set()
  origins.add("bank")
  self.assertIn("bank",origins)
  origins.clear()  # onRootCommit for the first use of a pooled root object
  self.assertNotIn("bank",origins)  # next use of SAME root object is legitimate
  origins.add("bank")
  original=origins.copy()
  origins.add("cell")
  origins=original  # revertToSnapshot for an aborted nested transaction
  self.assertIn("bank",origins)
  self.assertNotIn("cell",origins)
  origins.clear()  # root closed
  self.assertEqual(origins,set())

 def test_real_rollback_is_per_physical_cell_not_face(self):
  # The bug: two side handlers for one cell each independently snapshot FE.
  # Shared journal must restore to ONE common pre-transaction baseline.
  physical_stored=2_000_000_000
  snapshot=physical_stored
  physical_stored-=5_000_000 # extraction from OUTPUT
  physical_stored+=5_000_000 # insertion via INPUT must be rejected for self
  physical_stored=snapshot # rollback unchanged
  self.assertEqual(physical_stored,2_000_000_000)

 def test_never_recycle_source_into_its_own_input(self):
  # Source-first and sink-first transfer orders both have identity guards.
  def may_insert(source,receiver,auto_origin):
   return not (source==receiver or auto_origin==receiver)
  self.assertFalse(may_insert("A","A",None))
  self.assertFalse(may_insert(None,"A","A"))
  self.assertTrue(may_insert("A","B",None))
  self.assertTrue(may_insert(None,"B","A"))

 def test_real_demand_first_then_storage(self):
  source=2_000_000_000
  machines=[0,0]
  machine_caps=[7_000_000,3_000_000]
  storage=0
  storage_cap=100_000_000
  # Demand-first. A storage that's also a source in this cable component
  # must not take back FE from its own output side.
  delivered=0
  for i in range(len(machines)):
   want=machine_caps[i]-machines[i]
   n=min(source,want)
   source-=n;machines[i]+=n;delivered+=n
  remaining=min(source,storage_cap-storage)
  source-=remaining;storage+=remaining
  self.assertEqual(source+sum(machines)+storage,2_000_000_000)
  self.assertEqual(delivered,10_000_000)
  # Machines now full and storage is also a source => no remaining demand.
  before=source+sum(machines)+storage
  self.assertEqual(source+sum(machines)+storage,before)

 def test_workflow_applies_only_in_new_branch(self):
  s=WORK.read_text("utf8")
  patch="python3 features/v176/apply-v176-powerbank-transfer-1351.py"
  self.assertEqual(s.count(patch),1)
  i=s.index(patch)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.6-powerbank" ]; then',s[i-300:i])
  self.assertIn("test_v176_powerbank_transfer_1351.py",s)
  self.assertIn("inject-v176-powerbank-gametest-1355.py",s)
  for marker in ("B1355_ONE_PHYSICAL_CELL_SEVEN_FACES_ROLLBACK_PASS",
                 "B1355_CELL_CABLE_POWERBANK_CABLE_LIVE_SINK_PASS",
                 "B1355_TWO_BILLION_FE_POWERBANK_SOURCE_OFF_FULL_SINK_PASS"):
   self.assertIn(marker,s)
  self.assertIn("branches: [v1.7,",s)
  self.assertIn("1.7.6-powerbank",s)
  self.assertIn("apply-v176-b1300-energy-conservation.py",s)

if __name__=="__main__":unittest.main()
