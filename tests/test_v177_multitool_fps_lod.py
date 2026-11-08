#!/usr/bin/env python3
"""Regression: reduce Multitool held-item baked geometry while keeping 3D art."""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"features/v176/apply-v176-b1188-native-3d-multitool.py"
OPTIMIZER=ROOT/"features/v177/apply-v177-multitool-render-lod.py"
PARTS=ROOT/"features/v176/b1181-assets"
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class MultitoolFpsLod(unittest.TestCase):
 def test_regenerate_real_132_source_meshes_and_preserve_original_texture(self):
  bb=json.loads("\n".join(p.read_text(encoding="utf-8")
    for p in sorted(PARTS.glob("void_model.part*"))))
  self.assertEqual(len(bb["elements"]),132)
  png=base64.b64decode(bb["textures"][0]["source"].split("base64,",1)[1])
  with tempfile.TemporaryDirectory() as temp:
   assets=Path(temp)/"assets/obsidiannetwork"
   for folder in ("models/item","items","textures/item"):
    (assets/folder).mkdir(parents=True,exist_ok=True)
   (assets/"textures/item/void_reaver_hd.png").write_bytes(png)
   (assets/"items/multitool.json").write_text(json.dumps({
    "model":{"type":"minecraft:model","model":"obsidiannetwork:item/multitool"}}))
   display={
    "firstperson_righthand":{
      "rotation":[0,-90,10],"translation":[1,1.9,0],
      "scale":[.7,.7,.7]},
    "firstperson_lefthand":{
      "rotation":[0,90,-10],"translation":[-1,1.9,0],
      "scale":[.7,.7,.7]},
    "thirdperson_righthand":{
      "rotation":[0,-90,55],"translation":[0,2,0],
      "scale":[.7,.7,.7]},
   }
   model=assets/"models/item/multitool.json"
   model.write_text(json.dumps({
    "loader":"neoforge:obj",
    "model":"obsidiannetwork:models/item/void_reaver_hd.obj",
    "display":display,
   }))
   env={**os.environ,"V1_RESOURCE_ROOT":temp}
   subprocess.run([sys.executable,str(ORIGINAL)],env=env,check=True,
      capture_output=True,text=True)
   before=json.loads(model.read_text())
   self.assertEqual(len(before["elements"]),2318)
   before_hash=hashlib.sha256(png).digest()
   before_item=(assets/"items/multitool.json").read_bytes()
   subprocess.run([sys.executable,str(OPTIMIZER)],env=env,check=True,
      capture_output=True,text=True)
   after=json.loads(model.read_text())
   self.assertEqual(len(after["elements"]),518)
   self.assertEqual(before["display"],after["display"])
   self.assertEqual(before["textures"],after["textures"])
   self.assertEqual(before["parent"],after["parent"])
   self.assertEqual(before["ambientocclusion"],after["ambientocclusion"])
   self.assertNotIn("loader",after)
   self.assertEqual(hashlib.sha256(
      (assets/"textures/item/void_reaver_hd.png").read_bytes()).digest(),
      before_hash)
   self.assertEqual((assets/"items/multitool.json").read_bytes(),before_item)
   self.assertTrue(all(all(b>a for a,b in zip(e["from"],e["to"]))
     and len(e["faces"])==6 for e in after["elements"]))
   self.assertLess(len(after["elements"])/len(before["elements"]),0.25)
 def test_pipeline_scoped_to_v177_after_legacy_model_position(self):
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)
  self.assertLess(FLOW.index("python3 features/v176/apply-v176-b1224-held-tools.py"),
                  FLOW.index("python3 features/v177/apply-v177-multitool-render-lod.py"))
  self.assertIn("test_v177_multitool_fps_lod.py",FLOW)

if __name__=="__main__":
 unittest.main()
