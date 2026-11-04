"""B1085 turret renders aiming between shots and keeps original firing gates."""
import ast
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"features/v176/apply-v176-b1085-turret-live-aim.py"
class B1085TurretLiveAim(unittest.TestCase):
 def test_syntax(self): ast.parse(P.read_text("utf-8"))
 def test_server_aim_and_firing_gates(self):
  s=P.read_text("utf-8")
  for token in ("B1085_TURRET_TARGET_TRACKS_DURING_COOLDOWN",
      "suit.setYRot(xsxYaw);","suit.setYBodyRot(xsxYaw);",
      "suit.setYHeadRot(xsxYaw);","suit.setRightArmPose(",
      "ClipContext.Block.COLLIDER","V176MicroMgRules.canTurretFire(",
      "V176MicroMgRules.canSpawn(", "V176MicroMgRules.FE_PER_SHOT",
      "if(player.getDeltaMovement().lengthSqr()>0.0025D"):
   self.assertIn(token,s)
 def test_pipeline_order_and_buildlock(self):
  w=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
  self.assertLess(w.index("python3 features/v176/apply-v176-b1075-arm-turret-long-range.py"),
                  w.index("python3 features/v176/apply-v176-b1085-turret-live-aim.py"))
  self.assertIn("contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')",w)
if __name__=="__main__":unittest.main()
