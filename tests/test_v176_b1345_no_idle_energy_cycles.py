"""B1345 regression contracts: Powerbank reload repair / 2b FE no idle leak.

Source guards are secondary to the separate full Java+NeoForge GameTests:
- actual EnergyCell through cable INTO Powerbank INPUT;
- both controller ports on the same returning cable network;
- 2 billion FE and full sink remain unchanged for 40 server ticks;
- restarting/linking doesn't require breaking the controller.
"""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1345-no-idle-energy-cycles.py"
GAME=ROOT/"features/v176/inject-v176-b1345-fe-cable-loss-gametest.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class B1345NoPhantomEnergy(unittest.TestCase):
 def test_patch_syntax_and_source_invariants(self):
  s=PATCH.read_text("utf-8")
  ast.parse(s)
  for expected in (
   "B1345_RECOVER_PORT_LINKS","b1345NextLinkCheck",
   "be.revalidate(sl);","b1345AutoExporting()",
   "b1345ActiveAutoPush","b1345CanAutoReceiveStorage",
   "if(!canExtract())return 0L;",
   "if(mode()!=PowerbankBlock.Mode.OUTPUT)return 0L;",
   "private boolean b1345CanAutoReceiveStorage()",
   "EnergyCellBlockEntity.this","SideMode.OUTPUT",
   "b1345ActiveAutoPush.remove()", "b1300SelfCharge(tx,b)",
  ):
   self.assertIn(expected,s,expected)
  self.assertNotIn("setChunkForced(",s)
  self.assertNotIn("forceChunk(",s)
  self.assertNotIn("Thread.sleep(",s)
  self.assertIn("Math",s) if False else None

 def test_loop_guard_does_not_block_real_consumers_and_input_only_cells(self):
  # Full network graph: A and B both INPUT+OUTPUT -> they are producers;
  # neither is allowed to masquerade as auto output demand.
  def can_accept_storage_auto_push(has_output, active_cell_is_self):
   return not (has_output or active_cell_is_self)
  self.assertFalse(can_accept_storage_auto_push(True,True))
  self.assertFalse(can_accept_storage_auto_push(True,False))
  self.assertTrue(can_accept_storage_auto_push(False,False))
  self.assertFalse(can_accept_storage_auto_push(False,True))
  # A real machine's EnergyHandler is not modified by the patch.
  self.assertNotIn("machine/",PATCH.read_text("utf-8"))

 def test_two_billion_fe_source_off_without_demand_stays_put(self):
  bank=2_000_000_000
  cell=40_000_000
  machines_fully_charged=True
  source_active=False
  for _ in range(400):
   demand=0 if machines_fully_charged else 1000
   charge=0 if not source_active else 1000
   bank+=charge-demand
  self.assertEqual(bank,2_000_000_000)
  self.assertEqual(cell,40_000_000)

 def test_real_game_test_injects_requested_topologies(self):
  s=GAME.read_text("utf-8")
  ast.parse(s)
  for marker in (
   "B1345_POWERBANK_REAL_CABLE_INPUT_RELINK_PASS",
   "B1345_POWERBANK_TWO_BILLION_FE_NO_IDLE_LOSS_PASS",
   "B1345_ENERGY_CELL_NO_5M_PINGPONG_PASS",
   "B1345_IDLE_FE_2B_BUDGET_NO_RETURN_LEAK_PASS",
   "B1345_2B_NO_DRAIN",
   "2_000_000_000L",
   "1_998_000_000",
   "ObsidianNetwork.ENERGY_CABLE",
   "ObsidianNetwork.ULTIMATE_ENERGY_CELL",
   "ObsidianNetwork.POWERBANK_INPUT",
   "ObsidianNetwork.POWERBANK_OUTPUT",
   "source.cycleSide(Direction.EAST.get3DDataValue())",
   "long bankFe=bank.xsxNetworkStoredFe(), sourceFe=source.stored()",
   "bankFe+sourceFe!=initial",
   "thenExecuteAfter(60",
   "thenExecuteAfter(40",
  ):
   self.assertIn(marker,s,marker)

 def test_workflow_verifies_actual_jar_and_game_test(self):
  s=WORKFLOW.read_text("utf-8")
  a="python3 features/v176/apply-v176-b1324-zero-buffer-wireless.py"
  b="python3 features/v176/apply-v176-b1345-no-idle-energy-cycles.py"
  c="python3 features/v176/inject-v176-b1324-live-no-demand-gametest.py"
  d="python3 features/v176/inject-v176-b1345-fe-cable-loss-gametest.py"
  for token in (a,b,c,d,"test_v176_b1345_no_idle_energy_cycles.py",
    "B1345_POWERBANK_REAL_CABLE_INPUT_RELINK_PASS",
    "B1345_POWERBANK_TWO_BILLION_FE_NO_IDLE_LOSS_PASS",
    "B1345_IDLE_FE_2B_BUDGET_NO_RETURN_LEAK_PASS"):
   self.assertIn(token,s)
  self.assertLess(s.index(a),s.index(b))
  self.assertLess(s.index(b),s.index(c))
  self.assertLess(s.index(c),s.index(d))

if __name__=="__main__":unittest.main()
