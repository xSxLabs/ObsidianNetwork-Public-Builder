#!/usr/bin/env python3
"""Post-overlay B646: 24 skins, real head UV, no broken Recall phase boundary."""
import json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def first(t):return next(iter(t.values()))["vector"]
def last(t):return list(t.values())[-1]["vector"]
def same(a,b):return max(abs(x-y) for x,y in zip(a,b))<.0001
for mk in range(1,25):
 n=f"power_armor_visual_mk{mk}"
 model=json.loads((A/"geckolib/models/entity"/(n+".geo.json")).read_text())
 clips=json.loads((A/"geckolib/animations/entity"/(n+".animation.json")).read_text())["animations"]
 bones={b["name"]:b for b in model["minecraft:geometry"][0]["bones"]}
 assert len(bones)==38 and not bones["helmet"].get("cubes"),mk
 assert bones["faceplate"]["parent"]=="helmet"
 assert bones["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 for side,sign in (("left",-1),("right",1)):
  h=bones["helmet_"+side]
  assert h["parent"]=="helmet" and len(h["cubes"])==4,mk
  assert h["pivot"]==[4.5*sign,29,3.55],mk
  assert h["cubes"][0]["uv"]["south"]=={"uv":[24 if side=="left" else 28,8],"uv_size":[4,8]},mk
  assert h["cubes"][2]["uv"]["up"]=={"uv":[8 if side=="left" else 12,0],"uv_size":[4,8]},mk
  assert h["cubes"][3]["uv"]["down"]=={"uv":[16 if side=="left" else 20,0],"uv_size":[4,8]},mk
 for action in ("equip","unequip"):
  c=clips["animation.power_armor."+action]
  assert c["animation_length"]==4.0,mk
  for side in ("left","right"):
   f=c["bones"]["helmet_"+side]["rotation"]
   assert first(f)==last(f)==[0,0,0],(mk,action,side)
   assert max(abs(v["vector"][1]) for v in f.values())>100,(mk,action,side)
  f=c["bones"]["faceplate"]
  assert first(f["position"])==last(f["position"])==[0,0,0]
  assert first(f["rotation"])==last(f["rotation"])==[0,0,0]
  assert max(v["vector"][1] for v in f["position"].values())>2.7
  assert min(v["vector"][0] for v in f["rotation"].values())<=-89
  assert max(v["vector"][2] for v in f["position"].values())<.25
 app=clips["animation.power_armor.recall_approach"]
 brake=clips["animation.power_armor.recall_brake"]
 dock=clips["animation.power_armor.recall_dock"]
 assert (app["animation_length"],brake["animation_length"],dock["animation_length"])==(.55,.6,2.)
 assert first(brake["bones"]["root"]["rotation"])==[90,0,0]
 assert last(brake["bones"]["root"]["rotation"])==first(dock["bones"]["root"]["rotation"])==[0,0,0]
 for bone,tracks in app["bones"].items():
  if bone=="root":continue
  for kind,v in tracks.items():
   assert same(last(v),first(brake["bones"][bone][kind])),(mk,bone,kind,"approach->brake reset")
   assert same(last(brake["bones"][bone][kind]),first(dock["bones"][bone][kind])),(mk,bone,kind,"brake->dock reset")
 for side in ("left","right"):
  name="helmet_"+side
  assert last(brake["bones"][name]["rotation"])==first(dock["bones"][name]["rotation"]),(mk,name)
  assert last(dock["bones"][name]["rotation"])==[0,0,0]
 for name in ("recall_brake","recall_dock"):
  c=clips["animation.power_armor."+name]
  assert all(float(t)<=c["animation_length"]+.0001 for tr in c["bones"].values() for f in tr.values() for t in f),(mk,name,"keyframe beyond clip")
 b=brake["bones"]["faceplate"]["rotation"]
 d=dock["bones"]["faceplate"]["rotation"]
 assert first(b)==[0,0,0] and last(b)==first(d)==[-90,0,0] and last(d)==[0,0,0]
 skin="power_armor" if mk==1 else "power_armor_mk"+str(mk)
 with Image.open(A/"textures/entity"/(n+".png")) as img:atlas=img.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid"/(skin+".png")) as img:worn=img.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==worn.tobytes(),(mk,"original skin changed")
print("V175_B646_ALL_24_ORIGINAL_SKINS_HELMET_AND_RECALL_PHASES_PASS")
