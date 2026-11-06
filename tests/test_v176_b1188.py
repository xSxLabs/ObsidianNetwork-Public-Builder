"""B1188 actual native 3D multi-tool model regression: all 132 real source parts."""
import base64,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
from io import BytesIO
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'features/v176/apply-v176-b1188-native-3d-multitool.py'
PARTS=ROOT/'features/v176/b1181-assets'
W=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text(encoding='utf-8')
class B1188(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bb=json.loads('\n'.join(x.read_text() for x in sorted(PARTS.glob('void_model.part*'))))
  cls.png=base64.b64decode(cls.bb['textures'][0]['source'].split('base64,',1)[1])
  cls.tmp=tempfile.TemporaryDirectory()
  base=Path(cls.tmp.name)/'assets/obsidiannetwork'
  cls.res=base
  (base/'models/item').mkdir(parents=True)
  (base/'items').mkdir(parents=True)
  (base/'textures/item').mkdir(parents=True)
  old={'loader':'neoforge:obj','model':'obsidiannetwork:models/item/void_reaver_hd.obj',
       'display':{'firstperson_righthand':{'rotation':[0,-90,10]},'thirdperson_righthand':{'rotation':[0,-90,55]}}}
  (base/'models/item/multitool.json').write_text(json.dumps(old))
  (base/'items/multitool.json').write_text('{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/multitool"}}')
  (base/'textures/item/void_reaver_hd.png').write_bytes(cls.png)
  env=dict(os.environ,V1_RESOURCE_ROOT=cls.tmp.name)
  subprocess.run([sys.executable,str(SRC)],env=env,check=True,capture_output=True,text=True)
  cls.model=json.loads((base/'models/item/multitool.json').read_text())
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_native_vanilla_baker_not_invisible_obj(self):
  self.assertNotIn('loader',self.model)
  self.assertEqual(self.model['parent'],'minecraft:block/block')
  self.assertEqual(self.model['textures']['palette'],'obsidiannetwork:item/void_reaver_hd')
  self.assertEqual(len(self.model['elements']),2318)
  self.assertEqual(self.model['display']['firstperson_righthand']['rotation'][1],-90)
 def test_original_texture_hash(self):
  actual=(self.res/'textures/item/void_reaver_hd.png').read_bytes()
  self.assertEqual(hashlib.sha256(actual).digest(),hashlib.sha256(self.png).digest())
  self.assertEqual(Image.open(BytesIO(actual)).size,(128,128))
 def test_every_native_element_is_visible_3d_and_opaque(self):
  img=Image.open(BytesIO(self.png)).convert('RGBA')
  colors=set()
  for elem in self.model['elements']:
   a,b=elem['from'],elem['to']
   self.assertTrue(all(b[i]>a[i] for i in range(3)),('B1188_NOT_3D',elem))
   self.assertEqual(set(elem['faces']),{'up','down','north','south','west','east'})
   for face in elem['faces'].values():
    self.assertEqual(face['texture'],'#palette')
    u,v,u2,v2=face['uv']
    self.assertGreater(u2-u,0);self.assertGreater(v2-v,0)
    x=round((u+u2)*4);y=round((v+v2)*4)
    self.assertEqual(img.getpixel((x,y))[3],255)
    colors.add((x,y))
  self.assertGreaterEqual(len(colors),20)
 def test_all_132_original_meshes_present_not_flat(self):
  self.assertEqual(len(self.bb['elements']),132)
  self.assertEqual(len({x['name'] for x in self.bb['elements']}),132)
  self.assertGreaterEqual(max(e['to'][2] for e in self.model['elements'])-min(e['from'][2] for e in self.model['elements']),3)
 def test_ci_order(self):
  self.assertLess(W.index('apply-v176-b1187-worn-arm.py'),W.index('apply-v176-b1188-native-3d-multitool.py'))
  self.assertIn("test_v176_b1188.py",W)
if __name__=='__main__':unittest.main()
