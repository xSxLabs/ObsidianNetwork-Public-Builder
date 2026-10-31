#!/usr/bin/env python3
"""B626 final precompile 24-tier staged assembly & original-asset preservation."""
import json, os, math
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
BASE="animation.power_armor."
part_names=("spine","reactor","chest_left","chest_right","rear_left",
 "rear_right","left_leg","right_leg","left_boot","right_boot","left_arm",
 "right_arm","left_forearm","right_forearm","left_shoulder","right_shoulder","helmet")
assert len(part_names)==17

def value(anim,bone,kind,key):
 return anim["bones"][bone][kind][key]["vector"]

for tier in range(1,25):
 stem=f"power_armor_visual_mk{tier}"
 md=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
 ad=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())
 bs=md["minecraft:geometry"][0]["bones"]
 index={b["name"]:b for b in bs}
 assert len(index)==len(bs)==28,(tier,"lost model component")
 assert index["faceplate"]["parent"]=="helmet" and index["visor"]["parent"]=="faceplate"
 assert index["rear_left"]["pivot"]==[-4.4,20,3.4] and index["rear_right"]["pivot"]==[4.4,20,3.4]
 for part,parent in (("left_forearm","left_arm"),("right_forearm","right_arm"),
                     ("left_boot","left_leg"),("right_boot","right_leg"),
                     ("left_shoulder","left_arm"),("right_shoulder","right_arm"),
                     ("reactor","spine")):
  assert index[part]["parent"]==parent,(tier,part,"original normal-enter hierarchy changed")
 # Original 24 individual texture atlases remain the source. No third-party file.
 tex=A/"textures/entity"/(stem+".png")
 assert tex.stat().st_size>600 and md["minecraft:geometry"][0]["description"]["texture_width"]==128
 an=ad["animations"]
 assert len(an)==7
 for action in ("equip","unequip"):
  normal=an[BASE+action]
  assert normal["animation_length"]==1.0,(tier,action,"normal must stay B625 20-tick")
  assert "rear_left" in normal["bones"] and "faceplate" in normal["bones"]
 for action,length in (("recall_brake",.6),("recall_dock",2.0)):
  c=an[BASE+action]
  assert abs(c["animation_length"]-length)<1e-9,(tier,action,"duration")
  for part in part_names:
   assert part in c["bones"] and "rotation" in c["bones"][part] and "position" in c["bones"][part],(tier,action,part)
   for kind in ("rotation","position"):
    k=c["bones"][part][kind]
    assert len(k)==25 and "0.0" in k and "1.0" in k
    assert all(x["easing"]=="easeInOutSine" and len(x["vector"])==3
       and all(math.isfinite(y) for y in x["vector"]) for x in k.values())
   if action=="recall_dock":
    assert value(c,part,"position","1.0")==[0,0,0],(tier,part,"not docked")
  m=c["bones"]["faceplate"]["rotation"]
  if action=="recall_brake":
   assert m["0.0"]["vector"]==[0,0,0] and m["1.0"]["vector"][0]<=-115
  else:
   assert m["0.0"]["vector"][0]<=-115 and m["1.0"]["vector"]==[0,0,0]
 # Movie-style but independent from other packs: 17 parts, staggered timing.
 montage=an[BASE+"recall_dock"]
 torso=value(montage,"spine","position","0.5")
 helmet=value(montage,"helmet","position","0.5")
 assert all(abs(v)<.001 for v in torso) and abs(helmet[1])>10,(tier,"no staggered arrival")
 arm=value(montage,"left_arm","position","0.5")
 boot=value(montage,"left_boot","position","0.5")
 # Each component must still travel at least 25% of its authored lateral path
 # halfway through docking; boots have a shorter path than the arms.
 assert abs(arm[0])>=20*.25 and abs(boot[0])>=17*.25,(tier,"arm or boot not flying")
 # Recall brake must end with exact same spread as dock begins; no teleport pop.
 br=an[BASE+"recall_brake"]; dock=an[BASE+"recall_dock"]
 for part in part_names:
  for kind in ("rotation","position"):
   assert value(br,part,kind,"1.0")==value(dock,part,kind,"0.0"),(tier,part,kind,"phase jump")
 assert value(br,"root","rotation","0.0")==[90,0,0]
 assert value(br,"root","rotation","1.0")==[0,0,0]
 flight=an[BASE+"recall_flight"]
 assert all(frame["vector"][0]==90 for frame in flight["bones"]["root"]["rotation"].values())
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
vis=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
assert world.count("new Animation(stand,20,entering,")==3
assert "int t=21-animation.ticks();" in world
assert "xsxlabs_v175_temporarily_hidden_world_suit" in world
assert "v175RestoreWorldSuitOnLoad" in world
assert "stand.entityTags()" in world and "stand.getTags()" not in world
assert "tickCount>23" in vis
assert "PowerArmorRecall.isVisualActive(getUUID())" in vis
assert "progress<12?3:4" in rec and "if(progress<52)" in rec
assert "MAX_FLIGHT&&!DOCKING.containsKey(player.getUUID())" in rec
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
assert "visual.beginPhase(2)" in rec
assert "DOCKING.remove(player.getUUID())" in rec
print("V175_B628_RECALL_ONLY_PIECE_ASSEMBLY_PASS: 24 original tier rigs; 17 part recall montage tracks; normal enter/exit 20-tick split-back unchanged; 52-tick safe dock")
