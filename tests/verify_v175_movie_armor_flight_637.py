#!/usr/bin/env python3
"""B637 finished-model and runtime checks. All 24 original equipment skins."""
import json,os,math
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
parts=("arm_back_shell","forearm_back_shell","thigh_back_shell","boot_back_shell")
for mk in range(1,25):
 n=f"power_armor_visual_mk{mk}"
 model=json.loads((A/"geckolib/models/entity"/(n+".geo.json")).read_text())
 anim=json.loads((A/"geckolib/animations/entity"/(n+".animation.json")).read_text())
 index={b["name"]:b for b in model["minecraft:geometry"][0]["bones"]}
 assert len(index)==36,(mk,"8 back shell bones missing")
 mask=index["faceplate"]["cubes"][0]
 assert mask["size"]==[8,8,.96],(mk,"mask distorted")
 assert mask["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]},(mk,"wrong eye source")
 assert "cubes" not in index["visor"],(mk,"double eyes")
 assert index["spine"].get("cubes")==[],(mk,"double front")
 for side in ("left","right"):
  for suffix in parts:
   bone=index[f"{side}_{suffix}"]
   assert len(bone["cubes"])==1
   assert bone["parent"] in index
   assert bone["cubes"][0]["uv"]["south"]["uv"][0] in (12,52)
  for p in ("leg","boot"):
   b=index[f"{side}_{p}"]
   assert len(b["cubes"])==2,(mk,p,"legs have no opaque backing")
 for action in ("equip","unequip"):
  clip=anim["animations"]["animation.power_armor."+action]
  assert clip["animation_length"]==2.4
  tracks=clip["bones"]
  assert all(v["vector"]==[0,0,0] for v in tracks["faceplate"]["rotation"].values()),(mk,action,"mask still hinges")
  moves=[v["vector"] for v in tracks["faceplate"]["position"].values()]
  assert max(v[2] for v in moves)>=7.8 and max(v[1] for v in moves)>=7.0,(mk,action,"mask does not slide over crown")
  assert moves[0]==moves[-1]==[0,0,0],(mk,action,"mask not closed")
  for side in ("left","right"):
   for suffix in parts:
    k=tracks[f"{side}_{suffix}"]["rotation"]
    assert max(abs(v["vector"][1]) for v in k.values())>=100,(mk,action,suffix,"back hatch frozen")
    assert list(k.values())[0]["vector"]==list(k.values())[-1]["vector"]==[0,0,0]
   assert max(abs(v["vector"][2]) for v in tracks[f"{side}_arm"]["rotation"].values())>=30
   assert max(abs(v["vector"][2]) for v in tracks[f"{side}_leg"]["rotation"].values())>=19
 for mode in ("recall_brake","recall_dock"):
  c=anim["animations"]["animation.power_armor."+mode]
  assert c["animation_length"]==(.6 if mode=="recall_brake" else 2.0)
  mask=c["bones"]["faceplate"]
  assert all(v["vector"]==[0,0,0] for v in mask["rotation"].values())
  assert max(v["vector"][2] for v in mask["position"].values())>=7.8,(mk,mode)
  assert all(x in c["bones"] for x in ("rear_left","rear_right","spine","helmet","left_arm","right_arm"))
 assert all(x["vector"][0]==90 for x in anim["animations"]["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
 asset="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity/equipment/humanoid"/(asset+".png")) as f:top=f.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid_leggings"/(asset+".png")) as f:leg=f.convert("RGBA")
 with Image.open(A/"textures/entity"/(n+".png")) as f:atlas=f.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),(mk,"worn body changed")
 assert atlas.crop((0,32,64,64)).tobytes()==leg.tobytes(),(mk,"worn leggings changed")
 assert atlas.crop((8,8,16,16)).tobytes()==top.crop((8,8,16,16)).tobytes(),(mk,"eyes no longer exact")
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
client=(J/"client/PowerArmorBuild98Client.java").read_text()
assert world.count("new Animation(stand,48,entering,")==3
assert "pose(stand,48,false)" in world and "pose(stand,20,false)" not in world
assert "V175_B633_EXIT_BACK_TO_PLAYER" in world
assert "BlockPos p=player.blockPosition().relative(player.getDirection());" in world
assert "distance<=6.0D || DOCKING.containsKey(player.getUUID())" in rec
assert "if(progress<52)" in rec and "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
assert "V175_HEAD_FIRST_JETS" in rec
assert "V175_B637_CREATIVE_JETS" in client
assert "p.getAbilities().flying" in client
assert 'if(card.equals("flight"))hasFlightCard=true;' in client
assert "creativeArmor=complete&&hasFlightCard" in client
assert "PowerArmorElytraBridge.chest(p)" in client
assert client.count("for(var p:mc.level.players())")==1
assert client.count("for(int limb=0;limb<4;limb++)")==1
assert "creativeArmor?-.14D" in client
assert "ParticleTypes.END_ROD" in client and "ParticleTypes.CLOUD" in client
print("V175_B637_FULL_GATE_PASS: all 24 true eye/body/leg pixels, 8 hinged limb shells, 8x8 sliding faceplate, opaque leg backing, early recall, 48-tick neutral exit, powered creative-flight jets")
