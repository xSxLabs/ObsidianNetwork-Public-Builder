#!/usr/bin/env python3
"""B1652 native team GUI: compiled packet, input validation, map access."""
import ast,os,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=(R/"features/v178/apply-v178-team-gui.py").read_text()
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class TeamGui(unittest.TestCase):
 def test_patch_flow(self):
  ast.parse(S)
  self.assertIn("python3 features/v178/apply-v178-team-gui.py",W)
  self.assertLess(W.index("apply-v178-ftb-map-gui.py"),W.index("apply-v178-team-gui.py"))
  self.assertLess(W.index("apply-v178-team-gui.py"),W.index("apply-v178-mining-map-gui.py"))
 def test_safe_inputs_and_server_snapshot(self):
  for part in ("VALID_PLAYER","VALID_UUID","sendCommand(","event.register(V178TeamSnapshot.TYPE",
               'e.registrar("1").playToClient(TYPE,CODEC)',"summary.toString()",
               "Math.min(16,members.length)","b->namedAction", "b->send(\"list\")",
               "new V178ClaimTeamScreen(this)"):
   self.assertIn(part,S)
  self.assertNotIn("loadChunk(",S)
  self.assertNotIn("forceChunk(",S)
 def test_compiled_sources(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:return
  j=Path(root)/"dev/obsidiannetwork"
  for f in ("claims/V178TeamSnapshot.java","client/V178ClaimTeamScreen.java"):
   self.assertTrue((j/f).exists(),f)
  self.assertIn("V178TeamSnapshot(",(j/"claims/V178Claims.java").read_text())
  self.assertIn("new V178ClaimTeamScreen(this)",(j/"client/V178ClaimsMapScreen.java").read_text())
if __name__=="__main__":unittest.main()
