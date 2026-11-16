#!/usr/bin/env python3
"""v1.7.8 owner-managed claim-team regression/generation contracts."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v178/apply-v178-teams.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class ClaimTeams(unittest.TestCase):
 def test_integrated_and_python_compiles(self):
  ast.parse(PATCH)
  self.assertIn("python3 features/v178/apply-v178-teams.py",WORKFLOW)
  self.assertLess(WORKFLOW.index("apply-v178-claims.py"),WORKFLOW.index("apply-v178-teams.py"))
  self.assertLess(WORKFLOW.index("apply-v178-ftb-batch.py"),WORKFLOW.index("apply-v178-teams.py"))
  self.assertLess(WORKFLOW.index("apply-v178-teams.py"),WORKFLOW.index("apply-v178-ftb-map-gui.py"))
 def test_permissions_and_owner_quota_preserved(self):
  for token in ("TEAM_MEMBERS.getOrDefault(owner,Set.of()).contains(player)",
                "MEMBER_TEAM.containsKey(member)","MAX_TEAM_SIZE=16",
                "TEAM_INVITES.put(member","teamUnlink(UUID owner,UUID member)",
                'data.append("M\\t")',"TEAM_MEMBERS.clear();MEMBER_TEAM.clear();TEAM_INVITES.clear();"):
   self.assertIn(token,PATCH)
  self.assertNotIn("TICKETS.forceChunk(",PATCH)
  self.assertNotIn("CLAIMS.put(",PATCH)
 def test_generated_backend(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:return
  source=(Path(root)/"dev/obsidiannetwork/claims/V178Claims.java").read_text()
  for token in ("V178_CLAIM_TEAMS", "TEAM_INVITES", "teamInvite(ServerPlayer",
                "teamAccept(ServerPlayer", "teamLeave(ServerPlayer",
                "teamKick(ServerPlayer", 'Commands.literal("team")',
                'data.append("M\\t")', "TEAM_MEMBERS.getOrDefault(owner,Set.of()).contains(player)"):
   if token=="V178_CLAIM_TEAMS":continue
   self.assertIn(token,source)
  self.assertIn("MAX_CLAIMS",source)
  self.assertIn("MAX_LOADED",source)
  self.assertIn("TICKETS.forceChunk(level",source)
if __name__=="__main__":unittest.main()
