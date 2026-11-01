#!/usr/bin/env python3
"""B652: immobile arms, ONLY their rear armor plates swing outward.
Staged EXIT opens a cosmetic shell around still-visible, still-wearing player.
64 server ticks before existing safe item transfer; then only closes.
Recall, gameplay, MK1-MK24 original textures and stored loadouts unchanged.
"""
import hashlib,json,math,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ease(a,b,t):
 if t<=a:return 0.
 if t>=b:return 1.
 x=(t-a)/(b-a);return x*x*(3-2*x)
def v(x):return {"vector":[round(float(q),4) for q in x],"easing":"easeInOutSine"}
def key(d,fun,n=100):return {str(round(d*i/n,4)):v(fun(i/n)) for i in range(n+1)}
def sample(fr,t):
 pts=sorted((float(k),z["vector"]) for k,z in fr.items())
 if t<=pts[0][0]:return pts[0][1]
 if t>=pts[-1][0]:return pts[-1][1]
 for (a,x),(b,y) in zip(pts,pts[1:]):
  if a<=t<=b:
   p=(t-a)/(b-a);p=p*p*(3-2*p)
   return [x[i]+(y[i]-x[i])*p for i in range(3)]
 raise AssertionError(t)
def once(s,a,b):
 assert s.count(a)==1,("B652 source anchor",a,s.count(a))
 return s.replace(a,b,1)
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 mp=A/"geckolib/models/entity"/(stem+".geo.json")
 ap=A/"geckolib/animations/entity"/(stem+".animation.json")
 worn="power_armor" if mk==1 else f"power_armor_mk{mk}"
 pngs=[A/"textures/entity"/(stem+".png"),
       A/"textures/entity/equipment/humanoid"/(worn+".png"),
       A/"textures/entity/equipment/humanoid_leggings"/(worn+".png")]
 hashes=[sha(p) for p in pngs]
 m=json.loads(mp.read_text(encoding="utf-8"))
 a=json.loads(ap.read_text(encoding="utf-8"))
 bones={b["name"]:b for b in m["minecraft:geometry"][0]["bones"]}
 assert len(bones)==40,mk
 recall={s:json.dumps(a["animations"]["animation.power_armor."+s],sort_keys=True)
        for s in ("recall_flight","recall_approach","recall_brake","recall_dock")}
 for side,sign in (("left",-1),("right",1)):
  unit=side+"_entry_unit"
  assert bones[unit]["pivot"]==[sign*6.3,23,3.4]
  assert bones[side+"_arm"]["parent"]==unit
  for part in ("arm_back_shell","forearm_back_shell"):
   name=side+"_"+part
   b=bones[name]
   assert b["parent"]==(side+"_arm" if part=="arm_back_shell" else side+"_forearm")
   assert len(b["cubes"])==1
   assert b["pivot"][0]==(-9.45 if side=="left" else 9.45)
 for mode in ("equip","unequip"):
  clip=a["animations"]["animation.power_armor."+mode]
  assert clip["animation_length"]==4.0
  for side,sgn in (("left",-1),("right",1)):
   c=clip["bones"]
   unit=side+"_entry_unit"
   assert max(abs(k["vector"][0]) for k in c[unit]["rotation"].values())>80,(mk,side,mode)
   # No arm motion at all: 0 deg on compound, upper arm and forearm.
   c[unit]["rotation"]=key(4.,lambda t:(0,0,0))
   for part in ("arm","forearm"):
    c[side+"_"+part]["rotation"]=key(4.,lambda t:(0,0,0))
   # Exterior rear panels are real original-UV parts with one Y hinge
   # each; each inner edge moves BACK (+Z), not sideways or forwards.
   for part in ("arm_back_shell","forearm_back_shell"):
    name=side+"_"+part;ang=(-105. if side=="left" else 105.)
    c[name]["rotation"]=key(4.,lambda t,q=ang:(0,q*ease(.34,.56,t)*(1-ease(.80,.975,t)),0))
    c[name]["scale"]=key(4.,lambda t:(1,1,1))
    assert c[name]["rotation"]["2.4"]["vector"][1]==ang,(mk,name)
   assert c[unit]["rotation"]["2.4"]["vector"]==[0,0,0]
 # A separate opening phase holds all rear plates open BEFORE any exit
 # transfer. A separate closing phase starts at the EXACT same pose.
 src=a["animations"]["animation.power_armor.unequip"]
 opened={"animation_length":3.,"loop":"hold_on_last_frame","bones":{}}
 closing={"animation_length":2.,"loop":"hold_on_last_frame","bones":{}}
 for bone,channels in src["bones"].items():
  opened["bones"][bone]={};closing["bones"][bone]={}
  for ch,fr in channels.items():
   assert ch in ("rotation","position","scale"),(mk,bone,ch)
   opened["bones"][bone][ch]=key(3.,lambda t,f=fr:sample(f,min(2.4,t*3.)),80)
   closing["bones"][bone][ch]=key(2.,lambda t,f=fr:sample(f,2.4+1.6*min(1.,t)),80)
   assert opened["bones"][bone][ch]["3.0"]["vector"]==closing["bones"][bone][ch]["0.0"]["vector"],(mk,bone,ch,"opening seam")
   assert closing["bones"][bone][ch]["2.0"]["vector"]==v(sample(fr,4.))["vector"],(mk,bone,ch,"closing")
 a["animations"]["animation.power_armor.exit_open"]=opened
 a["animations"]["animation.power_armor.exit_close"]=closing
 for phase,old in recall.items():
  assert json.dumps(a["animations"]["animation.power_armor."+phase],sort_keys=True)==old,(mk,phase,"Recall drift")
 mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 ap.write_text(json.dumps(a,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 assert [sha(p) for p in pngs]==hashes,(mk,"original armor atlas changed")
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
s=once(s,"next>6","next>7")
s=once(s,'case 6 -> "animation.power_armor.exit_close";',
'''case 6 -> "animation.power_armor.exit_close";
    case 7 -> "animation.power_armor.exit_open";''')
visual.write_text(s,encoding="utf-8")
helper=J/"powerarmor/PowerArmorExitSequence650.java"
s=helper.read_text(encoding="utf-8")
s=once(s,"BlockPos target=p.blockPosition().relative(p.getDirection());",
'''// Open around the player WHO IS STILL WEARING THE SUIT, not the future stand.''')
s=once(s,"visual.setPos(target.getX()+.5D,target.getY(),target.getZ()+.5D);",
       "visual.setPos(p.getX(),p.getY(),p.getZ());")
s=once(s,"visual.begin(false);",
'''visual.begin(false);
  visual.beginPhase(7); // open fully, then hold until safe transfer''')
s=once(s,"p.tickCount+42","p.tickCount+64")
assert "setInvisible(" not in s
helper.write_text(s,encoding="utf-8")
# Unused B649 invisibility event subscriber is not needed: remove it to
# eliminate any possibility of the old hide-player logic reactivating.
old=J/"powerarmor/PowerArmorExitReveal649.java"
if old.exists():
 assert "public final class PowerArmorExitReveal649" in old.read_text(encoding="utf-8")
 old.unlink()
# B651 GameTest must now check all 63 PRE-transfer ticks and transfer at 64.
fixture=J/"build103/Build103GameTests.java"
s=fixture.read_text(encoding="utf-8")
assert "completeExitOpening650" in s
s=once(s,"for(int step=0;step<42;step++){","for(int step=0;step<64;step++){")
s=once(s,"if(step<41){","if(step<63){")
s=once(s,"// B651: exactly 42 exit preview ticks, BEFORE the atomic transfer.",
       "// B652: all 63 opening ticks retain armor; 64th tick transfers after full opening.")
fixture.write_text(s,encoding="utf-8")
print("V175_B652_PASS: all 24 stationary arms, real hinged rear plates, player-visible 64-tick opening, transfer after opening")
