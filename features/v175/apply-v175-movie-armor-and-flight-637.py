#!/usr/bin/env python3
"""B637: 24 authentic movie-style armor skins, rear-opening limbs, sliding mask,
earlier recall disassembly, neutral exit pose, powered creative-flight jets.
Generated-source overlay ONLY; run after B634. No item ownership or FE changes.
"""
import hashlib,json,os,math
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
TAG="V175_B637_MOVIE_SHELL_JETS"
def hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def uv(u,v,w,h):
 assert u>=0 and v>=0 and w>0 and h>0 and u+w<=128 and v+h<=128
 return {"uv":[u,v],"uv_size":[w,h]}
def ease(a,b,t):
 z=max(0.,min(1.,(t-a)/(b-a)))
 return z*z*(3-2*z)
def openval(t):return ease(.17,.40,t)*(1-ease(.68,.92,t))
def slide(v):
 # 0 = mask flush on face; 1 = passed over the crown to the rear.
 path=((0,(0,0,0)),(.28,(0,7,0)),(.62,(0,9,7.8)),(1,(0,4.5,8.4)))
 for (t,a),(u,b) in zip(path,path[1:]):
  if v<=u:
   q=ease(t,u,v)
   return [round(a[i]+(b[i]-a[i])*q,4) for i in range(3)]
 return list(path[-1][1])
def frame(v):return {"vector":list(v),"easing":"easeInOutSine"}
TIMES=(0,.04,.08,.12,.16,.20,.24,.28,.32,.38,.42,.48,.56,.64,.68,.73,.78,.82,.86,.90,.94,.98,1)
def track(fn):
 return {str(round(t*2.4,3)):frame(fn(t)) for t in TIMES}
def inner(c):
 w,h,d=c["size"]
 return {"north":uv(25,83,w,h),"south":uv(42,83,w,h),
         "west":uv(58,83,d,h),"east":uv(75,83,d,h),
         "up":uv(25,103,w,d),"down":uv(42,103,w,d)}
protected=[J/"powerarmor/PowerArmorRuntime.java",J/"powerarmor/PowerArmorElytraBridge.java",
           J/"powerarmor/ArmorLoadoutData.java",J/"conduit/EnergyConduitTicker.java"]
before={str(p):hash(p) for p in protected}
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 mp=A/"geckolib/models/entity"/(name+".geo.json")
 ap=A/"geckolib/animations/entity"/(name+".animation.json")
 tp=A/"textures/entity"/(name+".png")
 tex_sha=hash(tp)
 m=json.loads(mp.read_text(encoding="utf-8"))
 an=json.loads(ap.read_text(encoding="utf-8"))
 bones=m["minecraft:geometry"][0]["bones"]
 idx={b["name"]:b for b in bones}
 assert len(bones)==len(idx)==28 and idx["spine"].get("cubes")==[],mk
 assert "cubes" not in idx["visor"] and idx["faceplate"]["parent"]=="helmet"
 mask=idx["faceplate"]["cubes"][0]
 assert mask["uv"]["north"]==uv(8,8,8,8) and mask["size"]==[9,8.5,.95],mk
 # Same 8x8 pixels as the real worn helmet, with EXACT 1:1 surface size.
 mask["origin"]=[-4,25.25,-4.55]
 mask["size"]=[8,8,.96]
 for side in ("left","right"):
  for parent,suffix,y,height,u,v in (
      (f"{side}_arm","arm_back_shell",19,6,52,20),
      (f"{side}_forearm","forearm_back_shell",13,6,52,25),
      (f"{side}_leg","thigh_back_shell",4,9,12,52),
      (f"{side}_boot","boot_back_shell",0,4,12,29)):
   original=idx[parent]["cubes"][0]
   x,oy,z=original["origin"]
   w,h,d=original["size"]
   assert abs(oy-y)<.01 and abs(h-height)<.01,(mk,parent,oy,h)
   back=original["uv"]["south"]
   assert back["uv"]==[u,v],(mk,parent,back)
   # Stationary cube shows opaque INSIDE hardware on its back;
   # one moving rear shell has the genuine armor outer UV instead.
   original["uv"]["south"]=uv(42,83,w,h)
   tag=f"{side}_{suffix}"
   assert tag not in idx
   outer=x if side=="left" else x+w
   psize=[w,h,.28]
   faces=inner({"size":psize})
   faces["south"]=back
   panel={"name":tag,"parent":parent,"pivot":[round(outer,3),round(y+h*.55,3),2.7],
          "cubes":[{"origin":[x,y,2.58],"size":psize,"uv":faces,"inflate":0}]}
   bones.append(panel)
   idx[tag]=panel
 # Alpha-safe INSET cores, underneath untouched original leg surface.
 # Decorative eye/leg pixels remain byte-for-byte the real equipment art.
 for parent in ("left_leg","right_leg","left_boot","right_boot"):
  cube=idx[parent]["cubes"][0]
  x,y,z=cube["origin"];w,h,d=cube["size"]
  inset=.22
  sub=[round(w-2*inset,3),round(h-2*inset,3),round(d-2*inset,3)]
  idx[parent]["cubes"].append({
    "origin":[round(x+inset,3),round(y+inset,3),round(z+inset,3)],
    "size":sub,"uv":inner({"size":sub}),"inflate":0})
 assert len(idx)==len(bones)==36,(mk,"missing 8 actual rear limb shells")
 for action in ("equip","unequip"):
  clip=an["animations"]["animation.power_armor."+action]
  assert clip["animation_length"]==2.4,(mk,action)
  bt=clip["bones"]
  bt["faceplate"]["rotation"]=track(lambda t:[0,0,0])
  bt["faceplate"]["position"]=track(lambda t:slide(ease(.02,.33,t)*(1-ease(.67,.98,t))))
  for side,sign in (("left",-1),("right",1)):
   bt[f"{side}_arm"]["rotation"]=track(lambda t,s=sign:[0,0,s*33*openval(t)])
   bt[f"{side}_leg"]["rotation"]=track(lambda t,s=sign:[0,0,s*21*openval(t)])
   for suffix in ("arm_back_shell","forearm_back_shell","thigh_back_shell","boot_back_shell"):
    bt[f"{side}_{suffix}"]={"rotation":track(
      lambda t,s=sign:[0,s*105*openval(t),0])}
  assert bt["faceplate"]["position"]["0.0"]["vector"]==[0,0,0]
  assert bt["faceplate"]["position"]["2.4"]["vector"]==[0,0,0]
 # Recall brake opens helmet by translation; staggered docking closes
 # it by translation; the 17 flying exterior parts remain as authored.
 for action in ("recall_brake","recall_dock"):
  clip=an["animations"]["animation.power_armor."+action]
  assert clip["animation_length"]==(.6 if action=="recall_brake" else 2.0)
  f=clip["bones"]["faceplate"]
  keys=list(f["rotation"])
  assert len(keys)==25
  maximum=max(float(x) for x in keys)
  f["rotation"]={t:frame([0,0,0]) for t in keys}
  f["position"]={t:frame(slide(ease(.10,1,float(t)/maximum)
          if action=="recall_brake" else 1-ease(.74,.99,float(t)/maximum)))
            for t in keys}
 assert all(x["vector"][0]==90 for x in an["animations"][
  "animation.power_armor.recall_flight"]["bones"]["root"]["rotation"].values())
 save(mp,m);save(ap,an)
 assert hash(tp)==tex_sha,(mk,"original MK texture drift")
 worn="power_armor" if mk==1 else f"power_armor_mk{mk}"
 with Image.open(A/"textures/entity/equipment/humanoid"/(worn+".png")) as im:original=im.convert("RGBA")
 with Image.open(tp) as im:atlas=im.convert("RGBA")
 assert atlas.crop((8,8,16,16)).tobytes()==original.crop((8,8,16,16)).tobytes()
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
assert s.count("new Animation(stand,48,entering,")==3
assert "pose(stand,20,false)" in s and "progress/48F" in s
s=s.replace("pose(stand,20,false)","pose(stand,48,false)")
assert "V175_B633_EXIT_BACK_TO_PLAYER" in s and "stand.setInvisible(false)" in s
world.write_text(s,encoding="utf-8")
rec=J/"powerarmor/PowerArmorRecall.java"
s=rec.read_text(encoding="utf-8")
old="distance<=2.5D || DOCKING.containsKey(player.getUUID())"
assert s.count(old)==1,("B637 recall range changed",s.count(old))
s=s.replace(old,"distance<=6.0D || DOCKING.containsKey(player.getUUID())")
for fragment in ("progress<12?3:4","if(progress<52)","PowerArmorSuitWorld.recallEquip(stand,player)",
                 "MAX_FLIGHT&&!DOCKING.containsKey(player.getUUID())"):
 assert fragment in s,fragment
rec.write_text(s,encoding="utf-8")
# Expand existing per-player, four-nozzle particles to the real 'flight'
# upgrade (creative-style hover). No additional event hook or FE cost.
client=J/"client/PowerArmorBuild98Client.java"
s=client.read_text(encoding="utf-8")
old="""   // Only a complete MK1-MK24 suit with the Network Elytra upgrade and FE.
   if(!p.isFallFlying() || p.onGround())continue;
   var chest=PowerArmorElytraBridge.chest(p);
   if(chest.isEmpty()||EnergyTool.energy(chest)<125L)continue;
   boolean boost=p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
   if(!boost && p.tickCount%2!=0)continue;"""
new="""   // V175_B637_CREATIVE_JETS: glide OR card-enabled powered creative flight.
   if(p.onGround())continue;
   boolean gliding=p.isFallFlying();
   boolean hover=!gliding && p.getAbilities().flying;
   if(!gliding&&!hover)continue;
   boolean creativeArmor=false;
   if(hover){
    int tier=PowerArmorRuntime.tier(p.getItemBySlot(EquipmentSlot.HEAD),0);
    boolean complete=tier>=1&&tier<=24, hasFlightCard=false;
    for(int slot=0;slot<PowerArmorRuntime.SLOTS.length;slot++){
     var item=p.getItemBySlot(PowerArmorRuntime.SLOTS[slot]);
     if(PowerArmorRuntime.tier(item,slot)!=tier||EnergyTool.energy(item)<20L)
      complete=false;
     String cards=item.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
     if(cards!=null)for(String card:cards.split(","))
      if(card.equals("flight"))hasFlightCard=true;
    }
    creativeArmor=complete&&hasFlightCard;
   }
   var chest=gliding?PowerArmorElytraBridge.chest(p):
     p.getItemBySlot(EquipmentSlot.CHEST);
   if((!gliding&&!creativeArmor)||chest.isEmpty()
      ||EnergyTool.energy(chest)<(gliding?125L:20L))continue;
   boolean boost=gliding && p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
   if(!boost && p.tickCount%2!=0)continue;"""
assert s.count(old)==1,("B637 jets gate",s.count(old))
s=s.replace(old,new)
old="   Vec3 backwards=look.scale(-0.3);"
assert s.count(old)==1
s=s.replace(old,"   Vec3 backwards=creativeArmor?new Vec3(0D,-.24D,0D):look.scale(-.3);")
old="""     mc.level.addParticle(ParticleTypes.END_ROD,px,py,pz,
       -look.x*(boost?0.18:0.06),-look.y*(boost?0.18:0.06)-0.02,
       -look.z*(boost?0.18:0.06));"""
new="""     mc.level.addParticle(ParticleTypes.END_ROD,px,py,pz,
       creativeArmor?0D:-look.x*(boost?0.18:0.06),
       creativeArmor?-.14D:-look.y*(boost?0.18:0.06)-0.02,
       creativeArmor?0D:-look.z*(boost?0.18:0.06));"""
assert s.count(old)==1,("B637 particle vector",s.count(old))
s=s.replace(old,new)
assert s.count("for(var p:mc.level.players())")==1
assert s.count("for(int limb=0;limb<4;limb++)")==1
assert "ParticleTypes.CLOUD" in s and "BUILD124_SHARED_ELYTRA_PARTICLES" in s
client.write_text(s,encoding="utf-8")
assert {str(p):hash(p) for p in protected}==before,"B637 gameplay ownership/FE drift"
print(TAG+": 24 original eye skins, 8 rear limb panels, opaque inset legs, slide-over-head mask, early Recall, neutral finish, same 4 jet emitters for flight or Elytra")
