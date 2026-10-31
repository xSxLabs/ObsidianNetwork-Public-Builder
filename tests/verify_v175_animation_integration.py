#!/usr/bin/env python3
"""v1.7.5 no-build integration gate for ALL 24 textured rigs + recall stages.
Use after both apply-v175-*.py scripts, before requesting first full CI.
"""
import os,json,math
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
all_clips={"animation.power_armor."+n for n in
 ("open","close","equip","unequip","recall_flight","recall_brake","recall_dock")}
for tier in range(1,25):
 prefix=f"power_armor_visual_mk{tier}"
 model=json.loads((A/"geckolib/models/entity"/(prefix+".geo.json")).read_text(encoding="utf-8"))
 anim=json.loads((A/"geckolib/animations/entity"/(prefix+".animation.json")).read_text(encoding="utf-8"))
 bones=model["minecraft:geometry"][0]["bones"]
 names={b["name"] for b in bones}
 assert len(bones)==len(names)==20,("V175_RIG_TIER_MISMATCH",tier,names)
 for name in ("rear_left","rear_right","faceplate","left_forearm","right_forearm","left_boot","right_boot"):
  assert name in names and next(b for b in bones if b["name"]==name).get("cubes"),("V175_MISSING_ACTUAL_MESH",tier,name)
 assert all(c.get("uv") is not None and not c.get("texture") for b in bones for c in b.get("cubes",[]))
 assert model["minecraft:geometry"][0]["description"]["texture_width"]==128
 assert (A/"textures/entity"/(prefix+".png")).is_file(),("V175_MISSING_TIER_TEXTURE",tier)
 assert set(anim["animations"])==all_clips,("V175_UNBOUND_ACTION",tier)
 assert next(b for b in bones if b["name"]=="faceplate")["parent"]=="helmet"
 assert next(b for b in bones if b["name"]=="visor")["parent"]=="faceplate"
 assert next(b for b in bones if b["name"]=="root")["pivot"]==[0,17,0]
 for clipname,clip in anim["animations"].items():
  assert clip["animation_length"]>0
  assert set(clip["bones"]).issubset(names),("V175_UNKNOWN_ANIM_BONE",tier,clipname)
  for b,channels in clip["bones"].items():
   for cname,curve in channels.items():
    assert cname in ("rotation","position"),(tier,b,cname)
    for t,frame in curve.items():
     vec=frame["vector"]
     assert len(vec)==3 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in vec)
     assert frame["easing"]=="easeInOutSine"
  pitch=clip["bones"]["root"]["rotation"]
  if clipname.endswith("recall_flight"):
   assert all(abs(v["vector"][0]+90)<.0001 for v in pitch.values()),("V175_FLIGHT_NOT_HORIZONTAL",tier)
  if clipname.endswith("recall_brake"):
   assert pitch["0"]["vector"][0]==-90 and pitch["1.0"]["vector"][0]==0,("V175_NOT_UPRIGHT_AT_DOCK",tier)
  if clipname.endswith("recall_dock"):
   assert clip["bones"]["rear_left"]["rotation"]["1.0"]["vector"]==[0,0,0]
   assert clip["bones"]["rear_right"]["rotation"]["1.0"]["vector"]==[0,0,0]
   assert clip["bones"]["faceplate"]["rotation"]["1.0"]["vector"]==[0,0,0]
  if clipname.endswith(("equip","unequip")):
   # Both normal transitions must show the mechanical opening and finish
   # fully closed, without the player seeing a permanently opened mannequin.
   rear=clip["bones"]["rear_left"]["rotation"]
   mask=clip["bones"]["faceplate"]["rotation"]
   assert rear["0"]["vector"]==[0,0,0] and rear["1.0"]["vector"]==[0,0,0], (tier,clipname,"rear terminal")
   assert mask["0"]["vector"]==[0,0,0] and mask["1.0"]["vector"]==[0,0,0], (tier,clipname,"mask terminal")
   assert abs(rear["0.55"]["vector"][1])>65, (tier,clipname,"rear fails to split")
   assert abs(mask["0.32"]["vector"][0])>100, (tier,clipname,"mask fails to lift")
  if clipname.endswith("close"):
   assert clip["bones"]["faceplate"]["rotation"]["1.0"]["vector"]==[0,0,0]
      # Last closed frame must have an intact faceplate.
vis=(J/"powerarmor/PowerArmorVisualEntity.java").read_text(encoding="utf-8")
rec=(J/"powerarmor/PowerArmorRecall.java").read_text(encoding="utf-8")
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
assert all(s in vis for s in ("V175_PHASE","beginPhase(int next)","thenLoop(","recall_flight","recall_brake","recall_dock"))
assert '"animation.power_armor.equip":"animation.power_armor.unequip"' in vis, "V175_EQUIP_UNEQUIP_ACTIONS_NOT_BOUND"
assert "V175_RECALL_VISUAL_LIFETIME" in vis
assert ('PowerArmorRecall.isVisualActive(getUUID())' in vis or
  "tickCount>23&&entityData.get(V175_PHASE)==0" in vis), "V175_RECALL_GHOST_DISCARDED_PREMATURELY"
assert all(s in rec for s in ("V175_RECALL_DOCK","V175_RECOVERY_SAFE_DOCK","DOCKING.remove(player.getUUID())",
 "visual.beginPhase(2)","visual.beginPhase(progress<8?3:4)","PowerArmorSuitWorld.recallEquip(stand,player)",
 "PowerArmorRecallTickets.ticket","V173_RECALL_GHOST_FLIGHT174"))
# The real 4-stack transfer, persistent source, anti-dup, backup and legacy
# vanilla ArmorStand fallback must NEVER be stripped for a visual improvement.
assert "ArmorStand stand=new ArmorStand(level,pos.getX()" in world
assert "stand.setInvisible(true);" not in world
assert "PowerArmorRuntime.full(player)" in world
assert "stand.discard();" in world
assert "for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)" in world
print("V175_PREBUILD_GATE_GREEN: 24 unique textured rigs; 168 valid clips; cosmetic recall states; source suit preserved")
