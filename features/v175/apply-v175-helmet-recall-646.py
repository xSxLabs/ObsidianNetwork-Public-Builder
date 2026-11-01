#!/usr/bin/env python3
"""B646: actual original-textured split helmet, crown-stowed faceplate and
phase-continuous recall. Runs AFTER B645; no textures, items, FE, tick or
inventory ownership code is altered. Only MK1--MK24 GeckoLib model/clip JSON.
"""
import copy,hashlib,json,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ease(a,b,t):
 if t<=a:return 0.
 if t>=b:return 1.
 x=(t-a)/(b-a)
 return x*x*(3-2*x)
def vec(v):return {"vector":[round(float(x),4) for x in v],"easing":"easeInOutSine"}
def frames(d,fn,n=80):
 return {str(round(d*i/n,4)):vec(fn(i/n)) for i in range(n+1)}
def first(t):return next(iter(t.values()))["vector"]
def last(t):return list(t.values())[-1]["vector"]
def mask(p):
 # The face moves in front of the face, lifts, rotates, retracts and
 # settles flat ON the crown, not far behind the head.
 stops=((0.,(0,0,0),0),(.3,(0,2.5,-.85),-16),
        (.66,(0,2.9,-.65),-68),(.84,(0,1.65,-.15),-86),
        (1.,(0,.7,.12),-90))
 for (a,v,r),(b,w,s) in zip(stops,stops[1:]):
  if p<=b:
   f=ease(a,b,p)
   return tuple(v[i]+(w[i]-v[i])*f for i in range(3)),r+(s-r)*f
 return stops[-1][1],stops[-1][2]
def face(clip,d,progress):
 t=clip["bones"].setdefault("faceplate",{})
 t["position"]=frames(d,lambda x:mask(progress(x))[0])
 t["rotation"]=frames(d,lambda x:(mask(progress(x))[1],0,0))
def helm(clip,d,openat):
 for name,sign in (("left",-1),("right",1)):
  clip["bones"]["helmet_"+name]={"rotation":frames(d,lambda t,s=sign:(0,s*104*openat(t),0))}
def half(original,side):
 b=copy.deepcopy(original)
 x,y,z=original["origin"];w,h,d=original["size"]
 assert x==-4.5 and w==9,(x,w)
 b["origin"]=[-4.5 if side=="left" else 0,y,z]
 b["size"]=[4.5,h,d]
 for direction,o in original["uv"].items():
  f=copy.deepcopy(o)
  if direction in ("north","south","up","down"):
   f["uv"][0]=round(f["uv"][0]+(f["uv_size"][0]/2 if side=="right" else 0),4)
   f["uv_size"][0]=round(f["uv_size"][0]/2,4)
  elif (direction=="west" and side=="right") or (direction=="east" and side=="left"):
   f={"uv":[58 if side=="right" else 75,83],"uv_size":[d,h]}
  b["uv"][direction]=f
 return b
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 mp=A/"geckolib/models/entity"/(stem+".geo.json")
 ap=A/"geckolib/animations/entity"/(stem+".animation.json")
 tp=A/"textures/entity"/(stem+".png")
 name="power_armor" if mk==1 else f"power_armor_mk{mk}"
 texts=[tp,A/"textures/entity/equipment/humanoid"/(name+".png"),
       A/"textures/entity/equipment/humanoid_leggings"/(name+".png")]
 hashes=[sha(p) for p in texts]
 m=json.loads(mp.read_text(encoding="utf-8"))
 a=json.loads(ap.read_text(encoding="utf-8"))
 bones=m["minecraft:geometry"][0]["bones"]
 byname={b["name"]:b for b in bones}
 assert len(bones)==len(byname)==36,(mk,"source model drift")
 head=byname["helmet"]
 assert len(head["cubes"])==5 and head["parent"]=="root",mk
 assert byname["faceplate"]["parent"]=="helmet",mk
 original=copy.deepcopy(head["cubes"])
 assert original[0]["uv"]["south"]=={"uv":[24,8],"uv_size":[8,8]},mk
 assert original[3]["uv"]["up"]=={"uv":[8,0],"uv_size":[8,8]},mk
 assert original[4]["uv"]["down"]=={"uv":[16,0],"uv_size":[8,8]},mk
 # Physical split of all rear, top and bottom surfaces. Keep exact worn UV
 # and side walls, preserve the one true faceplate uncut.
 head.pop("cubes")
 for side,wall in (("left",1),("right",2)):
  pieces=[half(original[i],side) for i in (0,3,4)]
  pieces.insert(1,copy.deepcopy(original[wall]))
  bones.append({"name":"helmet_"+side,"parent":"helmet",
                "pivot":[-4.5 if side=="left" else 4.5,29,3.55],
                "cubes":pieces})
 assert len(bones)==38,mk
 clip=a["animations"]
 get=lambda n:clip["animation.power_armor."+n]
 for mode in ("equip","unequip"):
  c=get(mode)
  assert c["animation_length"]==4.0,(mk,mode)
  if mode=="equip":
   openness=lambda t:ease(.015,.27,t)*(1-ease(.82,.99,t))
   halves=lambda t:ease(.14,.34,t)*(1-ease(.68,.83,t))
  else:
   openness=lambda t:ease(.02,.23,t)*(1-ease(.87,.99,t))
   halves=lambda t:ease(.14,.33,t)*(1-ease(.71,.87,t))
  face(c,4.,openness)
  helm(c,4.,halves)
  assert first(c["bones"]["faceplate"]["rotation"])==[0,0,0]
  assert last(c["bones"]["faceplate"]["rotation"])==[0,0,0]
 approach,brake,dock=map(get,("recall_approach","recall_brake","recall_dock"))
 assert (approach["animation_length"],brake["animation_length"],dock["animation_length"])==(.55,.6,2.),mk
 # B645 bug: each part's .55-second approach finishes DISASSEMBLED,
 # but .6-second brake started every part at ZERO and re-disassembled it.
 # Freeze each at its actual approach end while the root alone levels out.
 for bone,tracks in approach["bones"].items():
  if bone=="root":continue
  assert bone in brake["bones"] and bone in dock["bones"],(mk,bone)
  for kind,values in tracks.items():
   value=last(values)
   assert first(dock["bones"][bone][kind])==value,(mk,bone,kind,"dock mismatch")
   brake["bones"][bone][kind]={"0.0":vec(value),"0.6":vec(value)}
 # B645 root's last frame was at 1.0 seconds OUTSIDE its .6s clip.
 brake["bones"]["root"]={"rotation":frames(.6,lambda t:(90*(1-ease(0,1,t)),0,0),24)}
 face(brake,.6,lambda t:ease(0,1,t))
 helm(brake,.6,lambda t:ease(0,1,t))
 # Body assembles once, during the FIRST 1.35s of the two-second dock.
 # Helmet halves close afterwards; faceplate seals absolutely last.
 for bone,tracks in dock["bones"].items():
  if bone in ("root","faceplate"):continue
  for kind,old in list(tracks.items()):
   if kind not in ("rotation","position","scale"):continue
   end=max(float(k) for k in old)
   assert .99<=end<=1.01,(mk,bone,kind,end)
   tracks[kind]={str(round(float(t)*1.35/end,4)):v for t,v in old.items()}
 dock["bones"]["root"]={"rotation":{"0.0":vec((0,0,0)),"2.0":vec((0,0,0))}}
 helm(dock,2.,lambda t:1-ease(.68,.84,t))
 face(dock,2.,lambda t:1-ease(.84,1.,t))
 assert last(dock["bones"]["faceplate"]["rotation"])==[0,0,0],mk
 mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 ap.write_text(json.dumps(a,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 assert [sha(p) for p in texts]==hashes,(mk,"real armor texture changed")
print("V175_B646_PASS: 24 real split helmets, crown mask, one Recall break and one dock; texture/runtime untouched")
