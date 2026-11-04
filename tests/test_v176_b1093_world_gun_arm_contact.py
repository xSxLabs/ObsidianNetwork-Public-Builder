"""B1093 regression: world gun must seat on actual model right arm in 3P/turret."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v176/apply-v176-b1093-world-gun-arm-contact.py").read_text("utf-8")
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
class B1093WorldGunArmContact(unittest.TestCase):
 def test_syntax_and_scope(self):
  ast.parse(SRC)
  self.assertNotIn("V176MicroMgFire.java",SRC)
  self.assertNotIn("V176MicroMgProjectile.java",SRC)
  self.assertNotIn("cellterminal/",SRC)
 def test_shared_arm_contact_and_no_duplicate(self):
  for token in ("B1093_WORLD_GUN_ARM_CONTACT",
      "drawArm(pose,event.getSubmitNodeCollector()",
      "parent.translateAndRotate(pose)",
      "RIGHT_ARM_PIVOT.xRot=(float)Math.toRadians(state.rightArmPose.x());",
      "PartPose.offset(-5.0F,2.0F,0.0F)",
      "nodes.submitModelPart(XSX_WORLD_BARREL,pose",
      "nodes.submitModelPart(BARREL,pose",
      ".addBox(-0.46F,6.8F,-4.15F,0.92F,4.7F,1.05F)"):
   self.assertIn(token,SRC)
  self.assertIn("renderedArm.xRot=-1.535F",SRC) # removed from generated Java using old anchor
  self.assertIn("0.006F",SRC)
 def test_after_aim_and_before_recipe(self):
  self.assertLess(W.index("python3 features/v176/apply-v176-b1085-turret-live-aim.py"),
                  W.index("python3 features/v176/apply-v176-b1093-world-gun-arm-contact.py"))
  self.assertIn("contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')",W)
if __name__=="__main__":unittest.main()
