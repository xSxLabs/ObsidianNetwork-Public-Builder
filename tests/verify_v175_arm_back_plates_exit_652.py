#!/usr/bin/env python3
"""B652 fail-closed: actual geometry, 64-tick exit state and Mk1-Mk24 UV."""
import json,os,math
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 m=json.loads((A/"geckolib/models/entity"/(name+".geo.json")).read_text())
 a=json.loads((A/"geckolib/animations/entity"/(name+".animation.json")).read_text())["animations"]
 b={x["name"]:x for x in m["minecraft:geometry"][0]["bones"]}
 assert len(b)==40,mk
 opened=a["animation.power_armor.exit_open"]
 closing=a["animation.power_armor.exit_close"]
 assert opened["animation_length"]==3. and closing["animation_length"]==2.
 for side,sign in (("left",-1),("right",1)):
  assert b[side+"_arm"]["parent"]==side+"_entry_unit",mk
  for part in ("arm","forearm","leg","boot"):
   assert len(b[side+"_"+part]["cubes"])==5,(mk,side,part,"hollow shell")
  for mode in ("equip","unequip","exit_open","exit_close"):
   c=a["animation.power_armor."+mode]["bones"]
   for name_part in (side+"_entry_unit",side+"_arm",side+"_forearm"):
    assert all(fr["vector"]==[0,0,0] for fr in c[name_part]["rotation"].values()),(mk,mode,name_part,"arm moved")
   for suffix in ("arm_back_shell","forearm_back_shell"):
    r=c[side+"_"+suffix]
    assert all(fr["vector"]==[1,1,1] for fr in r["scale"].values()),(mk,mode,suffix,"rear panel hidden")
    assert all(fr["vector"][0]==fr["vector"][2]==0 for fr in r["rotation"].values()),(mk,mode,suffix,"wrong hinge axis")
    if mode in ("equip","unequip","exit_open"):
     assert max(abs(fr["vector"][1]) for fr in r["rotation"].values())>100,(mk,mode,suffix,"panel not opened")
  hinge=b[side+"_arm_back_shell"]
  pivot=hinge["pivot"][0];cub=hinge["cubes"][0]
  far=max((cub["origin"][0],cub["origin"][0]+cub["size"][0]),key=lambda x:abs(x-pivot))
  angle=-105 if side=="left" else 105
  assert -(far-pivot)*math.sin(math.radians(angle))>4,(mk,side,"panel not moving backward")
 for name_part,tracks in opened["bones"].items():
  for channel,frames in tracks.items():
   assert frames["3.0"]["vector"]==closing["bones"][name_part][channel]["0.0"]["vector"],(mk,name_part,channel,"open->close jump")
   assert all(float(k)<=3.00001 for k in frames)
 for part,tracks in closing["bones"].items():
  for channel,frames in tracks.items():
   assert all(float(k)<=2.00001 for k in frames)
 for phase in ("recall_flight","recall_approach","recall_brake","recall_dock"):
  c=a["animation.power_armor."+phase]
  assert "left_entry_unit" not in c["bones"] and "right_entry_unit" not in c["bones"]
 wear="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity"/(name+".png")) as im:atlas=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid"/(wear+".png")) as im:top=im.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),mk
h=(J/"powerarmor/PowerArmorExitSequence650.java").read_text()
v=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
w=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
f=(J/"build103/Build103GameTests.java").read_text()
assert "visual.setPos(p.getX(),p.getY(),p.getZ());" in h,"preview not at wearer"
assert "visual.beginPhase(7);" in h and "p.tickCount+64" in h
assert "p.tickCount+42" not in h and "setInvisible(" not in h
assert 'case 7 -> "animation.power_armor.exit_open";' in v
assert 'case 6 -> "animation.power_armor.exit_close";' in v and "next>7" in v
assert "PowerArmorExitReveal649.begin(player)" not in w
assert not (J/"powerarmor/PowerArmorExitReveal649.java").exists()
assert "for(int step=0;step<64;step++)" in f and "if(step<63)" in f
assert f.count("completeExitOpening650(player,level,base);")==2
assert "POWER_ARMOR_REAL_ROUNDTRIP_V69" in f
print("B652_ALL_24_STATIC_ARMS_REAR_PLATES_REAL_SERVER_DELAY_VISIBLE_64T_PASS")
