"""B1185: prove that the original Blockbench texture remains byte-identical
while the compiled item OBJ has nondegenerate UVs and two-sided geometry.
Test the *generated* model, not merely strings in the overlay.
"""
import base64,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
from io import BytesIO

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'features/v176/apply-v176-b1181-user-bbmodel.py'
HEIGHT=ROOT/'features/v176/apply-v176-b1185-worn-height.py'
PARTS=ROOT/'features/v176/b1181-assets'
W=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text(encoding='utf-8')
class B1185(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bb=json.loads('\n'.join(p.read_text() for p in sorted(PARTS.glob('void_model.part*'))))
  cls.png=base64.b64decode(cls.bb['textures'][0]['source'].split('base64,',1)[1])
  cls.tmp=tempfile.TemporaryDirectory()
  r=Path(cls.tmp.name)/'assets/obsidiannetwork'
  (r/'models/item').mkdir(parents=True)
  (r/'models/item/multitool.json').write_text('{}\n')
  env=dict(os.environ,V1_RESOURCE_ROOT=cls.tmp.name)
  subprocess.run([sys.executable,str(SRC)],env=env,check=True,capture_output=True,text=True)
  cls.res=r
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_original_texture_bytes_identical(self):
  generated=(self.res/'textures/item/void_reaver_hd.png').read_bytes()
  self.assertEqual(hashlib.sha256(generated).digest(),hashlib.sha256(self.png).digest())
  self.assertEqual(Image.open(BytesIO(generated)).size,(128,128))
 def test_geometry_and_model_loader(self):
  obj=(self.res/'models/item/void_reaver_hd.obj').read_text()
  original_vertex_count=sum(len(e['vertices']) for e in self.bb['elements'])
  self.assertEqual(sum(line.startswith('v ') for line in obj.splitlines()),original_vertex_count)
  self.assertEqual(original_vertex_count,6044)
  self.assertEqual(sum(line.startswith('f ') for line in obj.splitlines()),3520)
  self.assertEqual(sum(line.startswith('vn ') for line in obj.splitlines()),3520)
  self.assertIn('mtllib void_reaver_hd.mtl',obj)
  self.assertIn('map_Kd #texture0',(self.res/'models/item/void_reaver_hd.mtl').read_text())
  mdl=json.loads((self.res/'models/item/multitool.json').read_text())
  self.assertEqual(mdl['loader'],'neoforge:obj')
  self.assertEqual(mdl['textures']['texture0'],'obsidiannetwork:item/void_reaver_hd')
  self.assertEqual(mdl['display']['firstperson_righthand']['rotation'][1],-90)
 def test_every_face_nonzero_uv_area_and_opaque(self):
  obj=(self.res/'models/item/void_reaver_hd.obj').read_text()
  uv=[None]+[tuple(map(float,line.split()[1:])) for line in obj.splitlines() if line.startswith('vt ')]
  img=Image.open(BytesIO(self.png)).convert('RGBA')
  checked=0
  for line in obj.splitlines():
   if not line.startswith('f '):continue
   refs=[x.split('/') for x in line.split()[1:]]
   self.assertIn(len(refs),(3,4))
   pts=[uv[int(x[1])] for x in refs]
   a,b,c=pts[:3]
   area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
   self.assertGreater(abs(area),0.00001,'B1185_TRANSPARENT_ZERO_AREA_OBJ_FACE')
   for u,v in pts:
    x=round(u*128-.5);y=round((1-v)*128-.5)
    self.assertEqual(img.getpixel((x,y))[3],255,'B1185_UV_SAMPLED_TRANSPARENT_PIXEL')
   checked+=1
  self.assertEqual(checked,3520)
 def test_independent_worn_mount_and_ci_order(self):
  h=HEIGHT.read_text()
  self.assertIn('if(worn)pose.translate(0.0F,-0.012F,0.18F);',h)
  self.assertIn('if(worn)pose.translate(0.0F,-0.012F,0.15F);',h)
  self.assertIn('drawArm(pose,nodes,light,parent,tier,extension,false);',h)
  self.assertLess(W.index('apply-v176-b1181-arm-fixes.py'),
                  W.index('apply-v176-b1185-worn-height.py'))
  self.assertIn('test_v176_b1185.py',W)
if __name__=='__main__':unittest.main()
