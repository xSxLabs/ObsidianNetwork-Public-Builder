#!/usr/bin/env python3
"""Build the native Minecraft 26.1.2 Hammer item model from exact reference measurements.
No Blockbench runtime dependency; no changes to Multitool or Powerarmor.
"""
import os,json,base64,hashlib
from pathlib import Path

source=Path(__file__).resolve().parent
assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
data=json.loads((source/"hammer-geometry.json").read_text())
assert len(data["elements"])==126, "Hammer must retain all 126 reference cubes"
texture_bytes=base64.b64decode((source/"hammer-texture.png.base64").read_text().strip(),validate=True)
assert texture_bytes[:8]==bytes((137,80,78,71,13,10,26,10))
assert int.from_bytes(texture_bytes[16:20],"big")==512
assert int.from_bytes(texture_bytes[20:24],"big")==512
tex=assets/"textures/item/hammer.png"
tex.parent.mkdir(parents=True,exist_ok=True)
tex.write_bytes(texture_bytes)

# Blockbench UVs are 512-pixel atlas coordinates; Java item-model UVs use 0..16.
# Thus divide every atlas coordinate by 32. No geometry translation or rescaling.
elements=[]
for e in data["elements"]:
 faces={direction:{"uv":[round(x/32,6) for x in uv],"texture":"#0"} for direction,uv in e["faces"].items()}
 elements.append({"from":e["from"],"to":e["to"],"faces":faces})
model=assets/"models/item/hammer.json"
model.parent.mkdir(parents=True,exist_ok=True)
model.write_text(json.dumps({"textures":{"0":"obsidiannetwork:item/hammer"},"elements":elements,"display":data["display"]},ensure_ascii=False,separators=(",",":"))+chr(10))
definition=assets/"items/hammer.json"
definition.parent.mkdir(parents=True,exist_ok=True)
definition.write_text(json.dumps({"model":{"type":"minecraft:model","model":"obsidiannetwork:item/hammer"}},indent=2)+chr(10))
assert len(elements)==126
print("HAMMER_EXACT_TEXTURE_AND_126_PART_MODEL_PASS",hashlib.sha256(texture_bytes).hexdigest())
