"""B1178 first-person duplicate and reference model safety contracts."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=(ROOT/"features/v176/apply-v176-b1178-multitool-arm.py").read_text(encoding="utf-8")
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class B1178(unittest.TestCase):
 def test_python_syntax(self):ast.parse(P)
 def test_first_person_only_cancels_old_right_arm(self):
  self.assertIn("xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event)",P)
  self.assertIn("event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT",P)
  self.assertIn("!armedForAttack(player)",P)
  self.assertIn("event.setCanceled(true); // B1178_CANCEL_ONLY_REDUNDANT_VANILLA_RIGHT_ARM",P)
  self.assertNotIn("V176MicroMgStandLayer.java",P)
 def test_tool_physical_forged_and_optics(self):
  for key in ("# Heavy AXE blade on LEFT","# Right PICK/CLAW",
       "one bold electric-purple cutting edge","six-sided magenta gem",
       "70<len(parts)<220","firstperson_righthand","thirdperson_righthand"):
   self.assertIn(key,P)
  self.assertIn("scale\\":[.43,.43,.43]",P)
  self.assertNotIn("models/block/",P)
 def test_scope_no_gameplay(self):
  for forbidden in ("NetworkBackpackMenu.java","PowerArmorSuitWorld.java",
     "PowerArmorRuntime.java","V176MicroMgStandLayer.java","micro_mg_fire",
     "recipe/multitool.json"):
   self.assertNotIn(forbidden,P)
 def test_apply_after_b1176(self):
  self.assertLess(W.index("python3 features/v176/apply-v176-b1176-screenshot-fixes.py"),
                  W.index("python3 features/v176/apply-v176-b1178-multitool-arm.py"))
  self.assertIn("python3 -m unittest discover -s tests -p 'test_v176_b1178.py' -v",W)
if __name__=="__main__":unittest.main()
