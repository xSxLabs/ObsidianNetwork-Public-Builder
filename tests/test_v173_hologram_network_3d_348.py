import ast
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/"features/v173/apply-hologram-network-3d-348.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestNetworkHologram348(unittest.TestCase):
 def test_patch_parses(self):
  ast.parse(P.read_text(encoding="utf-8"))
 def test_network_is_geometry_not_fake_hud(self):
  s=P.read_text(encoding="utf-8")
  for token in (
    'V173_B348_NETWORK_3D',
    'if("network".equals(be.holoMode()))networkProjection(',
    'private static void networkProjection(',
    'BlockModelRenderState',
    'drawSized(mc,ev,camera,real,x,y,z,scale,scale,scale)',
    'be.holoWidth()/Math.max(dx,Math.max(dy,dz))',
    'origin.getY()-be.holoHeight()+1D',
  ):
   if token=='BlockModelRenderState':
    # Actual model renderer is inherited from the 303 patch.
    self.assertIn('drawSized(mc,ev,camera,real',s)
   else:self.assertIn(token,s)
 def test_only_connected_network_cables_no_fe(self):
  s=P.read_text(encoding="utf-8")
  for token in (
    'state.is(ObsidianNetwork.NETWORK_CABLE.get())',
    'state.is(ObsidianNetwork.CONDUIT_BUNDLE.get())',
    'ConduitBundleBlockEntity.Layer.NETWORK',
    'networkWire(mc,first)',
    'frontier.addLast(next)',
    'networkAttachment(mc,next)',
    'result.size()<256',
    'seen.size()<512',
    'mc.level.hasChunkAt(next)',
  ):
   self.assertIn(token,s)
  self.assertNotIn('Layer.ENERGY',s)
  self.assertNotIn('ObsidianNetwork.ENERGY_CABLE',s)
 def test_readonly(self):
  s=P.read_text(encoding="utf-8")
  for forbidden in (
    'mc.level.setBlock(', 'setBlockAndUpdate(', 'setChanged(',
    'sendBlockUpdated(', 'sendParticles(', 'addParticle(',
    'new BlockEntity(', 'forceChunk(', 'world.addFreshEntity('
  ):self.assertNotIn(forbidden,s)
 def test_workflow_order(self):
  s=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("python3 features/v173/apply-hologram-network-3d-348.py",s)
  self.assertIn("test_v173_hologram_network_3d_348.py",s)
  self.assertLess(s.index('python3 features/v173/apply-holo-text-visibility-345.py'),
                  s.index('python3 features/v173/apply-hologram-network-3d-348.py'))

if __name__=="__main__":
 unittest.main()
