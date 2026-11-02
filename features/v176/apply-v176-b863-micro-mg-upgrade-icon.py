#!/usr/bin/env python3
"""B863 v1.7.6: restore Micro-MG upgrade card visual parity with other
Power Armor upgrade cards without changing its registry, recipe or properties.
Apply AFTER B847/B862. Source-only change, buildlock remains active.
"""
import json
import os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ["V1_RESOURCE_ROOT"])
assets=R/"assets/obsidiannetwork"
model=assets/"models/item/power_card_micro_mg.json"
data=json.loads(model.read_text(encoding="utf-8"))
assert data.get("parent")=="minecraft:item/generated",("B863_UPGRADE_PARENT_DRIFT",data.get("parent"))
assert data.get("textures",{}).get("layer0")=="obsidiannetwork:item/power_card_micro_mg",("B863_UPGRADE_MODEL_DRIFT",data.get("textures"))
# Same vanilla nether-star background as the installed existing Power Armor cards;
# only the small transparent emblem is unique to the Micro-MG.
data["textures"]={
 "layer0":"minecraft:item/nether_star",
 "layer1":"obsidiannetwork:item/power_card_micro_mg"}
model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
icon=assets/"textures/item/power_card_micro_mg.png"
assert icon.is_file(),("B863_UPGRADE_TEXTURE_MISSING",str(icon))
im=Image.new("RGBA",(32,32),(0,0,0,0))
d=ImageDraw.Draw(im)
# Single right-upper-arm gun, not a full-opaque 32px panel blocking the star.
d.rounded_rectangle((11,12,26,24),radius=2,
 fill=(18,43,69,236),outline=(102,183,218,255),width=1)
d.rectangle((13,14,21,17),fill=(65,104,131,255))
d.rectangle((15,17,23,19),fill=(165,200,218,255))
d.rectangle((22,16,28,18),fill=(138,211,231,255))
d.rectangle((24,16,27,17),fill=(33,64,88,255))
d.rectangle((13,21,19,22),fill=(66,219,240,255))
d.point((28,17),fill=(235,249,255,255))
im.save(icon,optimize=True)
assert im.getpixel((0,0))[3]==0 and im.getpixel((15,17))[3]>0
print("B863_MICRO_MG_UPGRADE_SHARED_POWER_ARMOR_CARD_STYLE_PASS_BUILDLOCK")
