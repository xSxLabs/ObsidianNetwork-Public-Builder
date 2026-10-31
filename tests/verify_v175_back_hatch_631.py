#!/usr/bin/env python3
"""B631: ensure true rear-only entry/exit without static interior collisions."""
import hashlib,json,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 model=json.loads((A/"geckolib/models/entity"/(name+".geo.json")).read_text())
 animations=json.loads((A/"geckolib/animations/entity"/(name+".animation.json")).read_text())["animations"]
 idx={b["name"]:b for b in model["minecraft:geometry"][0]["bones"]}
 assert len(idx)==28,(mk,"lost authored shell")
 assert len(idx["spine"]["cubes"])==1,(mk,"front must be ONLY fixed front plate")
 assert len(idx["torso_inner_spine"]["cubes"])==4,(mk,"static interior moved")
 assert idx["torso_inner_spine"]["parent"]=="spine"
 assert idx["rear_left"]["pivot"]==[-4.4,20,3.4] and idx["rear_right"]["pivot"]==[4.4,20,3.4]
 assert idx["faceplate"]["parent"]=="helmet" and idx["visor"]["parent"]=="faceplate"
 assert idx["visor"].get("cubes") is None,(mk,"extra faceplate reintroduced")
 for action in ("equip","unequip"):
  c=animations["animation.power_armor."+action]
  assert c["animation_length"]==1.0,(mk,action)
  bone=c["bones"]
  for n in ("chest_left","chest_right"):
   for channel in ("rotation","position"):
    assert all(frame["vector"]==[0,0,0] for frame in bone[n][channel].values()),(mk,action,n,"front opens")
  for n in ("rear_left","rear_right"):
   # The external door is moving, not a static lid/placeholder.
   frames=bone[n]["rotation"].values()
   assert max(abs(f["vector"][1]) for f in frames)>=78,(mk,action,n,"rear hinge frozen")
  mask=bone["faceplate"]["rotation"].values()
  assert max(abs(f["vector"][0]) for f in mask)>=90,(mk,action,"faceplate frozen")
  scales=bone["torso_inner_spine"]["scale"]
  assert scales["0.0"]["vector"]==scales["1.0"]["vector"]==[1,1,1],(mk,action,"interior not restored")
  assert scales["0.12"]["vector"]==scales["0.76"]["vector"]==[0,0,0],(mk,action,"interior visible while hatch opens")
  assert len(scales)==6
  for n in ("left_leg","right_leg","left_forearm","right_forearm"):
   assert all(f["vector"]==[0,0,0] for f in bone[n]["rotation"].values()),(mk,action,n,"disconnected box movement")
 # Exact wearer outer UVs still reside on actual rear pieces and mask.
 assert idx["rear_left"]["cubes"][0]["uv"]["south"]=={"uv":[32,20],"uv_size":[4,12]}
 assert idx["rear_right"]["cubes"][0]["uv"]["south"]=={"uv":[36,20],"uv_size":[4,12]}
 assert idx["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 for clip in ("recall_flight","recall_brake","recall_dock"):
  c=animations["animation.power_armor."+clip]
  assert "torso_inner_spine" not in c["bones"],(mk,"recall inner geometry must remain intact")
  assert len(c["bones"]["root"]["rotation"])>0
 assert animations["animation.power_armor.recall_dock"]["animation_length"]==2.0
 assert animations["animation.power_armor.recall_brake"]["animation_length"]==.60
 assert all(frame["vector"][0]==90 for frame in
       animations["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
tex=(J/"powerarmor/PowerArmorRecall.java").read_text()
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
assert "progress<12?3:4" in tex and "if(progress<52)" in tex
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in tex
assert world.count("new Animation(stand,20,entering,")==3
assert "v175RestoreWorldSuitOnLoad" in world
print("V175_B631_BACK_OPEN_SAFE_PASS: all 24 exterior worn textured suits, rear split only, inner scales zero while open/one when closed, original recall unchanged")
