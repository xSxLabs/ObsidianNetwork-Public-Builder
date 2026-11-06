"""B1187 validates actual exported model + MTL + Minecraft item routing."""
import base64,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'features/v176/apply-v176-b1181-user-bbmodel.py'
FIX=ROOT/'features/v176/apply-v176-b1187-obj-material.py'
ARM=ROOT/'features/v176/apply-v176-b1187-worn-arm.py'
PARTS=ROOT/'features/v176/b1181-assets'
WORKFLOW=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text(encoding='utf-8')
class B1187(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bb=json.loads('\n'.join(p.read_text() for p in sorted(PARTS.glob('void_model.part*'))))
  cls.png=base64.b64decode(cls.bb['textures'][0]['source'].split('base64,',1)[1])
  cls.temp=tempfile.TemporaryDirectory()
  r=Path(cls.temp.name)/'assets/obsidiannetwork'
  (r/'models/item').mkdir(parents=True)
  (r/'models/item/multitool.json').write_text('{}\n')
  (r/'items').mkdir(parents=True)
  (r/'items/multitool.json').write_text('{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/multitool"}}')
  env=dict(os.environ,V1_RESOURCE_ROOT=cls.temp.name)
  subprocess.run([sys.executable,str(BASE)],env=env,check=True,capture_output=True)
  subprocess.run([sys.executable,str(FIX)],env=env,check=True,capture_output=True)
  cls.res=r
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_png_is_exact_user_binary(self):
  actual=(self.res/'textures/item/void_reaver_hd.png').read_bytes()
  self.assertEqual(hashlib.sha256(actual).digest(),hashlib.sha256(self.png).digest())
 def test_per_group_material_and_triangles(self):
  obj=(self.res/'models/item/void_reaver_hd.obj').read_text().splitlines()
  self.assertEqual(sum(x.startswith('f ') for x in obj),5048)
  self.assertEqual(sum(x.startswith('g mesh_') for x in obj),132)
  self.assertEqual(sum(x.startswith('usemtl void_reaver_material') for x in obj),133)
  self.assertEqual(sum(x.startswith('v ') for x in obj),6044)
  self.assertEqual(sum(x.startswith('vn ') for x in obj),3520)
  self.assertTrue(all(len(x.split())==4 for x in obj if x.startswith('f ')))
  for i,line in enumerate(obj):
   if line.startswith('g mesh_'): self.assertEqual(obj[i+1],'usemtl void_reaver_material')
 def test_neoforge_loader_link(self):
  mdl=json.loads((self.res/'models/item/multitool.json').read_text())
  client=json.loads((self.res/'items/multitool.json').read_text())
  self.assertEqual(client['model']['model'],'obsidiannetwork:item/multitool')
  self.assertEqual(mdl['loader'],'neoforge:obj')
  self.assertEqual(mdl['mtl_override'],'obsidiannetwork:models/item/void_reaver_hd.mtl')
  self.assertEqual(mdl['textures']['texture0'],'obsidiannetwork:item/void_reaver_hd')
  self.assertEqual(mdl['display']['firstperson_righthand']['rotation'][1],-90)
 def test_arm_height_is_only_worn(self):
  s=ARM.read_text()
  self.assertIn('if(worn)pose.translate(0.0F,-0.012F,0.15F)',s)
  self.assertIn('if(worn)pose.translate(0.0F,-0.012F,0.13F)',s)
  self.assertIn('drawArm(pose,nodes,light,parent,tier,extension,false);',s)
 def test_workflow_order(self):
  self.assertLess(WORKFLOW.index('apply-v176-b1185-worn-height.py'),
                  WORKFLOW.index('apply-v176-b1187-obj-material.py'))
  self.assertLess(WORKFLOW.index('apply-v176-b1187-obj-material.py'),
                  WORKFLOW.index('apply-v176-b1187-worn-arm.py'))
  self.assertIn('test_v176_b1187.py',WORKFLOW)
if __name__=='__main__':unittest.main()
