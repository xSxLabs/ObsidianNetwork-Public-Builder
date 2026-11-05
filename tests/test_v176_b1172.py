import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=(ROOT/"features/v176/apply-v176-b1172-worn-arm.py").read_text()
B=(ROOT/"features/v176/apply-v176-b1172-tool-and-backpack.py").read_text()
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class B1172Regression(unittest.TestCase):
 def test_syntax(self):
  ast.parse(A);ast.parse(B)
 def test_arm_scope(self):
  for x in ("V176FinalArmBufferMixin.java","V176ThirdPersonArmSnapshot","capture(","drawArm(pose,nodes,light,parent,tier,extension,false)","if(worn)pose.translate(0.0F,-0.015F,-0.09F)","drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F,true)"):
   self.assertIn(x,A)
  self.assertNotIn("V176MicroMgStandLayer.java",A)
  self.assertNotIn("PowerArmorSuitWorld.java",A)
  self.assertNotIn("firstPerson(RenderHandEvent",A)
 def test_tool_and_backpack(self):
  for x in ("textures/item/multitool_3d.png","elements","0<=v<=16","0.78F","V176BackpackScreen.java","gui","firstperson_righthand"):
   self.assertIn(x,B)
  for x in ("netherite_pickaxe","netherite_shovel","netherite_axe"):self.assertNotIn(x,B)
 def test_pipeline(self):
  anchor="python3 features/v176/apply-v176-multitool.py"
  self.assertLess(W.index(anchor),W.index("python3 features/v176/apply-v176-b1172-worn-arm.py"))
  self.assertLess(W.index(anchor),W.index("python3 features/v176/apply-v176-b1172-tool-and-backpack.py"))
  self.assertIn("python3 -m unittest discover -s tests -p 'test_v176_b1172.py' -v",W)
if __name__=="__main__":unittest.main()
