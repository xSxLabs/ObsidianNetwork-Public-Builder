#!/usr/bin/env python3
"""B632 gate: all 24 Mk worn-shell 3D proportions, exact UVs, and unchanged recall."""
import json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def expect(idx,bn,n,origin,size):
 obj=idx[bn]["cubes"][n]
 assert obj["origin"]==origin and obj["size"]==size,(bn,n,obj["origin"],obj["size"])
 assert set(obj["uv"])=={"north","south","east","west","up","down"}
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 model=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
 clips=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())["animations"]
 idx={b["name"]:b for b in model["minecraft:geometry"][0]["bones"]}
 assert len(idx)==28,(mk,"B631 rig altered")
 expect(idx,"spine",0,[-4.4,13,-3.4],[8.8,12,.8])
 expect(idx,"chest_left",0,[-4.4,13,-3.55],[4.35,12,.2])
 expect(idx,"chest_right",0,[.05,13,-3.55],[4.35,12,.2])
 expect(idx,"rear_left",0,[-4.4,13,2.5],[4.35,12,.9])
 expect(idx,"rear_right",0,[.05,13,2.5],[4.35,12,.9])
 expect(idx,"faceplate",0,[-4.5,25,-4.5],[9,8.5,.95])
 expect(idx,"left_arm",0,[-9.45,19,-2.5],[5,6,5])
 expect(idx,"right_arm",0,[4.45,19,-2.5],[5,6,5])
 expect(idx,"left_forearm",0,[-9.45,13,-2.5],[5,6,5])
 expect(idx,"right_forearm",0,[4.45,13,-2.5],[5,6,5])
 expect(idx,"left_leg",0,[-5.1,4,-2.5],[4.9,9,5])
 expect(idx,"right_leg",0,[.2,4,-2.5],[4.9,9,5])
 expect(idx,"left_boot",0,[-5.1,0,-2.5],[4.9,4,5])
 expect(idx,"right_boot",0,[.2,0,-2.5],[4.9,4,5])
 expect(idx,"torso_inner_spine",1,[-4.4,13,-2.6],[.95,12,5.1])
 expect(idx,"torso_inner_spine",2,[3.45,13,-2.6],[.95,12,5.1])
 assert idx["spine"]["cubes"][0]["uv"]["north"]=={"uv":[20,20],"uv_size":[8,12]},mk
 assert idx["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]},mk
 assert idx["rear_left"]["cubes"][0]["uv"]["south"]=={"uv":[32,20],"uv_size":[4,12]},mk
 assert idx["rear_right"]["cubes"][0]["uv"]["south"]=={"uv":[36,20],"uv_size":[4,12]},mk
 assert idx["torso_inner_spine"]["parent"]=="spine"
 assert idx["faceplate"]["parent"]=="helmet"
 assert idx["visor"]["parent"]=="faceplate" and "cubes" not in idx["visor"]
 assert idx["rear_left"]["pivot"]==[-4.4,20,3.4]
 assert idx["rear_right"]["pivot"]==[4.4,20,3.4]
 for typ in ("equip","unequip"):
  clip=clips["animation.power_armor."+typ]
  assert clip["animation_length"]==1.0,(mk,typ)
  for side in ("chest_left","chest_right"):
   for track in ("position","rotation"):
    assert all(x["vector"]==[0,0,0] for x in clip["bones"][side][track].values()),(mk,side,track)
  carrier=clip["bones"]["torso_inner_spine"]["scale"]
  assert carrier["0.0"]["vector"]==carrier["1.0"]["vector"]==[1,1,1],(mk,"interior end state")
  assert carrier["0.12"]["vector"]==carrier["0.76"]["vector"]==[0,0,0],(mk,"interior opening")
 assert clips["animation.power_armor.recall_dock"]["animation_length"]==2.0
 assert clips["animation.power_armor.recall_brake"]["animation_length"]==.60
 assert all(f["vector"][0]==90 for f in
   clips["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
 eq="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity/equipment/humanoid"/(eq+".png")) as im: top=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid_leggings"/(eq+".png")) as im: leg=im.convert("RGBA")
 with Image.open(A/"textures/entity"/(stem+".png")) as im: atlas=im.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),(mk,"worn upper pixels")
 assert atlas.crop((0,32,64,64)).tobytes()==leg.tobytes(),(mk,"worn leg pixels")
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
assert world.count("new Animation(stand,20,entering,")==3
assert "BUILD117_EXIT_FRONT_FACING" in world,( "player exit placement must stay in front" )
assert "BlockPos p=player.blockPosition().relative(player.getDirection());" in world
assert "progress<12?3:4" in rec and "if(progress<52)" in rec
assert "V175_HEAD_FIRST_JETS" in rec
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
print("V175_B632_WORN_SHELL_GATE_PASS: 24 MK models, wearer-proportioned 3D parts, exact worn PNG pixels, rear hatch only, no player movement or recall changes")
