#!/usr/bin/env python3
"""Generate the 126-cuboid native Hammer model, reconstructed from reference coordinates."""
import os,json,zlib,base64
from pathlib import Path
from PIL import Image,ImageDraw
data=json.loads(zlib.decompress(base64.b64decode("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")))
assert len(data["elements"])==126
assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
model=assets/"models/item/hammer.json";model.parent.mkdir(parents=True,exist_ok=True)
elements=[]
for e in data["elements"]:
 faces={k:{"uv":[round(q/32,5) for q in uv],"texture":"#0"} for k,uv in e["faces"].items()}
 elements.append({"from":[round(v+8 if i==1 else v+8,4) for i,v in enumerate(e["from"])],"to":[round(v+8,4) for v in e["to"]],"faces":faces})
# Shift geometry into item model space without altering its relative proportions.
model.write_text(json.dumps({"texture_size":[512,512],"textures":{"0":"obsidiannetwork:item/hammer"},"elements":elements,"display":data["display"]},separators=(",",":"))+"\n")
tex=assets/"textures/item/hammer.png";tex.parent.mkdir(parents=True,exist_ok=True)
im=Image.new("RGBA",(512,512),(38,35,50,255))
d=ImageDraw.Draw(im)
for i in range(0,512,16):
 for j in range(0,512,16):
  c=(57,54,73,255) if (i//16+j//16)%2 else (75,70,90,255)
  d.rectangle((i,j,i+15,j+15),fill=c)
for k in range(0,512,64):
 d.line((k,0,k,511),fill=(160,53,230,255),width=5)
 d.line((0,k,511,k),fill=(122,48,180,255),width=4)
im.save(tex)
print("HAMMER_NATIVE_MODEL_126_CUBES_GENERATED")
