#!/usr/bin/env python3
"""B1651 fluid inside-claim compatibility and cross-claim protection contracts."""
import os,ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=(ROOT/"features/v178/apply-v178-fluid-boundary.py").read_text()
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class ClaimFluidBoundary(unittest.TestCase):
 def test_order(self):
  ast.parse(P)
  self.assertIn("python3 features/v178/apply-v178-fluid-boundary.py",W)
  self.assertLess(W.index("apply-v178-server-config.py"),W.index("apply-v178-fluid-boundary.py"))
  self.assertLess(W.index("apply-v178-fluid-boundary.py"),W.index("apply-v178-ftb-map-gui.py"))
 def test_owner_internal_compat(self):
  for token in ("event.getLiquidPos()","Claim target=","Claim source=",
                "if(source==null||!source.owner().equals(target.owner()))",
                "if(target==null)return;","if(claims.isEmpty())return;"):
   self.assertIn(token,P)
  self.assertNotIn("level.getChunk(",P)
  self.assertNotIn("forceChunk(",P)
 def test_generated(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:return
  s=(Path(root)/"dev/obsidiannetwork/claims/V178Claims.java").read_text()
  self.assertIn("B1651_FLUID_BOUNDARY_GUARD",s)
  self.assertIn("event.getLiquidPos()",s)
  self.assertIn("if(source==null||!source.owner().equals(target.owner()))",s)
if __name__=="__main__":unittest.main()
