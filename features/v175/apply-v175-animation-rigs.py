#!/usr/bin/env python3
"""v1.7.5: turn ALL 24 original textured Geo models into articulated suit rigs.

Applies after v1.7.4 B598 and v1.7.3 MK3..MK24 resource generation.
No armor stats, inventories, energy mechanics or server ticks changed.
"""
import json,os,math
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def file(name):return A/"geckolib/models/entity"/(name+".geo.json")
def animation(name):return A/"geckolib/animations/entity"/(name+".animation.json")
def save(p,d):p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def bone(name,pivot,origin,size,uv,parent="root"):
 return {"name":name,"parent":parent,"pivot":pivot,"cubes":[{"origin":origin,"size":size,"uv":uv,"inflate":0}]}
def smooth(a,b,t):
 x=max(0.,min(1.,(t-a)/(b-a)))
 return x*x*(3.-2.*x)
def curve(action,t):
 if action=="open":
  return dict(mask=smooth(.02,.23,t),rear=smooth(.13,.59,t),
   chest=smooth(.14,.63,t),arm=smooth(.19,.66,t),leg=smooth(.21,.68,t),root=0)
 if action=="close":
  return dict(mask=1-smooth(.74,1,t),rear=1-smooth(.14,.63,t),
   chest=1-smooth(.11,.60,t),arm=1-smooth(.17,.64,t),leg=1-smooth(.16,.63,t),root=0)
 if action=="recall_flight":
  return dict(mask=0,rear=0,chest=0,arm=0,leg=0,root=-90)
 if action=="recall_brake":
  return dict(mask=smooth(.61,1,t),rear=0,chest=0,arm=0,leg=0,
   root=-90*(1-smooth(.05,.91,t)))
 if action=="recall_dock":
  def env(a,b,c,d):return smooth(a,b,t)*(1-smooth(c,d,t))
  return dict(mask=1-smooth(.82,1,t),rear=env(0,.19,.53,.77),
   chest=env(.04,.23,.54,.77),arm=env(.07,.26,.56,.79),
   leg=env(.08,.29,.58,.80),root=0)
 raise AssertionError(action)
TIMES=[0,.05,.11,.17,.24,.32,.43,.55,.64,.72,.8,.88,.94,1.0]
def keyframes(points):
 return {str(round(t,3)):{ "vector":[round(v,4) for v in vector],
                           "easing":"easeInOutSine"}
         for t,vector in points}
def clip(name):
 bones={}
 def channel(bone,channel,fn):
  bones.setdefault(bone,{})[channel]=keyframes(
   [(t,fn(curve(name,t))) for t in TIMES])
 channel("root","rotation",lambda x:[x["root"],0,0])
 channel("rear_left","rotation",lambda x:[0,-78*x["rear"],0])
 channel("rear_right","rotation",lambda x:[0,78*x["rear"],0])
 channel("rear_left","position",lambda x:[-2.6*x["rear"],0,0])
 channel("rear_right","position",lambda x:[2.6*x["rear"],0,0])
 channel("chest_left","rotation",lambda x:[0,-21*x["chest"],-4*x["chest"]])
 channel("chest_right","rotation",lambda x:[0,21*x["chest"],4*x["chest"]])
 channel("chest_left","position",lambda x:[-1.3*x["chest"],0,0])
 channel("chest_right","position",lambda x:[1.3*x["chest"],0,0])
 channel("faceplate","rotation",lambda x:[-108*x["mask"],0,0])
 channel("faceplate","position",lambda x:[0,2*x["mask"],-1.5*x["mask"]])
 channel("left_arm","rotation",lambda x:[0,0,-13*x["arm"]])
 channel("right_arm","rotation",lambda x:[0,0,13*x["arm"]])
 channel("left_forearm","rotation",lambda x:[-9*x["arm"],0,-3*x["arm"]])
 channel("right_forearm","rotation",lambda x:[-9*x["arm"],0,3*x["arm"]])
 channel("left_leg","rotation",lambda x:[0,0,-11*x["leg"]])
 channel("right_leg","rotation",lambda x:[0,0,11*x["leg"]])
 channel("left_boot","rotation",lambda x:[6*x["leg"],0,0])
 channel("right_boot","rotation",lambda x:[6*x["leg"],0,0])
 return {"animation_length":1.0 if name not in ("recall_flight","recall_brake") else (.35 if name=="recall_brake" else 1.0),
         "loop":"loop" if name=="recall_flight" else "hold_on_last_frame",
         "bones":bones}
names=("open","close","recall_flight","recall_brake","recall_dock")
for tier in range(1,25):
 name="power_armor_visual_mk"+str(tier)
 path=file(name);asset=animation(name)
 assert path.exists() and asset.exists(),("V175_MISSING_TIER",tier)
 model=json.loads(path.read_text(encoding="utf-8"))
 geo=model["minecraft:geometry"][0]
 bones=geo["bones"]
 assert len(bones)==13 and len({b["name"] for b in bones})==13,("V175_MODEL_DRIFT",tier,[b["name"] for b in bones])
 index={b["name"]:b for b in bones}
 required={"root","spine","chest_left","chest_right","helmet","left_arm","right_arm","left_leg","right_leg","visor","reactor","left_shoulder","right_shoulder"}
 assert set(index)==required,("V175_UNEXPECTED_BONES",tier,set(index)^required)
 # Rotate the entire armor around its torso while in horizontal recall flight.
 index["root"]["pivot"]=[0,17,0]
 # Transform the original monolithic torso into front/interior, two sidewalls,
 # and real articulated back shell panels. Use the SAME UV atlas as this tier.
 spine=index["spine"]
 assert len(spine["cubes"])==1 and spine["cubes"][0]["size"]==[8.8,10,6.8],("V175_SPINE_SOURCE_CHANGED",tier)
 spine["cubes"]=[
  {"origin":[-4.4,15,-3.4],"size":[8.8,10,2.4],"uv":[0,0],"inflate":0},
  {"origin":[-4.4,15,-1],"size":[.95,10,4.4],"uv":[0,0],"inflate":0},
  {"origin":[3.45,15,-1],"size":[.95,10,4.4],"uv":[0,0],"inflate":0},
  {"origin":[-3.45,15,2.5],"size":[6.9,1.0,.9],"uv":[0,0],"inflate":0}]
 # Unlike a generic box overlay, these are the actual rear surfaces of the
 # armor. Closed geometry aligns with the old 8.8x10x6.8 shell silhouette.
 bones.append(bone("rear_left",[-.05,20,3.4],[-4.4,15,2.5],[4.35,10,.9],[0,0]))
 bones.append(bone("rear_right",[.05,20,3.4],[.05,15,2.5],[4.35,10,.9],[28,0]))
 # A monolithic helmet front cannot hinge. Keep the original tier texture,
 # reshape the shell into top/side/back surfaces, and put the original face
 # into an independent full-area, upper-hinged faceplate bone.
 helmet=index["helmet"]
 assert len(helmet["cubes"])==1 and helmet["cubes"][0]["size"]==[9,8.5,9],("V175_HELMET_SOURCE_CHANGED",tier)
 helmet["cubes"]=[
  {"origin":[-4.5,25,3.55],"size":[9,8.5,.95],"uv":[0,25],"inflate":0},
  {"origin":[-4.5,25,-3.55],"size":[.95,8.5,7.1],"uv":[0,25],"inflate":0},
  {"origin":[3.55,25,-3.55],"size":[.95,8.5,7.1],"uv":[0,25],"inflate":0},
  {"origin":[-4.5,32.55,-4.5],"size":[9,.95,9],"uv":[0,25],"inflate":0},
  {"origin":[-4.5,25,-4.5],"size":[9,.95,9],"uv":[0,25],"inflate":0}]
 bones.append(bone("faceplate",[0,33.45,-4.45],[-4.45,25.9,-4.5],[8.9,7.55,.95],[0,25],"helmet"))
 index["visor"]["parent"]="faceplate"
 index["visor"]["pivot"]=[0,30,-4.80]
 # Elbows and boots open as real independently pivoting textured geometry.
 for bname in ("left_arm","right_arm"):
  entry=index[bname];cube=entry["cubes"][0]
  assert cube["size"]==[4,11,6.8],("V175_ARM_DRIFT",tier,bname)
  cube["origin"]=[cube["origin"][0],19,cube["origin"][2]]
  cube["size"]=[4,5,6.8]
  o=entry["cubes"][0]["origin"]
  new_name=bname.replace("_arm","_forearm")
  bones.append(bone(new_name,[entry["pivot"][0],19,0],
      [o[0],13,o[2]],[4,6,6.8],cube["uv"],bname))
 for bname in ("left_leg","right_leg"):
  entry=index[bname];cube=entry["cubes"][0]
  assert cube["size"]==[4.9,14.3,7.2],("V175_LEG_DRIFT",tier,bname)
  cube["origin"]=[cube["origin"][0],4,cube["origin"][2]]
  cube["size"]=[4.9,10.3,7.2]
  bones.append(bone(bname.replace("_leg","_boot"),[entry["pivot"][0],4,0],
     [cube["origin"][0],0,cube["origin"][2]],[4.9,4,7.2],cube["uv"],bname))
 assert len(bones)==20 and len({b["name"] for b in bones})==20,("V175_BONE_DUP",tier)
 save(path,model)
 anim=json.loads(asset.read_text(encoding="utf-8"))
 assert set(anim["animations"])=={"animation.power_armor.open","animation.power_armor.close"},("V175_ANIM_DRIFT",tier)
 anim["animations"]={"animation.power_armor."+n:clip(n) for n in names}
 save(asset,anim)
 assert (A/"textures/entity"/(name+".png")).is_file(),("V175_NO_ORIGINAL_TEXTURE",tier)
# Compatibility: the existing renderers resolve original model identifiers and
# original per-tier PNG. The only additions are bones/animation clips.
print("V175_24_TIER_RIGS_PASS: 24 original textured atlases; hinged backs, real faceplates, forearms/boots; 5 clips per tier")
