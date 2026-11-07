"""B1376 verify the actual mod's Reactor is tested, not an Energy Cell proxy."""
from pathlib import Path
import ast
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"features/v176/inject-v176-real-reactor-gametest-1376.py"
FLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
class ReactorIntegration(unittest.TestCase):
 def test_real_reactor_and_port_are_used(self):
  source=SOURCE.read_text("utf8")
  ast.parse(source)
  for marker in (
    "ObsidianNetwork.REACTOR_CONTROLLER",
    "ObsidianNetwork.REACTOR_POWER_PORT",
    "ObsidianNetwork.REACTOR_FUEL_ASSEMBLY",
    "reactor control rod not registered",
    "origin.offset(3,5,3)",
    "x==3&&y>=2&&y<=4&&z==3",
    "ObsidianNetwork.URANIUM_ROD",
    "ObsidianNetwork.REACTOR_FLUID_PORT",
    "ObsidianNetwork.REACTOR_ITEM_PORT",
    "reactor.revalidate(w)",
    "reactor.xsxNetworkSetEnabled(false)",
    "B1380 reactor FE changed during external idle funding",
    "reactor.xsxNetworkSetEnabled(true)",
    "ObsidianNetwork.POWERBANK_INPUT",
    "ObsidianNetwork.POWERBANK_OUTPUT",
    "ObsidianNetwork.ENERGY_CABLE",
    "2_000_000_000",
    "5_000_000",
    "b1376_reactor_energy.nbt",
   ):
   self.assertIn(marker,source)
 def test_real_gametest_mandatory_in_branch_and_absent_in_jar(self):
  flow=FLOW.read_text("utf8")
  self.assertIn('python3 features/v176/inject-v176-real-reactor-gametest-1376.py',flow)
  self.assertIn('test_v176_real_reactor_bank_1376.py',flow)
  for marker in (
    "B1376_REAL_REACTOR_CABLE_BANK_CONSUMER_PASS",
    "B1376_REACTOR_OFF_TWO_BILLION_IDLE_NO_LOSS_PASS",
    "B1376_REACTOR_OFF_BANK_TO_CONSUMER_PASS",
    "B1376_REACTOR_RESTART_BANK_AUTO_RECHARGE_PASS",
   ):
   self.assertIn(marker,flow)
   self.assertIn(marker,SOURCE.read_text("utf8"))
  self.assertIn("rm -f work/src/main/resources/data/obsidiannetwork/structure/b1376_reactor_energy.nbt",flow)
  control=(ROOT/"features/v176/apply-v176-reactor-powerbank-control.py").read_text("utf8")
  self.assertIn("B1380_REACTOR_OFF_BLOCKS_ALL_SERVER_TICKS",control)
  self.assertIn("if(!be.xsxNetworkEnabled)return;",control)
if __name__=="__main__":unittest.main()
