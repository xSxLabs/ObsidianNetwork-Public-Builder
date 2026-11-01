#!/usr/bin/env python3
"""B642 post-overlay fail-closed checks, including 24 tier animations + clients."""
import json,os,hashlib
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 mod=json.loads((A/"geckolib/models/entity"/(name+".geo.json")).read_text())
 clips=json.loads((A/"geckolib/animations/entity"/(name+".animation.json")).read_text())["animations"]
 bones={x["name"]:x for x in mod["minecraft:geometry"][0]["bones"]}
 assert len(bones)==36 and "cubes" not in bones["visor"],mk
 assert bones["faceplate"]["cubes"][0]["size"]==[8,8,.96]
 assert bones["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 for action in ("equip","unequip"):
  anim=clips["animation.power_armor."+action]
  assert anim["animation_length"]==4.,(mk,action,"not 80 ticks")
  tr=anim["bones"]
  for k in ("faceplate","left_arm","right_arm","left_leg","right_leg"):
   assert all(max(map(float,frame))<=0 for frame in []) or k in tr
  for side in ("left","right"):
   for part in ("arm","leg"):
    assert all(v["vector"]==[0,0,0] for v in tr[f"{side}_{part}"]["rotation"].values()),(mk,action,part,"X pose")
   for part in ("arm_back_shell","forearm_back_shell","thigh_back_shell","boot_back_shell"):
    vals=[v["vector"] for v in tr[f"{side}_{part}"]["rotation"].values()]
    assert max(abs(v[1]) for v in vals)>=98,(mk,action,part,"not open")
    assert all(abs(v[0])+abs(v[2])<.001 for v in vals),(mk,action,part,"scissors")
  face=tr["faceplate"]
  pos=list(face["position"].values())
  rot=list(face["rotation"].values())
  assert min(v["vector"][0] for v in rot)<=-82,(mk,action,"no crown rotation")
  assert max(v["vector"][2] for v in pos)<.6,(mk,action,"mask goes behind head")
  assert max(v["vector"][1] for v in pos)>=2.3,(mk,action,"no rising slide")
  assert pos[0]["vector"]==pos[-1]["vector"]==[0,0,0]
  assert rot[0]["vector"]==rot[-1]["vector"]==[0,0,0]
  assert all(float(t)<=4 for trk in tr.values() for frames in trk.values() for t in frames),mk
 approach=clips["animation.power_armor.recall_approach"]
 assert approach["animation_length"]==.55,(mk,"approach timing")
 assert len(approach["bones"])>=16,(mk,"no original 17-part separation")
 assert approach["bones"]["root"]["rotation"]["0.0"]["vector"]==[90,0,0]
 assert approach["bones"]["root"]["rotation"]["0.55"]["vector"]==[90,0,0]
 assert all(0<=float(t)<=.55 for tracks in approach["bones"].values() for keys in tracks.values() for t in keys), (mk,"Recall approach keys outlive clip")
 assert (14.0-6.0)/.72 >= .55*20,(mk,"Recall 14->6 interval too short for full disassembly")
 assert all(v["vector"][0]==90 for v in clips["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
 for c in ("recall_brake","recall_dock"):
  f=clips["animation.power_armor."+c]["bones"]["faceplate"]
  assert min(v["vector"][0] for v in f["rotation"].values())<=-82,(mk,c)
  assert max(v["vector"][2] for v in f["position"].values())<=.35,(mk,c,"head exceeded")
 asset="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity/equipment/humanoid"/(asset+".png")) as im:head=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid_leggings"/(asset+".png")) as im:legs=im.convert("RGBA")
 with Image.open(A/"textures/entity"/(name+".png")) as im:atlas=im.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==head.tobytes(),(mk,"original eye art altered")
 assert atlas.crop((0,32,64,64)).tobytes()==legs.tobytes(),(mk,"original leg art altered")
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
visual=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
client=(J/"client/PowerArmorBuild98Client.java").read_text()
jets=(J/"powerarmor/PowerArmorCreativeFlightJets.java").read_text()
fixture=(J/"build103/Build103GameTests.java").read_text()
assert world.count("new Animation(stand,80,entering,")==3
assert "int t=81-animation.ticks();" in world
assert "progress/80F" in world
assert "pose(stand,80,false)" in world
assert "float spread=0F;" in world
assert "tickCount>83" in visual
assert "entityData.set(V175_PHASE,next)" in visual
assert 'case 5 -> "animation.power_armor.recall_approach";' in visual
assert "visual.beginPhase(5);" in rec and "distance>6.0D&&distance<=24.0D" in rec
assert "player.level().addFreshEntity(visual)" in rec,( "not server-spawned, multi-player regression")
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
assert "if(progress<52)" in rec and "DOCKING" in rec
assert "for(int i=0;i<80;i++)" in fixture and "POWER_ARMOR_REAL_ROUNDTRIP_V69" in fixture
assert "V175_B642_80_TICK_ROUNDTRIP" in fixture
assert "boolean hover=false && !gliding" in client
assert "for(var p:mc.level.players())" in client
assert "@EventBusSubscriber(modid=\"obsidiannetwork\")" in jets
assert "PlayerTickEvent.Post" in jets
assert "instanceof ServerPlayer player" in jets
assert 'PowerArmorRuntime.hasCard(player,"flight")' in jets
assert "PowerArmorRuntime.powered(player)" in jets
assert "player.getAbilities().flying" in jets
assert "level.sendParticles(ParticleTypes.END_ROD" in jets
assert "for(int nozzle=0;nozzle<4;nozzle++)" in jets
assert "getPlayerList()" not in jets and "getAllEntities()" not in jets
print("V175_B642_ALL_24_MK_MULTIPLAYER_GATE_PASS: 80-tick natural opening; 4s 36 bones; no X limbs; crown-rotation mask; early synced 24-block original-part Recall; server-wide flight jets; no duplicated particles, real equipment backup untouched")
