"""B818 validates stack-bounded item extraction and literal 729 recipe chain."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class B818(unittest.TestCase):
 def test_max_stack_guard(self):
  text=(ROOT/"features/v176/apply-v176-backpack-transfer-safety-818.py").read_text("utf-8")
  self.assertIn("output.getMaxStackSize()",text)
  self.assertIn("output.setCount(count);",text)
  self.assertIn("if(count<=0)return false;",text)
 def test_cost_and_exact_output_verified_after_collision_resolver(self):
  text=(ROOT/"features/v176/verify-v176-cobble-obsidian-818.py").read_text("utf-8")
  self.assertIn('["CCC","CCC","CCC"]',text)
  self.assertIn('"minecraft:obsidian"',text)
  self.assertIn('{"id":result,"count":1}',text)
  flow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
  last=flow.rfind("python3 features/v175/apply-v175-recipe-collisions-659.py work/src/main/resources")
  check=flow.index("python3 features/v176/verify-v176-cobble-obsidian-818.py")
  self.assertLess(last,check)
if __name__=="__main__":
 unittest.main()
