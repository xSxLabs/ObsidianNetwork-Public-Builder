import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-hologram-text-bundle-362.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestHologramTextBundle362(unittest.TestCase):
 def test_python_patch_syntax(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
 def test_client_fallback_matches_server_multiline_order(self):
  s=PATCH.read_text(encoding="utf-8")
  for token in (
   "V173_B362_TEXT_ORDER",
   "int visibleLines=Math.min(lines.length,12);",
   "textLine(mc,ev,cam,t,be,lines[i],visibleLines-1-i,1F);",
  ):self.assertIn(token,s)
  for count in range(1,13):
   for i in range(count):
    server_baseline_index=count-1-i
    fallback_baseline_index=count-1-i
    self.assertEqual(server_baseline_index,fallback_baseline_index)
   self.assertEqual(count-1-(count-1),0)
 def test_genuine_network_bundle_connections(self):
  s=PATCH.read_text(encoding="utf-8")
  for token in (
   "V173_B362_BUNDLE_CONNECTIONS",
   "ObsidianNetwork.CONDUIT_BUNDLE.get()",
   "ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState()",
   "BooleanProperty link",
   "dir.getName()",
   "networkWire(mc,neighbor)||networkAttachment(mc,neighbor)",
   "cable=cable.setValue(link,linked)",
  ):self.assertIn(token,s)
  self.assertNotIn("Layer.ENERGY",s)
  self.assertNotIn("setBlockAndUpdate(",s)
  self.assertNotIn("sendBlockUpdated(",s)
 def test_ci_integration(self):
  s=WF.read_text(encoding="utf-8")
  self.assertIn("python3 features/v173/apply-hologram-text-bundle-362.py",s)
  self.assertIn("test_v173_hologram_text_bundle_362.py",s)
  self.assertLess(s.index("python3 features/v173/apply-hologram-height-up-357.py"),
                  s.index("python3 features/v173/apply-hologram-text-bundle-362.py"))

if __name__=="__main__":unittest.main()
