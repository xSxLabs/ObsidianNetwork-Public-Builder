import ast,base64,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FEATURES=ROOT/"features/v176"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
class HammerRegression(unittest.TestCase):
 def test_generator_syntax_and_pipeline(self):
  for name in ("apply-v176-hammer.py","apply-v176-hammer-model.py"):
   ast.parse((FEATURES/name).read_text())
   self.assertIn("python3 features/v176/"+name,WORKFLOW.read_text())
  self.assertLess(WORKFLOW.read_text().index("apply-v176-multitool.py"),WORKFLOW.read_text().index("apply-v176-hammer.py"))
 def test_reference_texture_is_pixel_exact(self):
  raw=base64.b64decode((FEATURES/"hammer-texture.png.base64").read_text().strip(),validate=True)
  self.assertEqual(hashlib.sha256(raw).hexdigest(),"b7f7e41af05fee0eeaf094f7d159c16a1388a734452c850f59dc1dc2aed93326")
  self.assertEqual(raw[:8],bytes((137,80,78,71,13,10,26,10)))
  self.assertEqual((int.from_bytes(raw[16:20],"big"),int.from_bytes(raw[20:24],"big")),(512,512))
 def test_generated_native_model(self):
  geometry=json.loads((FEATURES/"hammer-geometry.json").read_text())
  self.assertEqual(len(geometry["elements"]),126)
  with tempfile.TemporaryDirectory() as tmp:
   env={**os.environ,"V1_RESOURCE_ROOT":tmp}
   subprocess.run([sys.executable,str(FEATURES/"apply-v176-hammer-model.py")],env=env,check=True,capture_output=True)
   assets=Path(tmp)/"assets/obsidiannetwork"
   model=json.loads((assets/"models/item/hammer.json").read_text())
   self.assertEqual(len(model["elements"]),126)
   self.assertEqual(model["display"],geometry["display"])
   self.assertEqual((assets/"textures/item/hammer.png").read_bytes(),base64.b64decode((FEATURES/"hammer-texture.png.base64").read_text().strip()))
   self.assertEqual(json.loads((assets/"items/hammer.json").read_text())["model"]["model"],"obsidiannetwork:item/hammer")
 def test_separate_item_and_recipe(self):
  s=(FEATURES/"apply-v176-hammer.py").read_text()
  for value in ('"hammer"','hammer/HammerItem.java','netherite_pickaxe','netherite_ingot','"PPP"','" N "','"mineBlock"'.strip('"')):
   self.assertIn(value,s)
  self.assertNotIn('p.write_text(r\'\'\'package dev.obsidiannetwork.multitool',s)
if __name__=="__main__":unittest.main()
