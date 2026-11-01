#!/usr/bin/env python3
"""B642: slow smooth normal Power Armor, real crown-slide mask, no X pose,
early Recall approach split, and server-broadcast creative thrusters.

Runs AFTER B636 fixture overlay (so 48 -> 80 ticks also updates the GameTest).
All 24 original MK skins & 36-bone geometry stay unchanged.
Never touch equipment transfers, FE drain, movement, v1.7.4 or other machines.
"""
import os,json,hashlib,math
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
TAG="V175_B642_SLOW_SYNCED_MOVIE_ANIMATIONS"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def easing(t,a,b):
 x=max(0.0,min(1.0,(t-a)/(b-a)))
 return x*x*(3-2*x)
def pose(v):return {"vector":[round(float(x),4) for x in v],"easing":"easeInOutSine"}
def move(t):
 """Interpolated slide that stops ON the crown, never behind the head.

 1) Mask climbs the face; 2) while rising it tilts backward;
 3) it settles horizontal on the crown. Reverse while closing.
 The faceplate pivot is the helmet forehead; rotating -87 degrees
 extends 8px backward ON top of the 8px helmet, not behind it.
 """
 s=easing(t,.045,.39)*(1-easing(t,.62,.96))
 stops=(
  (0.00,(0.0,0.0,0.0),0.0),
  (0.25,(0.0,2.2,0.0),-17.0),
  (0.55,(0.0,2.6,0.2),-54.0),
  (0.85,(0.0,1.2,0.3),-83.0),
  (1.00,(0.0,0.45,0.2),-87.0)
 )
 for (u,p,r),(v,q,w) in zip(stops,stops[1:]):
  if s<=v:
   z=easing(s,u,v)
   pos=[p[i]*(1-z)+q[i]*z for i in range(3)]
   return pos,r*(1-z)+w*z
 return list(stops[-1][1]),stops[-1][2]
protected=[J/"powerarmor/PowerArmorRuntime.java",J/"powerarmor/PowerArmorElytraBridge.java",
           J/"powerarmor/ArmorLoadoutData.java",J/"conduit/EnergyConduitTicker.java"]
before={str(p):sha(p) for p in protected}
for mk in range(1,25):
 name=f"power_armor_visual_mk{mk}"
 model=A/"geckolib/models/entity"/(name+".geo.json")
 ani=A/"geckolib/animations/entity"/(name+".animation.json")
 texture=A/"textures/entity"/(name+".png")
 mo=load(model);clips=load(ani)
 model_hash=sha(model);tex_hash=sha(texture)
 bones={b["name"]:b for b in mo["minecraft:geometry"][0]["bones"]}
 assert len(bones)==36 and "cubes" not in bones["visor"],(mk,"B637 36 original exterior bones")
 assert bones["faceplate"]["cubes"][0]["size"]==[8,8,.96]
 assert bones["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 data=clips["animations"]
 assert "animation.power_armor.recall_approach" not in data
 old_flight=json.dumps(data["animation.power_armor.recall_flight"],sort_keys=True)
 for act in ("equip","unequip"):
  clip=data["animation.power_armor."+act]
  assert clip["animation_length"]==2.4,(mk,act,"B637 duration")
  tr=clip["bones"]
  # Preserve curves/keyframe shape, stretch to 80 server ticks = 4s.
  for bone,tracks in tr.items():
   for channel,frames in list(tracks.items()):
    assert channel in ("rotation","position","scale")
    times=list(frames)
    assert abs(max(float(t) for t in times)-2.4)<1e-3,(mk,act,bone,channel)
    tracks[channel]={str(round(float(t)*5.0/3.0,4)):v
                    for t,v in frames.items()}
  clip["animation_length"]=4.0
  # Whole arm and whole leg must NEVER fan out as an X. Back shells
  # already rotate horizontally about outer rear hinges; animate ONLY
  # those independent exterior pieces. Boots/cuffs remain attached.
  for side in ("left","right"):
   for limb in ("arm","leg"):
    k=tr[f"{side}_{limb}"]["rotation"]
    for f in k.values():f["vector"]=[0.0,0.0,0.0]
   # Back panels keep their sideways Y opening; do not rotate their
   # parent in Z, which made the limbs scissor/cross each other.
   for suffix in ("arm_back_shell","forearm_back_shell",
                  "thigh_back_shell","boot_back_shell"):
    k=tr[f"{side}_{suffix}"]["rotation"]
    assert max(abs(x["vector"][1]) for x in k.values())>95,(mk,suffix)
    assert all(abs(x["vector"][0])+abs(x["vector"][2])<.001 for x in k.values())
  # The mask moves up AND rotates while rising. Top-of-head end pose
  # stays close to the crown and never translates to z=8.4 behind it.
  tr["faceplate"]["position"]={}
  tr["faceplate"]["rotation"]={}
  for i in range(0,81,2):
   t=i/80.0
   pos,angle=move(t)
   key=str(round(t*4.0,4))
   tr["faceplate"]["position"][key]=pose(pos)
   tr["faceplate"]["rotation"][key]=pose([angle,0.0,0.0])
  assert tr["faceplate"]["position"]["0.0"]["vector"]==[0,0,0]
  assert tr["faceplate"]["position"]["4.0"]["vector"]==[0,0,0]
  assert tr["faceplate"]["rotation"]["4.0"]["vector"]==[0,0,0]
  assert min(f["vector"][0] for f in tr["faceplate"]["rotation"].values())<-82
  assert max(f["vector"][2] for f in tr["faceplate"]["position"].values())<.6
 # Intermediate approach clip: the 17 ORIGINAL recall pieces unfasten
 # on the horizontal flight while still 14 blocks from the wearer.
 # The actual four items remain at the source until the existing
 # 52-tick docking transaction is fully complete.
 brake=data["animation.power_armor.recall_brake"]
 flight=data["animation.power_armor.recall_flight"]
 assert brake["animation_length"]==.6
 original_brake=json.loads(json.dumps(brake))
 approach={"animation_length":1.0,"loop":"hold_on_last_frame","bones":{
   "root":{"rotation":{"0.0":pose([90,0,0]),"1.0":pose([90,0,0])}}
 }}
 for bone,channels in brake["bones"].items():
  if bone in ("root","faceplate"):continue
  result={}
  for ch,fr in channels.items():
   if ch not in ("rotation","position","scale"):continue
   keys=list(fr)
   total=max(float(k) for k in keys)
   assert total>0,(mk,bone,ch)
   result[ch]={str(round(float(k)/total,4)):val for k,val in fr.items()}
  if result:approach["bones"][bone]=result
 assert len(approach["bones"])>=16,(mk,"staggered original piece movement lost")
 data["animation.power_armor.recall_approach"]=approach
 # Recall brake and dock use the same top-of-head sliding/rolling
 # faceplate. Old B637's brake keys extended beyond its .6s length.
 for action in ("recall_brake","recall_dock"):
  c=data["animation.power_armor."+action]
  length=c["animation_length"]
  mask=c["bones"]["faceplate"]
  mask["position"]={}
  mask["rotation"]={}
  for i in range(25):
   t=i/24
   fraction=easing(t,.10,.95) if action=="recall_brake" else 1-easing(t,.68,.96)
   # move() itself is a full excursion; use the climb waypoints directly
   # so a brake only opens once and the dock only closes once.
   stops=((0,(0,0,0),0),(.25,(0,2.2,0),-17),
          (.55,(0,2.6,.2),-54),(.85,(0,1.2,.3),-83),
          (1,(0,.45,.2),-87))
   for (a,p,r),(b,q,w) in zip(stops,stops[1:]):
    if fraction<=b:
     z=easing(fraction,a,b)
     xyz=[p[j]*(1-z)+q[j]*z for j in range(3)]
     degrees=r*(1-z)+w*z
     break
   else:xyz=list(stops[-1][1]);degrees=-87
   key=str(round(t*length,4))
   mask["position"][key]=pose(xyz)
   mask["rotation"][key]=pose([degrees,0,0])
 assert json.dumps(data["animation.power_armor.recall_flight"],sort_keys=True)==old_flight
 save(ani,clips)
 assert sha(model)==model_hash and sha(texture)==tex_hash,(mk,"texture or original model changed")

# Server-authoritative normal opening and closing: 80 ticks, with synced
# GeckoLib entity living until tick 83 (3-tick grace).
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
for old,new,count in (
 ("new Animation(stand,48,entering,","new Animation(stand,80,entering,",3),
 ("int t=49-animation.ticks();","int t=81-animation.ticks();",1),
 ("progress/48F","progress/80F",1),
 ("pose(stand,48,false)","pose(stand,80,false)",1)):
 assert s.count(old)==count,("B642_80_TICK_RUNTIME",old,s.count(old))
 s=s.replace(old,new)
# Neutral fallback world-stand pose while the owner mesh is visible:
# no spread in Z and no scissoring legs, including under failure fallback.
assert "float spread=55F*open;" in s
s=s.replace("float spread=55F*open;","float spread=0F; // B642 neutral arms; exterior rear shells animate in Geo model")
s=s.replace("new net.minecraft.core.Rotations(0F,0F,-12F*open)",
            "new net.minecraft.core.Rotations(0F,0F,0F)")
s=s.replace("new net.minecraft.core.Rotations(0F,0F,12F*open)",
            "new net.minecraft.core.Rotations(0F,0F,0F)")
assert "V175_B633_EXIT_BACK_TO_PLAYER" in s
world.write_text(s,encoding="utf-8")
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
assert s.count("tickCount>51")==1
s=s.replace("tickCount>51","tickCount>83")
# A synced entity/data phase makes the new early disassembly visible to
# all tracking players; never spawn client-local-only visual copies.
assert "private static final EntityDataAccessor<Integer> V175_PHASE" in s
assert "entityData.set(V175_PHASE,next)" in s
assert "next>4" in s and 'case 3 -> "animation.power_armor.recall_brake"' in s
s=s.replace("next>4","next>5")
s=s.replace('case 3 -> "animation.power_armor.recall_brake";',
            'case 3 -> "animation.power_armor.recall_brake";\n    case 5 -> "animation.power_armor.recall_approach";')
assert 'case 5 -> "animation.power_armor.recall_approach";' in s
visual.write_text(s,encoding="utf-8")
rec=J/"powerarmor/PowerArmorRecall.java"
s=rec.read_text(encoding="utf-8")
anchor="   double distance=delta.length();"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''
   // B642_EARLY_RECALL_PIECES: start fully synchronized part separation
   // 14 blocks away, not just when the wearer is almost touched (6 blocks).
   // Real ItemStacks remain source-owned until the existing safe commit.
   if(distance>6.0D&&distance<=14.0D&&!DOCKING.containsKey(player.getUUID()))
    visual.beginPhase(5);''')
assert "if(progress<52)" in s and "PowerArmorSuitWorld.recallEquip(stand,player)" in s
assert "distance<=6.0D || DOCKING.containsKey(player.getUUID())" in s
assert "player.level().addFreshEntity(visual)" in s
rec.write_text(s,encoding="utf-8")
# The B636 game test must simulate ALL 80 ticks before asserting that
# the world stand's persistent items and visibility have been restored.
fixture=J/"build103/Build103GameTests.java"
s=fixture.read_text(encoding="utf-8")
assert "V175_B636_48_TICK_ROUNDTRIP" in s and s.count("for(int i=0;i<48;i++)")==1
s=s.replace("V175_B636_48_TICK_ROUNDTRIP","V175_B642_80_TICK_ROUNDTRIP")
s=s.replace("for(int i=0;i<48;i++)","for(int i=0;i<80;i++)")
fixture.write_text(s,encoding="utf-8")

# Multiplayer creative flight: vanilla does not guarantee that remote
# clients know another player's flying Ability flag. Don't guess it
# locally. Server validates full powered suit and FLIGHT card and
# sends the 4 END_ROD nozzles to all nearby/tracking players.
client=J/"client/PowerArmorBuild98Client.java"
s=client.read_text(encoding="utf-8")
anchor="boolean hover=!gliding && p.getAbilities().flying;"
assert s.count(anchor)==1
s=s.replace(anchor,"boolean hover=false && !gliding && p.getAbilities().flying; // B642 creative jets sent by server")
assert s.count("for(var p:mc.level.players())")==1
assert s.count("for(int limb=0;limb<4;limb++)")==1
client.write_text(s,encoding="utf-8")
jets=J/"powerarmor/PowerArmorCreativeFlightJets.java"
assert not jets.exists(),("B642 duplicate server jet emitter")
jets.write_text(r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** B642: one server-authoritative set of four downward creative-flight
 * nozzles. ServerLevel.sendParticles broadcasts to nearby observers:
 * no local player-only effect, no custom network traffic, no FE/physics
 * mutation or extra world scan; at most 4 particles every two ticks.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorCreativeFlightJets {
 private PowerArmorCreativeFlightJets(){}
 @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player))return;
  if(player.tickCount%2!=0 || player.onGround() || !player.getAbilities().flying)return;
  if(!PowerArmorRuntime.powered(player)||!PowerArmorRuntime.hasCard(player,"flight"))return;
  ServerLevel level=(ServerLevel)player.level();
  Vec3 look=player.getLookAngle();
  Vec3 right=new Vec3(-look.z,0D,look.x);
  if(right.lengthSqr()<1.0e-5D)right=new Vec3(1D,0D,0D);
  right=right.normalize();
  for(int nozzle=0;nozzle<4;nozzle++){
   double x=player.getX()+right.x*(nozzle%2==0?-.36D:.36D);
   double z=player.getZ()+right.z*(nozzle%2==0?-.36D:.36D);
   double y=nozzle<2?player.getEyeY()-.60D:player.getY()+.20D;
   level.sendParticles(ParticleTypes.END_ROD,x,y,z,1,.012D,.012D,.012D,.04D);
  }
 }
}
''',encoding="utf-8")
assert {str(p):sha(p) for p in protected}==before,"B642 altered suit/FE/inventory code"
print(TAG+": 24 MK skins unchanged; 80-tick 4s normal, no X legs/arms, sliding+rotating mask on crown, 14-block early synced Recall fragments, 80-tick real roundtrip, server-to-all creative jets")
