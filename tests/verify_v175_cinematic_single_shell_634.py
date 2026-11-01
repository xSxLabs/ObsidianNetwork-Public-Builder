#!/usr/bin/env python3
"""B634 post-apply regression for all 24 original armor skins and timings."""
import json,os,hashlib
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 md=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
 ad=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())
 idx={b["name"]:b for b in md["minecraft:geometry"][0]["bones"]}
 an=ad["animations"]
 assert len(idx)==28
 assert idx["spine"].get("cubes")==[],(mk,"duplicate front panel")
 assert idx["chest_left"]["cubes"][0]["uv"]["north"]=={"uv":[20,20],"uv_size":[4,12]}
 assert idx["chest_right"]["cubes"][0]["uv"]["north"]=={"uv":[24,20],"uv_size":[4,12]}
 assert idx["rear_left"]["cubes"][0]["uv"]["south"]=={"uv":[32,20],"uv_size":[4,12]}
 assert idx["rear_right"]["cubes"][0]["uv"]["south"]=={"uv":[36,20],"uv_size":[4,12]}
 assert idx["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 assert "cubes" not in idx["visor"]
 for bn in ("rear_left_hinge","rear_right_hinge","rear_left_gasket","rear_right_gasket",
            "faceplate_left_rail","faceplate_right_rail","faceplate_forehead_lock"):
  assert "cubes" not in idx[bn],(mk,bn,"detached box")
 assert idx["rear_left"]["pivot"]==[-4.4,20,3.4]
 assert idx["rear_right"]["pivot"]==[4.4,20,3.4]
 assert idx["faceplate"]["parent"]=="helmet"
 for act in ("equip","unequip"):
  c=an["animation.power_armor."+act]
  assert c["animation_length"]==2.4,(mk,act,"time mismatch")
  b=c["bones"]
  assert b["rear_left"]["rotation"]["0.0"]["vector"]==[0,0,0]
  assert b["rear_left"]["rotation"]["2.4"]["vector"]==[0,0,0]
  assert b["faceplate"]["rotation"]["2.4"]["vector"]==[0,0,0]
  assert max(abs(f["vector"][1]) for f in b["rear_left"]["rotation"].values())>=105
  assert max(abs(f["vector"][1]) for f in b["rear_right"]["rotation"].values())>=105
  assert max(abs(f["vector"][0]) for f in b["faceplate"]["rotation"].values())>=108
  assert all(x["vector"]==[0,0,0] for x in b["chest_left"]["position"].values())
  assert all(x["vector"]==[0,0,0] for x in b["chest_right"]["rotation"].values())
  scales=b["torso_inner_spine"]["scale"]
  assert scales["0.0"]["vector"]==scales["2.4"]["vector"]==[1,1,1]
  assert sum(1 for x in scales.values() if x["vector"]==[0,0,0])==2
  for tr in b.values():
   for channel,frames in tr.items():
    assert max(float(t) for t in frames)<=2.4,(mk,act,channel)
 assert an["animation.power_armor.recall_dock"]["animation_length"]==2.0
 assert an["animation.power_armor.recall_brake"]["animation_length"]==.6
 assert all(v["vector"][0]==90 for v in an["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
 n="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity/equipment/humanoid"/(n+".png")) as im: top=im.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid_leggings"/(n+".png")) as im: leg=im.convert("RGBA")
 with Image.open(A/"textures/entity"/(stem+".png")) as im: atlas=im.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),(mk,"body pixels drift")
 assert atlas.crop((0,32,64,64)).tobytes()==leg.tobytes(),(mk,"leg pixels drift")
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
visual=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
guard=(J/"client/PowerArmorTransitionRenderGuard.java").read_text()
assert world.count("new Animation(stand,48,entering,")==3
assert "int t=49-animation.ticks();" in world
assert "progress/48F" in world
assert "V175_B633_EXIT_BACK_TO_PLAYER" in world
assert "BlockPos p=player.blockPosition().relative(player.getDirection());" in world
assert "PowerArmorRuntime.SLOTS" in world and "stand.discard();" in world
assert "tickCount>51" in visual and "PowerArmorRecall.isVisualActive(getUUID())" in visual
assert '\"animation.power_armor.equip\":\"animation.power_armor.unequip\"' in visual
assert "RenderLivingEvent.Pre" in guard and "RegisterRenderStateModifiersEvent" in guard
assert "PowerArmorSuitWorld.full(stand)" in guard and "stand.isInvisible()" in guard
assert "getRenderDataOrDefault(HIDE_OWNER,false)" in guard and "event.setCanceled(true)" in guard
assert "V175_HEAD_FIRST_JETS" in (J/"powerarmor/PowerArmorRecall.java").read_text()
print("V175_B634_FULL_GATE_PASS: 24 exact armor textures, zero duplicate chest shell, synchronized 48-tick normal sequences, original recall and owned suit intact")
