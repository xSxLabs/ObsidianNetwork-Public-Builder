#!/usr/bin/env python3
"""B648: each rear body half folds onto the inside of its arm first.
Then the arm and folded rear half swing TOGETHER around one shoulder
pivot per side. Reverse order to close. No four independent wing joints.
Preserve original Recall choreography, model pixels and real equipment.
"""
import copy,hashlib,json,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(a,b,t):
 if t<=a:return 0.
 if t>=b:return 1.
 t=(t-a)/(b-a)
 return t*t*(3-2*t)
def v(a):return {"vector":[round(float(x),4) for x in a],"easing":"easeInOutSine"}
def track(fn):
 return {str(round(i*.04,4)):v(fn(i/100)) for i in range(101)}
def fold(t):return smooth(.1,.295,t)*(1-smooth(.80,.963,t))
def swing(t):return smooth(.31,.49,t)*(1-smooth(.655,.796,t))
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 model=A/"geckolib/models/entity"/(name+".geo.json")
 anim=A/"geckolib/animations/entity"/(name+".animation.json")
 tex=A/"textures/entity"/(name+".png")
 wear="power_armor" if mk==1 else f"power_armor_mk{mk}"
 textures=[tex,A/"textures/entity/equipment/humanoid"/(wear+".png"),A/"textures/entity/equipment/humanoid_leggings"/(wear+".png")]
 before=[sha(p) for p in textures]
 m=json.loads(model.read_text(encoding="utf8"))
 data=json.loads(anim.read_text(encoding="utf8"))
 bones=m["minecraft:geometry"][0]["bones"]
 idx={b["name"]:b for b in bones}
 assert len(bones)==len(idx)==38,(mk,"B647 base expected")
 for side,sign in (("left",-1),("right",1)):
  arm=idx[side+"_arm"]
  rear=idx["rear_"+side]
  assert arm["parent"]==rear["parent"]=="root",(mk,side)
  name_unit=side+"_entry_unit"
  pivot=[sign*6.3,23,0]
  assert arm["pivot"]==pivot,(mk,"original shoulder")
  bones.append({"name":name_unit,"parent":"root","pivot":pivot})
  arm["parent"]=name_unit
  rear["parent"]=name_unit
  # The existing REAL rear panel folds over the INSIDE of its arm.
  # Pivot at outer torso edge; side-specific positive/negative yaw
  # puts the closed plate alongside x~+/-4.45 and z~0.5.
  rear["pivot"]=[sign*4.4,20,2.7]
  assert rear["cubes"][0]["uv"]["south"]["uv_size"]==[4,12]
 assert len(bones)==40
 # The previously grey mask interior must match the authentic per-MK
 # OUTSIDE eye/face artwork pixel-for-pixel, not just its base color.
 mask=idx["faceplate"]["cubes"][0]
 assert mask["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 mask["uv"]["south"]=copy.deepcopy(mask["uv"]["north"])
 for mode in ("equip","unequip"):
  clip=data["animations"]["animation.power_armor."+mode]
  assert clip["animation_length"]==4.,(mk,mode)
  for side,sign in (("left",-1),("right",1)):
   plate=clip["bones"]["rear_"+side]
   plate["rotation"]=track(lambda t,s=sign:(0,-s*112*fold(t),0))
   clip["bones"][side+"_entry_unit"]={
     "rotation":track(lambda t,s=sign:(0,s*88*swing(t),0))}
   # Arm and forearm stay straight, no X pose and no extra arm
   # rear-shell hinges: both are carried by the one shoulder parent.
   for part in (side+"_arm",side+"_forearm",
                side+"_arm_back_shell",side+"_forearm_back_shell"):
    assert part in clip["bones"],(mk,part)
    clip["bones"][part]["rotation"]=track(lambda t:(0,0,0))
   assert abs(plate["rotation"]["1.2"]["vector"][1])>110
   assert clip["bones"][side+"_entry_unit"]["rotation"]["1.2"]["vector"]==[0,0,0]
   assert abs(clip["bones"][side+"_entry_unit"]["rotation"]["1.96"]["vector"][1])>87
   assert abs(plate["rotation"]["1.96"]["vector"][1])>110
   assert clip["bones"][side+"_entry_unit"]["rotation"]["3.2"]["vector"]==[0,0,0]
   assert abs(plate["rotation"]["3.2"]["vector"][1])>110
  # The old B634 scale guard hides the central interior hardware
  # and side walls while the two compound arm/rear units open.
  internal=clip["bones"]["torso_inner_spine"]["scale"]
  assert internal["0.2433"]["vector"]==internal["3.52"]["vector"]==[0,0,0]
 # New shared parents are identity during Recall, preserving all 17
 # independently recalled pieces and previous phase-continuity fixes.
 for phase in ("recall_flight","recall_approach","recall_brake","recall_dock"):
  clip=data["animations"]["animation.power_armor."+phase]
  assert all(side+"_entry_unit" not in clip["bones"] for side in ("left","right"))
 model.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 anim.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 assert [sha(p) for p in textures]==before,(mk,"PNG drift")
print("B648_24_MK_TWO_COUPLED_ARM_REAR_ASSEMBLIES_AND_EXACT_MASK_INTERIOR_PASS")
