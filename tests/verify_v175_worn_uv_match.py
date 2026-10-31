#!/usr/bin/env python3
"""B630 fail-closed, actual equipment-art identity for ALL MK1..MK24 visuals."""
import hashlib,json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def uv(bone,side,index=0):
 return bone["cubes"][index]["uv"][side]
def check(rect,x,y,w,h,why):
 assert rect["uv"]==[x,y] and rect["uv_size"]==[w,h],(why,rect)
def exact(a,b,why):
 assert a.tobytes()==b.tobytes(),why

textures=[]
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 equip="power_armor" if mk==1 else f"power_armor_mk{mk}"
 art=A/"textures/entity/equipment"
 with Image.open(art/"humanoid"/(equip+".png")) as im:
  worn=im.convert("RGBA")
 with Image.open(art/"humanoid_leggings"/(equip+".png")) as im:
  leggings=im.convert("RGBA")
 with Image.open(A/"textures/entity"/(stem+".png")) as im:
  atlas=im.convert("RGBA")
 assert atlas.size==(128,128) and worn.size==(64,32) and leggings.size==(64,32)
 exact(atlas.crop((0,0,64,32)),worn,(mk,"upper worn armor pixels changed"))
 exact(atlas.crop((0,32,64,64)),leggings,(mk,"leggings worn armor pixels changed"))
 textures.append(hashlib.sha256(worn.tobytes()+leggings.tobytes()).hexdigest())
 md=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
 bs=md["minecraft:geometry"][0]["bones"]
 bones={b["name"]:b for b in bs}
 assert len(bs)==len(bones)==28
 check(uv(bones["faceplate"],"north"),8,8,8,8,(mk,"mask exact worn face"))
 assert bones["visor"]["parent"]=="faceplate"
 assert not bones["visor"].get("cubes"),(mk,"duplicate old-visored flat strip")
 assert bones["faceplate"]["parent"]=="helmet"
 check(uv(bones["helmet"],"south"),24,8,8,8,(mk,"helmet back"))
 check(uv(bones["helmet"],"west",1),0,8,8,8,(mk,"helmet left"))
 check(uv(bones["helmet"],"east",2),16,8,8,8,(mk,"helmet right"))
 check(uv(bones["helmet"],"up",3),8,0,8,8,(mk,"helmet roof"))
 check(uv(bones["spine"],"north"),20,20,8,12,(mk,"real chest front"))
 check(uv(bones["spine"],"west",1),16,20,4,12,(mk,"real chest left"))
 check(uv(bones["spine"],"east",2),28,20,4,12,(mk,"real chest right"))
 check(uv(bones["rear_left"],"south"),32,20,4,12,(mk,"back left half"))
 check(uv(bones["rear_right"],"south"),36,20,4,12,(mk,"back right half"))
 check(uv(bones["chest_left"],"north"),20,20,4,12,(mk,"chest left half"))
 check(uv(bones["chest_right"],"north"),24,20,4,12,(mk,"chest right half"))
 # Rear shell shares the actual worn torso back, split without gap/overlap.
 left=uv(bones["rear_left"],"south");right=uv(bones["rear_right"],"south")
 assert left["uv"][0]+left["uv_size"][0]==right["uv"][0]
 for part in ("left_arm","right_arm"):
  check(uv(bones[part],"north"),44,20,4,5,(mk,part))
 for part in ("left_forearm","right_forearm"):
  check(uv(bones[part],"north"),44,25,4,7,(mk,part))
 for part in ("left_leg","right_leg"):
  check(uv(bones[part],"north"),4,52,4,9,(mk,part))
 for part in ("left_boot","right_boot"):
  check(uv(bones[part],"north"),4,29,4,3,(mk,part))
 check(uv(bones["reactor"],"north"),22,23,4,4,(mk,"reactor worn front"))
 for bone in bones.values():
  for cube in bone.get("cubes",[]):
   assert set(cube["uv"])=={"north","south","east","west","up","down"},(mk,bone["name"])
   for side,face in cube["uv"].items():
    x,y=face["uv"];w,h=face["uv_size"]
    assert min(x,y)>=0 and min(w,h)>0 and x+w<=128.001 and y+h<=128.001,(mk,bone["name"],side)
 an=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())
 assert len(an["animations"])==7
 flight=an["animations"]["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"]
 assert all(k["vector"][0]==90 for k in flight.values()),(mk,"must not change recall")
 for typ in ("equip","unequip"):
  assert an["animations"]["animation.power_armor."+typ]["animation_length"]==1.0,(mk,typ,"normal timing")
 assert an["animations"]["animation.power_armor.recall_dock"]["animation_length"]==2.0,(mk,"recall dock timing")
assert len(textures)==24 and len(set(textures))==24,("MK tier textures not individually distinct",len(set(textures)))
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
visual=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
assert world.count("new Animation(stand,20,entering,")==3
assert "int t=21-animation.ticks();" in world
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
assert "progress<12?3:4" in rec and "if(progress<52)" in rec
assert "V175_HEAD_FIRST_JETS" in rec
assert "PowerArmorRecall.isVisualActive(getUUID())" in visual
print("V175_B630_WORN_UV_IDENTITY_PASS: exact pixel-identical worn humanoid+leggings 24/24; single mask, physical back UV, 28/28 textured bones, unchanged recall/normal timings")
