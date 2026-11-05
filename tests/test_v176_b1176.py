"""B1176 user screenshot: scope/invariants and complete source pipeline."""
import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=(ROOT/"features/v176/apply-v176-b1176-screenshot-fixes.py").read_text()
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class ScreenshotFixes(unittest.TestCase):
 def test_syntax(self):ast.parse(F)
 def test_thirdperson_only(self):
  for key in ("if(worn)pose.translate(0.0F,-0.012F,0.020F)","drawArm(pose,nodes,light,parent,tier,extension,false)"):
   self.assertIn(key,F)
  for prohibited in ("V176MicroMgStandLayer.java","PowerArmorSuitWorld.java","firstPerson(RenderHandEvent"):
   self.assertNotIn(prohibited,F)
 def test_count_single_source(self):
  for key in ("stack.copyWithCount(1)","xsxCountScale","0.58F","xsx_v176_preview_total","old duplicate count loop removed"):
   self.assertIn(key,F)
 def test_reference_model(self):
  for key in ("CRESCENT AXE","Pick on RIGHT","violet","firstperson_righthand","0<=v<=16","len(parts)>=70"):
   self.assertIn(key,F)
  self.assertNotIn("data/obsidiannetwork/recipe",F)
 def test_pipeline(self):
  self.assertIn("python3 features/v176/apply-v176-b1176-screenshot-fixes.py",W)
  self.assertIn("python3 -m unittest discover -s tests -p 'test_v176_b1176.py' -v",W)
  self.assertLess(W.index("python3 features/v176/apply-v176-b1172-tool-and-backpack.py"),
                  W.index("python3 features/v176/apply-v176-b1176-screenshot-fixes.py"))
if __name__=="__main__":unittest.main()
