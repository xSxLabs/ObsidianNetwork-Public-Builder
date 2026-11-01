#!/usr/bin/env python3
"""B650 rear X shoulder hinge; staged exit with visible player and
unchanged original server-authoritative item transaction, no invisibility.
Only existing MK1--MK24 geo models / animations are changed.
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
def vec(v):return {"vector":[round(float(x),4) for x in v],"easing":"easeInOutSine"}
def frames(d,fn,n=100):
 return {str(round(d*i/n,4)):vec(fn(i/n)) for i in range(n+1)}
def sample(f,t):
 points=sorted((float(k),v["vector"]) for k,v in f.items())
 if t<=points[0][0]:return points[0][1]
 if t>=points[-1][0]:return points[-1][1]
 for (a,p),(b,q) in zip(points,points[1:]):
  if a<=t<=b:
   u=(t-a)/(b-a);u=(1-math.cos(math.pi*u))*.5
   return [p[i]+(q[i]-p[i])*u for i in range(3)]
 raise AssertionError(t)
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 mp=A/"geckolib/models/entity"/(stem+".geo.json")
 ap=A/"geckolib/animations/entity"/(stem+".animation.json")
 tp=A/"textures/entity"/(stem+".png")
 old=sha(tp)
 m=json.loads(mp.read_text(encoding="utf-8"))
 ani=json.loads(ap.read_text(encoding="utf-8"))
 bs={b["name"]:b for b in m["minecraft:geometry"][0]["bones"]}
 assert len(bs)==40,mk
 for side,sign in (("left",-1),("right",1)):
  unit=bs[side+"_entry_unit"]
  assert unit["pivot"]==[sign*4.4,23,3.4],(mk,side)
  assert bs[side+"_arm"]["parent"]==bs["rear_"+side]["parent"]==unit["name"]
  unit["pivot"]=[sign*6.3,23,3.4]
 for action in ("equip","unequip"):
  clip=ani["animations"]["animation.power_armor."+action]
  assert clip["animation_length"]==4.,mk
  for side in ("left","right"):
   oldrot=clip["bones"][side+"_entry_unit"]["rotation"]
   assert max(abs(x["vector"][1]) for x in oldrot.values())>=95,(mk,side,"expected lateral B649 source")
   # Hinged at BACK of shoulder; X pitch moves arms toward REAR (+Z).
   # Absolutely no yaw and no fan-out/scissor of whole arms.
   clip["bones"][side+"_entry_unit"]["rotation"]=frames(
       4.,lambda t:(-84*ease(.31,.53,t)*(1-ease(.70,.87,t)),0.,0.))
   assert clip["bones"][side+"_entry_unit"]["rotation"]["2.12"]["vector"]==[-84,0,0]
 source=ani["animations"]["animation.power_armor.unequip"]
 # The cosmetic shell opened until tick 42. After atomic item transfer,
 # a new visual starts at SAME pose and only CLOSES; no second opening.
 close={"animation_length":4.,"loop":"hold_on_last_frame","bones":{}}
 for bone,channels in source["bones"].items():
  close["bones"][bone]={}
  for kind,oldtrack in channels.items():
   if kind not in ("position","rotation","scale"):continue
   close["bones"][bone][kind]=frames(4.,
      lambda t,fr=oldtrack:sample(fr,2.12+(4.-2.12)*min(1.,t*2.)),80)
   assert close["bones"][bone][kind]["0.0"]["vector"]==vec(sample(oldtrack,2.12))["vector"],(mk,bone,kind)
   assert max(abs(a-b) for a,b in zip(close["bones"][bone][kind]["4.0"]["vector"],sample(oldtrack,4.)))<.0002
 ani["animations"]["animation.power_armor.exit_close"]=close
 mp.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 ap.write_text(json.dumps(ani,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 assert sha(tp)==old,mk
def replace(s,a,b,n=1):
 assert s.count(a)==n,("B650 anchor",a,s.count(a))
 return s.replace(a,b,n)
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
s=replace(s," public static int exit(ServerPlayer player){",''' public static int exit(ServerPlayer player){
  // Still wearing suit and fully visible while the synced shell opens.
  // Original safe equipment transfer occurs ONLY on gated tick 42.
  if(!PowerArmorExitSequence650.committing(player))
   return PowerArmorExitSequence650.request(player);''')
s=replace(s,"  PowerArmorExitReveal649.begin(player); // after successful transfer, show player only when hatch opens",
   "  // B650: no invisible player; original safe exit items moved after hatch opened.")
s=replace(s,"  visual.begin(entering);",'''  visual.begin(entering);
  // Complete the single exit opening: do NOT replay unequip after transfer.
  if(!entering&&PowerArmorExitSequence650.committing(player))
   visual.beginPhase(6);''')
world.write_text(s,encoding="utf-8")
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
s=replace(s,"next>5","next>6")
s=replace(s,'case 5 -> "animation.power_armor.recall_approach";',
'''case 5 -> "animation.power_armor.recall_approach";
    case 6 -> "animation.power_armor.exit_close";''')
visual.write_text(s,encoding="utf-8")
helper=J/"powerarmor/PowerArmorExitSequence650.java"
assert not helper.exists(),"B650 duplicate"
kinds="\n".join(f"   case {mk} -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{mk}.get();" for mk in range(1,25))
helper.write_text('''package dev.obsidiannetwork.powerarmor;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** B650: a purely cosmetic synced suit opens BEFORE the real transfer.
 * The visible player's four original stacks remain exclusively on player
 * until the ordinary, existing rollback-safe PowerArmorSuitWorld.exit().
 * No player invisibility, duplicating item entities, or client-local effects.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorExitSequence650 {
 private record Pending(PowerArmorVisualEntity preview,Vec3 start,int deadline){}
 private static final Map<UUID,Pending> PENDING=new HashMap<>();
 private static final Set<UUID> COMMITTING=new HashSet<>();
 private PowerArmorExitSequence650(){}
 public static boolean committing(ServerPlayer p){return COMMITTING.contains(p.getUUID());}
 private static EntityType<PowerArmorVisualEntity> kind(int tier){return switch(tier){
'''+kinds+'''
   default -> null;
  };}
 public static int request(ServerPlayer p){
  UUID id=p.getUUID();
  if(PENDING.containsKey(id)||COMMITTING.contains(id)||!PowerArmorRuntime.full(p))return 0;
  int tier=PowerArmorRuntime.tier(p.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  EntityType<PowerArmorVisualEntity> type=kind(tier);
  if(type==null)return 0;
  // Preview is EMPTY: it owns NO equipment, only the synced armor model.
  BlockPos target=p.blockPosition().relative(p.getDirection());
  PowerArmorVisualEntity visual=new PowerArmorVisualEntity(type,p.level());
  visual.setPos(target.getX()+.5D,target.getY(),target.getZ()+.5D);
  float yaw=p.getDirection().toYRot();
  visual.setYRot(yaw);visual.setYBodyRot(yaw);visual.setYHeadRot(yaw);
  visual.addTag("xsxlabs_b650_exit_preview");
  visual.begin(false);
  if(!p.level().addFreshEntity(visual))return 0;
  PENDING.put(id,new Pending(visual,p.position(),p.tickCount+42));
  p.sendSystemMessage(net.minecraft.network.chat.Component.literal("Power Armor opening for exit..."));
  return 1;
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post e){
  if(!(e.getEntity() instanceof ServerPlayer p))return;
  UUID id=p.getUUID();Pending pending=PENDING.get(id);
  if(pending==null)return;
  if(!p.isAlive()||!PowerArmorRuntime.full(p)||pending.preview().isRemoved()
     ||p.position().distanceToSqr(pending.start())>1.0D){cancel(p);return;}
  if(p.tickCount<pending.deadline())return;
  PENDING.remove(id);
  pending.preview().discard();
  COMMITTING.add(id);
  try{
   int result=PowerArmorSuitWorld.exit(p); // unchanged atomic rollback-safe transfer
   if(result==0)p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
      "Power Armor exit cancelled: suit remained equipped."));
  }finally{COMMITTING.remove(id);}
 }
 private static void cancel(ServerPlayer p){
  Pending x=PENDING.remove(p.getUUID());
  if(x!=null&&!x.preview().isRemoved())x.preview().discard();
 }
 @SubscribeEvent public static void logout(PlayerEvent.PlayerLoggedOutEvent e){
  if(e.getEntity() instanceof ServerPlayer p){cancel(p);COMMITTING.remove(p.getUUID());}
 }
 @SubscribeEvent public static void clone(PlayerEvent.Clone e){
  UUID id=e.getOriginal().getUUID();Pending x=PENDING.remove(id);
  if(x!=null&&!x.preview().isRemoved())x.preview().discard();
  COMMITTING.remove(id);
 }
}
''',encoding="utf-8")
print("V175_B650_PASS: all 24 rear-only X shoulder hinges, 42-tick visible exit prep, original transfer then continuous closure, no invisibility")
