#!/usr/bin/env python3
"""B1651 bounded world-scoped claim limits, startup-only I/O contract."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"features/v178/apply-v178-server-config.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class Limits(unittest.TestCase):
 def test_integrated(self):
  ast.parse(SOURCE)
  self.assertIn("python3 features/v178/apply-v178-server-config.py",WF)
  self.assertLess(WF.index("apply-v178-teams.py"),WF.index("apply-v178-server-config.py"))
  self.assertLess(WF.index("apply-v178-server-config.py"),WF.index("apply-v178-ftb-map-gui.py"))
 def test_no_tick_io_or_unlimited_quotas(self):
  for marker in ("readLimits(active);","serverconfig","xsxlabs-chunks.properties",
      "Files.isRegularFile(path)","Math.min(2048","Math.min(256",
      "activeMaxLoaded=Math.min(activeMaxLoaded,activeMaxClaims)",
      ">=activeMaxClaims",">=activeMaxLoaded","max_team_members",
      "activeMaxTeamMembers=MAX_TEAM_SIZE","V178_TEAM_LIMIT_DRIFT",
      ">=activeMaxTeamMembers","<activeMaxTeamMembers"):
   self.assertIn(marker,SOURCE)
  self.assertNotIn("event.getServer().getTickCount()",SOURCE)
 def test_generated(self):
  base=os.environ.get("V1_SOURCE_ROOT")
  if not base:return
  s=(Path(base)/"dev/obsidiannetwork/claims/V178Claims.java").read_text()
  self.assertIn("readLimits(active);",s)
  self.assertIn("activeMaxLoaded=Math.min(activeMaxLoaded,activeMaxClaims)",s)
  self.assertIn("max_force_loaded_chunks",s)
  self.assertIn(">=activeMaxClaims",s)
  self.assertIn(">=activeMaxLoaded",s)
  self.assertIn("max_team_members",s)
  self.assertIn(">=activeMaxTeamMembers",s)
  self.assertIn("<activeMaxTeamMembers",s)
if __name__=="__main__":unittest.main()
