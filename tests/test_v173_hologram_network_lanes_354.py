import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-hologram-network-lanes-354.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestHologramNetworkLanes354(unittest.TestCase):
 def test_patch_syntax(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
 def test_bundle_uses_true_network_conductor_model(self):
  s=PATCH.read_text(encoding="utf-8")
  for item in (
    'V173_B354_BUNDLE_NETWORK_LANE',
    'real.is(ObsidianNetwork.CONDUIT_BUNDLE.get())',
    'ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState()',
    'BlockState real=node.state()',
    'V173_B354_ENDPOINT_DRIFT',
    'path.equals("network_terminal")',
    'path.equals("network_drive")',
    'path.equals("network_crafting_terminal")',
  ):
   self.assertIn(item,s)
  self.assertNotIn('ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState()',s)
 def test_loaded_topology_is_bounded(self):
  s=PATCH.read_text(encoding="utf-8")
  for marker in (
    'V173_B354_CONNECTED_REACH','<=32L','<=24L',
    'result.size()<384','seen.size()<768',
    'frontier.addLast(next)',
  ):self.assertIn(marker,s)
  self.assertNotIn('forceChunk(',s)
  self.assertNotIn('setBlock(',s)
  self.assertNotIn('addFreshEntity(',s)
 def test_workflow_order(self):
  s=WF.read_text(encoding="utf-8")
  self.assertIn('python3 features/v173/apply-hologram-network-lanes-354.py',s)
  self.assertIn('test_v173_hologram_network_lanes_354.py',s)
  self.assertLess(s.index('python3 features/v173/apply-vision-holo-polish-351.py'),
                  s.index('python3 features/v173/apply-hologram-network-lanes-354.py'))

if __name__=="__main__":unittest.main()
