import ast,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"features/v176/apply-v176-multitool.py"
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class MultitoolRegression(unittest.TestCase):
 def test_syntax(self):ast.parse(P.read_text())
 def test_behavior(self):
  s=P.read_text()
  for token in ('p.durability(6093)','netherite_shovel','netherite_pickaxe','netherite_axe','netherite_ingot','isShiftKeyDown()','ORE_LIMIT=64','LOG_LIMIT=192','LEAF_LIMIT=256','hasLeaves(server,pos)','clearLeaves(server,pos)','minecraft:crafting_shaped','getDestroySpeed','isCorrectToolForDrops','DIRT_PATH'): 
   self.assertIn(token,s,token)
 def test_pipeline_and_entry_freeze(self):
  self.assertIn("python3 features/v176/apply-v176-multitool.py",W)
  self.assertLess(W.index("apply-v176-b1149-gravity-modes.py"),W.index("python3 features/v176/apply-v176-multitool.py"))
  self.assertIn("python3 features/v176/apply-v176-b1146-freeze-walkin.py",W)
if __name__=="__main__":unittest.main()
