#!/usr/bin/env python3
"""v1.7.7: optimize the expensive always-visible held Multitool model.

B1188 reconstructs 2318 native 3D cuboids from the 132-piece original
Blockbench model. Retain the original texture, all 132 source meshes and all
item transforms, while re-rasterizing at 2 instead of 8 cells per pixel.
The exact same model meshing logic then produces 518 native 3D elements:
~78% fewer independent cuboids, with no game logic or server changes.

Runs AFTER B1224 so existing handheld and GUI transforms are preserved.
"""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"v176/apply-v176-b1188-native-3d-multitool.py"
RESOURCE_ROOT=Path(os.environ["V1_RESOURCE_ROOT"])
ASSETS=RESOURCE_ROOT/"assets/obsidiannetwork"
model_file=ASSETS/"models/item/multitool.json"
client_item=ASSETS/"items/multitool.json"
texture=ASSETS/"textures/item/void_reaver_hd.png"

original=json.loads(model_file.read_text(encoding="utf-8"))
assert original.get("parent")=="minecraft:block/block"
assert original.get("textures",{}).get("palette")=="obsidiannetwork:item/void_reaver_hd"
assert len(original["elements"])==2318,("V177_MULTITOOL_EXPECT_B1188_BASE",len(original["elements"]))
assert original["display"]["firstperson_righthand"]["rotation"][1]==-90
sha_before=hashlib.sha256(texture.read_bytes()).hexdigest()
item_before=client_item.read_bytes()

# Re-run precisely the tested B1188 original-mesh rasterizer, only with
# fourfold coarser X/Y subdivision. Avoid separate or custom render layers.
script=SCRIPT.read_text(encoding="utf-8")
for old,new in (
  ("S=8\n","S=2\n"),
  ("XMAX=180\n","XMAX=45\n"),
  ("YMAX=260\n","YMAX=65\n"),
  ("assert len(elements)>=2000 and len(colors)>=20",
   "assert 400<=len(elements)<=700 and len(colors)>=20"),
):
 assert script.count(old)==1,("V177_MULTITOOL_BUILDER_DRIFT",old,script.count(old))
 script=script.replace(old,new,1)

with tempfile.TemporaryDirectory(prefix="xsxlabs-v177-multitool-lod-") as tmp:
  base=Path(tmp)/"assets/obsidiannetwork"
  for folder in ("models/item","items","textures/item"):
   (base/folder).mkdir(parents=True,exist_ok=True)
  # B1188's explicit legacy OBJ input gate is supplied only in TEMPORARY files.
  legacy={
   "loader":"neoforge:obj",
   "model":"obsidiannetwork:models/item/void_reaver_hd.obj",
   "display":original["display"],
  }
  (base/"models/item/multitool.json").write_text(
      json.dumps(legacy),encoding="utf-8")
  (base/"items/multitool.json").write_bytes(item_before)
  shutil.copyfile(texture,base/"textures/item/void_reaver_hd.png")
  previous=os.environ["V1_RESOURCE_ROOT"]
  try:
   os.environ["V1_RESOURCE_ROOT"]=tmp
   exec(compile(script,str(SCRIPT),"exec"),{
      "__file__":str(SCRIPT),"__name__":"__main__"})
  finally:
   os.environ["V1_RESOURCE_ROOT"]=previous
  optimized=json.loads((base/"models/item/multitool.json").read_text(encoding="utf-8"))
  assert (base/"textures/item/void_reaver_hd.png").read_bytes()==texture.read_bytes()

assert len(optimized["elements"])==518,(
    "V177_MULTITOOL_OPTIMIZED_MESH_DRIFT",len(optimized["elements"]))
assert optimized["textures"]==original["textures"]
assert optimized["display"]==original["display"]
assert all(len(e["faces"])==6 for e in optimized["elements"])
assert all(all(e["to"][axis]>e["from"][axis] for axis in range(3))
           for e in optimized["elements"])
# Change only the native cuboid geometry, not original art, item ID, animations,
# GUI scale, mining/enchantment properties, first/third-person transforms.
original["elements"]=optimized["elements"]
model_file.write_text(json.dumps(original,separators=(",",":"),ensure_ascii=False)+"\n",
                      encoding="utf-8")
assert hashlib.sha256(texture.read_bytes()).hexdigest()==sha_before
assert client_item.read_bytes()==item_before
print("V177_MULTITOOL_RENDER_FPS_LOD_PASS: 2318 -> 518 native 3D elements; "+
      "all 132 Blockbench meshes, original PNG and all hand transforms retained")
