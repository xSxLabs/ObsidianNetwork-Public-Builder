#!/usr/bin/env python3
"""Build117: front-only and player-facing armor-stand exit placement regression."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-exit-facing-117.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class ExitFacing117(unittest.TestCase):
 def test_valid_patch(self):ast.parse(PATCH)
 def test_front_block_and_facing_all_four_directions(self):
  for fragment in (
   "BUILD117_EXIT_FRONT_FACING",
   "BlockPos p=player.blockPosition().relative(player.getDirection());",
   "suitVolumeClearable(level,p)",
   "new AABB(p).inflate(0.25D)",
   "player.getDirection().getOpposite().toYRot()",
   "stand.setYRot(faceOwner);",
   "stand.setYBodyRot(faceOwner);",
   "stand.setYHeadRot(faceOwner);",
   "ArmorStand stand=spawn(player,worn);",
   "if(!clearSuitVolume(level,pos))return null;",
   "for direction,(dx,dz) in dirs.items():",
   '"N":(0,-1),"S":(0,1),"E":(1,0),"W":(-1,0)',
  ):self.assertIn(fragment,PATCH,fragment)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorShieldClient.java",PATCH)
 def test_workflow_after_slow_breathing_shield(self):
  self.assertLess(WF.index("apply-power-armor-pose-locked-shield-115.py"),
                  WF.index("apply-power-armor-exit-facing-117.py"))
  self.assertIn("BUILD117_EXIT_FRONT_FACING PASS",WF)
if __name__=="__main__":unittest.main()
