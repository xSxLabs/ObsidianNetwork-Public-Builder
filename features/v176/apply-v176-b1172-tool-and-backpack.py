#!/usr/bin/env python3
"""B1172: rebuild IN-GAME Netherite tool model to match black/purple curved axe/pick.

Also reduce only stored-item numerical overlay in backpack (~78%).
Does not touch recipes, tools' mechanics, armor, turret or cells.
"""
import os, json
from pathlib import Path
from PIL import Image
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
model=A/"models/item/multitool.json"
atlas=A/"textures/item/multitool_3d.png"
assert model.exists() and atlas.exists(),"B1172_MULTITOOL_GENERATOR_NOT_RUN"
data=json.loads(model.read_text(encoding="utf-8"))
assert len(data.get("elements",[]))>20 and data["textures"]["palette"]=="obsidiannetwork:item/multitool_3d"
# 4x4 tiles within a 64x64 texture. UV coordinates must be 0..16, not 0..64.
# Dark Netherite with metallic bevels and vivid amethyst luminous engravings.
colors=[
 (13,12,19),(28,27,38),(42,40,54),(65,61,78),
 (87,82,106),(116,110,133),(153,147,165),(195,186,207),
 (37,14,55),(78,26,111),(148,40,214),(223,92,255),
 (39,28,61),(90,55,126),(184,94,247),(246,177,255)]
tex=Image.new("RGBA",(64,64))
for t,c in enumerate(colors):
 x=(t%4)*16;y=(t//4)*16
 for dy in range(16):
  for dx in range(16):
   grain=((dx*13+dy*7+t*5)%11)-5
   bevel=9 if dx<=1 or dy<=1 else (-10 if dx>=14 or dy>=14 else 0)
   tex.putpixel((x+dx,y+dy),tuple(max(0,min(255,k+grain+bevel)) for k in c)+(255,))
tex.save(atlas)
parts=[]
def cub(a,b,t,edge=None,rotation=None):
 assert all(0<=v<=16 for v in a+b) and all(x<y for x,y in zip(a,b)),(a,b)
 def uv(tile):
  x=(tile%4)*4;y=(tile//4)*4
  return [x,y,x+4,y+4]
 faces={f:{"texture":"#palette","uv":uv(edge if edge is not None and f in ("north","east","up") else t)}
        for f in ("north","south","east","west","up","down")}
 o={"from":a,"to":b,"faces":faces}
 if rotation:
  o["rotation"]={"origin":[8,12,8],"axis":"z","angle":rotation,"rescale":True}
 parts.append(o)
# 12-pixel forged two-layer handle, armor plates and neon etched spine.
cub([7,0,7.0],[9,11.55,9.0],1,3)
cub([7.3,.1,6.7],[8.7,11,7.05],2,4)
cub([7.3,.1,8.95],[8.7,11,9.3],0,2)
cub([6.7,.1,7.3],[7.05,11,8.7],0,2)
cub([8.95,.1,7.3],[9.3,11,8.7],2,4)
cub([7.78,1.1,6.49],[8.23,9.9,6.78],10,11)
for y in (1.3,3.5,5.7,7.9,10.1):
 cub([6.7,y,6.55],[9.3,y+.30,9.45],1,3)
 cub([7.4,y+.08,6.35],[8.6,y+.24,6.58],9,11)
cub([6.5,0,6.45],[9.5,.9,9.55],2,5)
cub([7.45,.15,6.20],[8.55,.7,6.5],10,15)
# Main reinforced hub, faceted, layered, central glowing hex jewel.
cub([5.0,10.3,5.35],[11.0,14.0,10.65],1,4)
cub([5.5,11.1,5.0],[10.5,13.8,5.35],3,6)
cub([5.5,11.1,10.65],[10.5,13.8,11.0],2,5)
cub([7.2,11.7,4.75],[8.8,13.25,5.05],9,14)
cub([7.55,12.05,4.57],[8.45,12.92,4.78],11,15)
# Broad asymmetric AXE at -X: jagged crescent shoulder and concave waist.
cub([3.8,10.8,5.7],[6.1,15.0,10.3],2,5)
cub([2.8,12.3,5.8],[4.1,15.5,10.2],3,6)
cub([1.8,13.15,6.0],[3.2,15.8,10.0],4,7)
cub([.9,14.1,6.3],[2.15,15.9,9.7],5,7)
cub([.4,14.7,6.9],[1.1,15.95,9.1],6,15)
cub([3.2,9.6,5.9],[4.65,12.0,10.1],2,4)
cub([2.2,8.75,6.3],[3.55,10.6,9.7],3,5)
cub([1.3,8.2,6.7],[2.45,9.55,9.3],4,6)
cub([.45,7.75,7.2],[1.5,8.65,8.8],5,7)
# Visible thin violet AXT cutting edge and angled energy channels on BOTH faces.
for z in (5.52,10.30):
 cub([.23,14.2,z],[.72,15.8,z+.16],11,15)
 cub([.20,7.7,z],[.73,9.5,z+.16],10,11)
 cub([1.5,11.0,z],[2.05,14.5,z+.15],9,11)
 cub([3.7,12.7,z],[5.1,13.1,z+.16],10,15)
# Curved PICK at +X sweeping above right then bending down like a claw.
cub([10.5,11.5,5.9],[12.3,14.6,10.1],2,4)
cub([11.9,12.8,6.1],[13.3,15.0,9.9],3,5)
cub([13.0,13.4,6.5],[14.5,15.1,9.5],4,6)
cub([14.1,13.2,6.9],[15.0,14.6,9.1],4,6)
cub([14.75,12.1,7.05],[15.55,13.7,8.95],3,5)
cub([15.0,10.8,7.28],[15.85,12.5,8.72],4,6)
cub([15.30,9.75,7.57],[15.95,11.15,8.43],6,7)
# Purple spine wraps around the outer curved pick.
for z in (6.08,9.75):
 cub([11.6,14.66,z],[13.25,14.91,z+.16],10,15)
 cub([13.1,14.88,z],[14.5,15.03,z+.16],10,11)
 cub([14.83,12.1,z],[15.16,14.3,z+.16],10,15)
# Small dark spike behind hub, layered forged guard details.
cub([5.4,13.75,7.1],[7.1,15.0,8.9],1,3)
cub([9.3,10.6,5.35],[10.6,11.45,10.6],2,5)
# Bright pommel and mechanical body rivets for close-up first person view.
for x in (6.65,9.15):
 cub([x,10.5,5.1],[x+.22,11.0,5.35],11)
data["elements"]=parts
data["textures"]={"palette":"obsidiannetwork:item/multitool_3d","particle":"obsidiannetwork:item/multitool_3d"}
data["display"]={
 "gui":{"rotation":[24,140,0],"translation":[0,-.5,0],"scale":[.92,.92,.92]},
 "firstperson_righthand":{"rotation":[0,-90,45],"translation":[0,1,0],"scale":[.85,.85,.85]},
 "firstperson_lefthand":{"rotation":[0,90,-45],"translation":[0,1,0],"scale":[.85,.85,.85]},
 "thirdperson_righthand":{"rotation":[0,-90,45],"translation":[0,2,0],"scale":[.74,.74,.74]},
 "thirdperson_lefthand":{"rotation":[0,90,-45],"translation":[0,2,0],"scale":[.74,.74,.74]},
 "ground":{"translation":[0,2,0],"scale":[.55,.55,.55]},
 "fixed":{"rotation":[0,180,0],"scale":[.85,.85,.85]}}
model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
assert all(0<=v<=16 for e in parts for f in e["faces"].values() for v in f["uv"])
assert len(parts)>=45
# Backpack stored count labels only, retain 100% icon size and the rest of UI.
screen=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176BackpackScreen.java"
src=screen.read_text(encoding="utf-8")
old="    g.text(font,label,slot.x+16-font.width(label),slot.y+9,0xffeffaff);"
assert src.count(old)==1,("B1172_BACKPACK_COUNT_OVERLAY_ANCHOR",src.count(old))
new="""    // B1172: 78% label, bottom right of same slot; icons unchanged.
    g.pose().pushMatrix();
    g.pose().translate(slot.x+16.0F-font.width(label)*0.78F,slot.y+10.0F);
    g.pose().scale(0.78F,0.78F);
    g.text(font,label,0,0,0xffeffaff);
    g.pose().popMatrix();"""
screen.write_text(src.replace(old,new,1),encoding="utf-8")
print("B1172_MULTITOOL_CURVED_AXE_PICK_VIOLET_3D_UV_0_16_BACKPACK_COUNT_78_PASS")
