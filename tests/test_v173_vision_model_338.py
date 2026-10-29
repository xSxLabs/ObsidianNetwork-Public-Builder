import ast,pathlib,unittest
P=pathlib.Path(__file__).resolve().parents[1]/"features/v173/apply-vision-model-338.py"
class VisionRealModel338(unittest.TestCase):
 def test_syntax(self):ast.parse(P.read_text())
 def test_no_world_mutation(self):
  s=P.read_text()
  for marker in ("V173_B338_CABLE_MODEL_REVEAL","BooleanProperty bool",
                 "this.blockResolver.update(state.facadeModel, state.facade",
                 "if(s.facaded)","facadeModel.submit"):
   self.assertIn(marker,s)
  self.assertNotIn("level.setBlock(",s)
  self.assertNotIn("sendBlockUpdated(",s)
if __name__=="__main__":unittest.main()
