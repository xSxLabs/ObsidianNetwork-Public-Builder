#!/usr/bin/env python3
"""B650 actual generated models and state-machine safety gate."""
import json,math,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 model=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
 a=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())["animations"]
 bones={x["name"]:x for x in model["minecraft:geometry"][0]["bones"]}
 assert len(bones)==40,mk
 for side,sign in (("left",-1),("right",1)):
  unit=side+"_entry_unit"
  assert bones[unit]["pivot"]==[sign*6.3,23,3.4],(mk,"rear shoulder hinge")
  assert bones[side+"_arm"]["parent"]==bones["rear_"+side]["parent"]==unit
  for part in ("arm","forearm","leg","boot"):
   assert len(bones[side+"_"+part]["cubes"])==5,(mk,side,part,"not hollow")
  for mode in ("equip","unequip"):
   clip=a["animation.power_armor."+mode]
   p=clip["bones"][unit]["rotation"]
   assert all(abs(f["vector"][1])+abs(f["vector"][2])<.00001 for f in p.values()),(mk,"still rotates sideways")
   assert p["2.12"]["vector"]==[-84,0,0],mk
   assert p["0.0"]["vector"]==p["4.0"]["vector"]==[0,0,0],mk
   # X rotation of arm moves FRONT (-Z) toward BACK (+Z), without X displacement
   y,z=19-23,-2.5-3.4;angle=math.radians(-84)
   assert 3.4+y*math.sin(angle)+z*math.cos(angle)>6
 close=a["animation.power_armor.exit_close"]
 src=a["animation.power_armor.unequip"]
 assert close["animation_length"]==4 and len(close["bones"])==len(src["bones"])
 for bone,channels in close["bones"].items():
  for kind,fr in channels.items():
   assert set(("0.0","2.0","4.0")).issubset(fr)
   assert fr["2.0"]["vector"]==fr["4.0"]["vector"],(mk,bone,kind)
   if "2.12" in src["bones"][bone][kind]:
    assert fr["0.0"]["vector"]==src["bones"][bone][kind]["2.12"]["vector"],(mk,bone,kind,"restart")
 assert close["bones"]["left_entry_unit"]["rotation"]["0.0"]["vector"]==[-84,0,0]
 assert close["bones"]["right_entry_unit"]["rotation"]["0.0"]["vector"]==[-84,0,0]
 wear="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity"/(stem+".png")) as x:atlas=x.convert("RGBA")
 with Image.open(A/"textures/entity/equipment/humanoid"/(wear+".png")) as x:top=x.convert("RGBA")
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),mk
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
helper=(J/"powerarmor/PowerArmorExitSequence650.java").read_text()
vis=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
assert "if(!PowerArmorExitSequence650.committing(player))" in world
assert "return PowerArmorExitSequence650.request(player);" in world
assert "PowerArmorExitReveal649.begin(player);" not in world
assert "visual.beginPhase(6);" in world
assert "next>6" in vis and 'case 6 -> "animation.power_armor.exit_close";' in vis
assert "p.tickCount+42" in helper and "if(p.tickCount<pending.deadline())return;" in helper
assert "PowerArmorSuitWorld.exit(p)" in helper and "COMMITTING.add(id)" in helper
assert "COMMITTING.remove(id)" in helper and "visual.begin(false);" in helper
assert "p.setInvisible(" not in helper and "player.setInvisible(" not in world
assert "PlayerLoggedOutEvent" in helper and "PlayerEvent.Clone" in helper
assert "p.position().distanceToSqr(pending.start())>1.0D" in helper
assert all(f"case {mk} ->" in helper for mk in range(1,25))
print("B650_24_MK_REAR_X_HINGES_VISIBLE_DELAYED_EXIT_AND_CONTINUOUS_CLOSE_PASS")
