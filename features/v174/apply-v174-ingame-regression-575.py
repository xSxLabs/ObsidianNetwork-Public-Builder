#!/usr/bin/env python3
"""B575 fix: blue thin ENERGY input, real reactor MAX FE/t and joined glass."""
import json,os
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def change(file,a,b):
 p=J/file;s=p.read_text()
 assert s.count(a)==1,("B575_SOURCE_DRIFT",file,a,s.count(a))
 p.write_text(s.replace(a,b,1))
change("client/V174MachineScreen.java",
 "long b568Maximum=ctrl.guiFormed()?120L*ctrl.guiRodAssemblies():0L;",
 "long b568Maximum=120L*Math.max(0,ctrl.guiRodAssemblies()); // B575_REACTOR_MAX_SYNCED_RODS")
f="client/EnergyCableInputRenderer.java"
for a,b in (
 ("3/16f,0,3/16f,10/16f,3/16f,10/16f","5/16f,0,5/16f,6/16f,2/16f,6/16f"),
 ("3/16f,13/16f,3/16f,10/16f,3/16f,10/16f","5/16f,14/16f,5/16f,6/16f,2/16f,6/16f"),
 ("3/16f,3/16f,0,10/16f,10/16f,3/16f","5/16f,5/16f,0,6/16f,6/16f,2/16f"),
 ("3/16f,3/16f,13/16f,10/16f,10/16f,3/16f","5/16f,5/16f,14/16f,6/16f,6/16f,2/16f"),
 ("0,3/16f,3/16f,3/16f,10/16f,10/16f","0,5/16f,5/16f,2/16f,6/16f,6/16f"),
 ("13/16f,3/16f,3/16f,10/16f,10/16f","14/16f,5/16f,5/16f,2/16f,6/16f,6/16f")
):change(f,a,b)
p=J/f;s=p.read_text()
assert "XSX_ENERGY_INPUT_COLLAR.get().defaultBlockState()" in s
p.write_text("// B575_SLIM_BLUE_INPUT_SOCKET: 6/16 cyan, 2/16 depth.\n"+s)
p=A/"textures/block/xsx_energy_input_collar.png"
with Image.open(p) as im:assert im.size==(16,16)
def pixel(x,y):
 if x in (0,15) or y in (0,15):return (19,106,154,255)
 if x in (1,14) or y in (1,14):return (27,145,191,255)
 if x in (2,13) or y in (2,13):return (45,195,231,255)
 if x in (3,12) or y in (3,12):return (91,225,250,255)
 if 5<=x<=10 and 5<=y<=10:return (34,184,229,255)
 return (40,168,213,255)
im=Image.new("RGBA",(16,16));im.putdata([pixel(x,y) for y in range(16) for x in range(16)])
im.save(p,optimize=True)
for name,rgba in (("reactor_glass_formed",(43,104,148,81)),
                  ("reactor_glass_formed_lit",(49,160,232,103))):
 sprite=A/"textures/block"/(name+".png")
 with Image.open(sprite) as old:assert old.size==(32,32) and old.mode=="RGBA",name
 Image.new("RGBA",(32,32),rgba).save(sprite,optimize=True)
 model=A/"models/block"/(name+".json")
 d=json.loads(model.read_text());assert d["parent"] in ("minecraft:block/cube","minecraft:block/cube_all"),name
 d["ambientocclusion"]=False
 model.write_text(json.dumps(d,indent=2)+"\n")
print("B575_REACTOR_CONNECTED_GLASS_MAX_FE_BLUE_SLIM_ENERGY_INPUT_PASS")
