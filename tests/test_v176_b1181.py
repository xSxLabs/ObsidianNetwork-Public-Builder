"""B1181 verify exact uploaded mesh and scope before full compile."""
import ast,base64,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IMPORT=ROOT/'features/v176/apply-v176-b1181-user-bbmodel.py'
ARM=ROOT/'features/v176/apply-v176-b1181-arm-fixes.py'
W=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text()
class B1181(unittest.TestCase):
 def test_syntax(self):
  ast.parse(IMPORT.read_text());ast.parse(ARM.read_text())
 def test_exact_user_mesh_bytes(self):
  files=sorted((ROOT/'features/v176/b1181-assets').glob('void_model.part*'))
  self.assertEqual(len(files),8)
  j=json.loads('\n'.join(p.read_text() for p in files))
  self.assertEqual(len(j['elements']),132)
  self.assertEqual(sum(len(x['faces']) for x in j['elements']),1760)
  self.assertEqual(len(j['textures']),1)
  png=base64.b64decode(j['textures'][0]['source'].split('base64,')[1])
  self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
 def test_axe_orientation_and_arm_scope(self):
  a=IMPORT.read_text();b=ARM.read_text()
  self.assertIn("display['firstperson_righthand']['rotation']=[0,-90,10]",a)
  self.assertIn("display['thirdperson_righthand']['rotation']=[0,-90,55]",a)
  self.assertIn("'loader':'neoforge:obj'",a)
  self.assertIn("if(worn)pose.translate(0.0F,-0.012F,0.18F)",b)
  self.assertIn("parent.translateAndRotate(pose)",b)
  self.assertIn("assert 'pose.translate(0.0F,0.30F,0.0F)' not in w",b)
  self.assertIn("XSX_POWER_LOWER",b)
  self.assertNotIn("V176MicroMgStandLayer.java",b)
  self.assertNotIn("PowerArmorSuitWorld.java",b)
 def test_pipeline(self):
  self.assertLess(W.index('apply-v176-b1178-multitool-arm.py'),W.index('apply-v176-b1181-user-bbmodel.py'))
  self.assertLess(W.index('apply-v176-b1181-user-bbmodel.py'),W.index('apply-v176-b1181-arm-fixes.py'))
  self.assertIn("test_v176_b1181.py",W)
if __name__=='__main__':unittest.main()
