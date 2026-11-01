#!/usr/bin/env python3
"""B648 final generated Geo JSON and 24-skin regression gate."""
import json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def pose(c,k):return c[k]["vector"]
for mk in range(1,25):
 name="power_armor_visual_mk"+str(mk)
 model=json.loads((A/"geckolib/models/entity"/(name+".geo.json")).read_text())
 clips=json.loads((A/"geckolib/animations/entity"/(name+".animation.json")).read_text())["animations"]
 bone={b["name"]:b for b in model["minecraft:geometry"][0]["bones"]}
 assert len(bone)==40,mk
 mask=bone["faceplate"]["cubes"][0]["uv"]
 assert mask["south"]==mask["north"]=={"uv":[8,8],"uv_size":[8,8]},(mk,"face interior != original")
 for side,sign in (("left",-1),("right",1)):
  unit=side+"_entry_unit"
  assert bone[unit]["parent"]=="root" and "cubes" not in bone[unit],(mk,"new divider")
  assert bone[unit]["pivot"]==[sign*6.3,23,0]
  assert bone[side+"_arm"]["parent"]==bone["rear_"+side]["parent"]==unit
  assert bone["rear_"+side]["pivot"]==[sign*4.4,20,2.7]
  for mode in ("equip","unequip"):
   clip=clips["animation.power_armor."+mode]
   assert clip["animation_length"]==4.,mk
   p=clip["bones"]["rear_"+side]["rotation"]
   g=clip["bones"][unit]["rotation"]
   assert pose(p,"0.0")==pose(p,"4.0")==pose(g,"0.0")==pose(g,"4.0")==[0,0,0]
   assert abs(pose(p,"1.2")[1])>110 and pose(g,"1.2")==[0,0,0],(mk,"fold rear before swing")
   assert abs(pose(g,"1.96")[1])>87 and abs(pose(p,"1.96")[1])>110,(mk,"coupled wing")
   assert pose(g,"3.2")==[0,0,0] and abs(pose(p,"3.2")[1])>110,(mk,"reverse closure")
   for part in (side+"_arm",side+"_forearm",side+"_arm_back_shell",side+"_forearm_back_shell"):
    assert all(k["vector"]==[0,0,0] for k in clip["bones"][part]["rotation"].values()),(mk,"extra hinge",part)
 for mode in ("equip","unequip"):
  c=clips["animation.power_armor."+mode]
  guard=c["bones"]["torso_inner_spine"]["scale"]
  assert pose(guard,"0.2433")==pose(guard,"3.52")==[0,0,0],(mk,"interior walls")
  assert c["bones"]["faceplate"]["position"]["4.0"]["vector"]==[0,0,0]
 for phase in ("recall_approach","recall_brake","recall_dock"):
  c=clips["animation.power_armor."+phase]
  assert all(side+"_entry_unit" not in c["bones"] for side in ("left","right"))
  assert all(float(t)<=c["animation_length"]+.0001 for v in c["bones"].values() for frames in v.values() for t in frames),(mk,phase)
 skin="power_armor" if mk==1 else "power_armor_mk"+str(mk)
 with Image.open(A/"textures/entity"/(name+".png")) as im:atlas=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid"/(skin+".png")) as im:top=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid_leggings"/(skin+".png")) as im:leg=im.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes()
 assert atlas.crop((0,32,64,64)).tobytes()==leg.tobytes()
print("B648_ALL_24_ORIGINAL_SKINS_NO_DIVIDERS_TWO_STAGE_ENTRY_AND_FACE_UV_PASS")
