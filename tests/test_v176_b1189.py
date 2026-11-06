"""B1189 source/CI invariants: mute only our mod messages, preserve B1188."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'features/v176/apply-v176-b1189-chat-toggle.py'
W=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text()
class B1189(unittest.TestCase):
 def test_patch_syntax(self):ast.parse(SCRIPT.read_text())
 def test_exact_commands(self):
  s=SCRIPT.read_text()
  for c in ('Commands.literal("xsxlabs")','Commands.literal("chat")',
            'Commands.literal("off")','Commands.literal("on")',
            'Commands.literal("status")'):
   self.assertIn(c,s)
 def test_scoped_to_our_mod_and_player(self):
  s=SCRIPT.read_text()
  for c in ('ClientboundSystemChatPacket',
            'ClientboundSetActionBarTextPacket',
            'WALKER.walk','cls.startsWith("dev.obsidiannetwork.")',
            'p.getUUID()','xsxlabs-muted-chat-players.txt',
            'StandardCopyOption.ATOMIC_MOVE','CONFIRMATION.set(true)'):
   self.assertIn(c,s)
  self.assertIn('V176ChatMutePacketMixin',s)
  self.assertIn('cancellable=true,require=1',s)
  self.assertNotIn('ClientboundPlayerChatPacket',s)
 def test_original_tool_locked(self):
  s=SCRIPT.read_text()
  self.assertIn("len(tool.get('elements',[]))==2318",s)
  self.assertNotIn("MODEL.write_text",s)
 def test_pipeline(self):
  self.assertLess(W.index('apply-v176-b1188-native-3d-multitool.py'),W.index('apply-v176-b1189-chat-toggle.py'))
  self.assertIn("test_v176_b1189.py",W)
if __name__=='__main__':unittest.main()
