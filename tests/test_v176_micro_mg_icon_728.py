#!/usr/bin/env python3
"""B728: image-model linkage and texture completeness before long Gradle build."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v176/apply-v176-micro-mg-icon-728.py"
class MicroMgMissingTextureRegression(unittest.TestCase):
 def test_fixes_missing_vanilla_crossbow_layer(self):
  with tempfile.TemporaryDirectory() as tmp:
   assets=Path(tmp)/"assets/obsidiannetwork"
   model=assets/"models/item/power_card_micro_mg.json"
   model.parent.mkdir(parents=True)
   model.write_text(json.dumps({
     "parent":"minecraft:item/generated",
     "textures":{"layer0":"minecraft:item/crossbow"}
   }))
   env={**os.environ,"V1_RESOURCE_ROOT":tmp}
   patch=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertEqual(patch.returncode,0,patch.stdout+patch.stderr)
   data=json.loads(model.read_text())
   self.assertEqual(data["textures"]["layer0"],"obsidiannetwork:item/power_card_micro_mg")
   png=assets/"textures/item/power_card_micro_mg.png"
   self.assertTrue(png.is_file())
   with Image.open(png) as im:
    self.assertEqual(im.size,(32,32))
    self.assertEqual(im.mode,"RGBA")
    self.assertEqual(im.getpixel((0,0))[3],0)
    self.assertGreater(len(im.getcolors(1024) or []),12)
   # Fail closed instead of silently replacing a working asset on reruns.
   second=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertNotEqual(second.returncode,0)
 def test_does_not_accept_incorrect_model(self):
  with tempfile.TemporaryDirectory() as tmp:
   model=Path(tmp)/"assets/obsidiannetwork/models/item/power_card_micro_mg.json"
   model.parent.mkdir(parents=True)
   model.write_text('{"parent":"minecraft:item/generated","textures":{"layer0":"other:broken"}}')
   r=subprocess.run([sys.executable,str(SCRIPT)],env={**os.environ,"V1_RESOURCE_ROOT":tmp},capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertFalse((model.parent.parent.parent/"textures/item/power_card_micro_mg.png").exists())
if __name__=="__main__":unittest.main()
