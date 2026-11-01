#!/usr/bin/env python3
"""v1.7.6 B728: replace missing vanilla crossbow texture with a real Micro-MG icon.

Minecraft 26.1 has crossbow_standby rather than textures/item/crossbow.png.
The invalid generated-model layer produced the purple/black missing-texture
checkerboard visible in the inventory. This builds a unique 32x32 opaque/alpha
power-armor upgrade icon, leaving all recipe IDs and armor visuals unchanged.
Run after apply-v176-micro-mg-module.py.
"""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
model=A/"models/item/power_card_micro_mg.json"
output=A/"textures/item/power_card_micro_mg.png"

assert model.is_file(),("V176_B728_MICRO_MG_MODEL_MISSING",str(model))
info=json.loads(model.read_text(encoding="utf-8"))
assert info["parent"]=="minecraft:item/generated",("V176_B728_MODEL_PARENT_DRIFT",info)
assert info["textures"]=={"layer0":"minecraft:item/crossbow"},("V176_B728_LAYER_DRIFT",info["textures"])
assert not output.exists(),("V176_B728_ICON_ALREADY_EXISTS",str(output))

# Each power-armor weapon upgrade has its own recognizable circuit/dual-gun
# silhouette. Keep the 32px pixel grid crisp; Minecraft downsamples to 16px.
im=Image.new("RGBA",(32,32),(0,0,0,0))
d=ImageDraw.Draw(im)
# Floating metallic board, navy/rifle-metal shadow and cyan bevel.
d.rounded_rectangle((2,3,29,29),radius=5,fill=(9,15,24,255),
                    outline=(54,72,88,255),width=1)
d.rounded_rectangle((4,4,27,26),radius=4,fill=(27,39,52,255),
                    outline=(109,133,145,255),width=1)
d.rectangle((7,6,24,7),fill=(69,97,116,255))
d.line([(6,9),(6,23)],fill=(39,67,86,255),width=2)
d.line([(25,9),(25,23)],fill=(15,26,39,255),width=2)
# Two extended futuristic gun barrels (not arrows, swords or crossbows).
for y in (11,18):
 d.rectangle((8,y,22,y+3),fill=(91,110,120,255))
 d.rectangle((10,y,20,y),fill=(176,195,199,255))
 d.rectangle((11,y+2,21,y+2),fill=(47,63,74,255))
 d.rectangle((21,y-1,26,y+4),fill=(15,21,29,255))
 d.rectangle((24,y,28,y+3),fill=(102,121,134,255))
 d.rectangle((27,y+1,29,y+2),fill=(11,18,24,255))
 d.point((29,y+1),fill=(66,230,240,255))
# Reactor-powered mounting mechanism and glowing charging conduit.
d.rectangle((9,15,20,17),fill=(11,18,30,255))
d.rectangle((14,14,17,19),fill=(45,204,224,255))
d.rectangle((15,15,16,18),fill=(189,247,243,255))
d.rectangle((8,24,23,25),fill=(34,166,192,255))
for x in (7,12,19,24):
 d.point((x,27),fill=(79,120,132,255))
# Hardened rivets and subtle magenta Network Storage accent.
for x in (7,24):
 for y in (8,22):
  d.point((x,y),fill=(199,216,219,255))
d.rectangle((13,5,19,5),fill=(206,59,204,255))
assert im.getbbox() and len(im.getcolors(1024) or [])>=12
output.parent.mkdir(parents=True,exist_ok=True)
im.save(output,optimize=True)
info["textures"]["layer0"]="obsidiannetwork:item/power_card_micro_mg"
model.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert output.stat().st_size>150
with Image.open(output) as check:
 assert check.size==(32,32) and check.mode=="RGBA"
 assert check.getpixel((0,0))[3]==0
print("V176_B728_MICRO_MG_INVENTORY_ICON_REAL_32PX_PNG_AND_MODEL_PASS")
