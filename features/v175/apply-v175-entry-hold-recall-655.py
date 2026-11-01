#!/usr/bin/env python3
"""B655: Recall helmet REAR stays shut (mask track untouched).
Right-click real placed suit = OPEN & HOLD, walk into hollow suit = CLOSE then
original safe equipment transfer; exit player invisible only until hatch open.
All MK1-24 real original armor PNG, FE, recall flight & multiplayer preserved.
"""
import copy,hashlib,json,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 n=s.count(a);assert n==1,("B655_DRIFT",a[:130],n)
 return s.replace(a,b,1)
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 p=A/"geckolib/animations/entity"/(stem+".animation.json")
 model=A/"geckolib/models/entity"/(stem+".geo.json")
 png=A/"textures/entity"/(stem+".png")
 hashes=(sha(model),sha(png))
 doc=json.loads(p.read_text(encoding="utf8"))
 clips=doc["animations"]
 oldRecall={k:json.dumps(clips["animation.power_armor."+k],sort_keys=True)
       for k in ("recall_flight","recall_approach")}
 original_face={k:json.dumps(clips["animation.power_armor."+k]["bones"]["faceplate"],sort_keys=True)
       for k in ("recall_brake","recall_dock")}
 original_normal={k:json.dumps(clips["animation.power_armor."+k],sort_keys=True)
       for k in ("equip","unequip")}
 for phase in ("recall_brake","recall_dock"):
  c=clips["animation.power_armor."+phase]
  for side in ("helmet_left","helmet_right"):
   a=c["bones"][side]["rotation"]
   assert max(abs(f["vector"][1]) for f in a.values())>90,(mk,phase,side,"expected open source")
   for f in a.values():f["vector"]=[0.,0.,0.]
  assert json.dumps(c["bones"]["faceplate"],sort_keys=True)==original_face[phase],(mk,phase,"mask modified")
  assert c["bones"]["faceplate"]["rotation"],(mk,phase)
 # Normal equipment still opens rear helmet; the Recall-only fix must not touch it.
 for mode in ("equip","unequip"):
  assert json.dumps(clips["animation.power_armor."+mode],sort_keys=True)==original_normal[mode],mk
  assert max(abs(f["vector"][1]) for f in clips["animation.power_armor."+mode]["bones"]["helmet_left"]["rotation"].values())>100,mk
 # Physically one continuous open animation followed by a distinct close
 # animation that starts from exactly the same original hull pose.
 clips["animation.power_armor.entry_open"]=copy.deepcopy(clips["animation.power_armor.exit_open"])
 clips["animation.power_armor.entry_close"]=copy.deepcopy(clips["animation.power_armor.exit_close"])
 for name in clips["animation.power_armor.entry_open"]["bones"]:
  for channel,fr in clips["animation.power_armor.entry_open"]["bones"][name].items():
   nxt=clips["animation.power_armor.entry_close"]["bones"][name][channel]
   assert list(fr.values())[-1]["vector"]==next(iter(nxt.values()))["vector"],(mk,name,channel,"close starts from open")
 for phase,original in oldRecall.items():
  assert json.dumps(clips["animation.power_armor."+phase],sort_keys=True)==original,mk
 p.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 assert (sha(model),sha(png))==hashes,mk
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf8")
s=once(s,"next>7","next>9")
s=once(s,'case 7 -> "animation.power_armor.exit_open";',
'''case 7 -> "animation.power_armor.exit_open";
    case 8 -> "animation.power_armor.entry_open";
    case 9 -> "animation.power_armor.entry_close";''')
s=once(s,'tickCount>83','tickCount>83&&!entityTags().contains("xsxlabs_b655_entry_hold_visual")')
# The same exact-owner client movement lock used for exiting applies while
# entering is CLOSING, not while waiting for the user to walk in.
s=once(s,'entityData.get(V175_PHASE)==7 &&',
       '(entityData.get(V175_PHASE)==7||entityData.get(V175_PHASE)==9) &&')
visual.write_text(s,encoding="utf8")
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf8")
s=once(s,''' private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){
  if(!(actor instanceof ServerPlayer player))return;''',
''' private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){
  if(!(actor instanceof ServerPlayer player))return;
  // One right click OPENS; it never equips anything. Step physically inside
  // to initiate the actual existing safe 80-tick closing+transfer transaction.
  if(!PowerArmorEntrySequence655.committing(player)){
   PowerArmorEntrySequence655.request(stand,player);
   return;
  }''')
s=once(s,'''  if(!entering&&PowerArmorExitSequence650.committing(player))
   visual.beginPhase(6);''',
'''  if(!entering&&PowerArmorExitSequence650.committing(player))
   visual.beginPhase(6);
  if(entering&&PowerArmorEntrySequence655.committing(player)){
   visual.beginPhase(9);  // close from the HOLD-OPEN geometry, never reopen
   visual.setExitOwner654(player.getUUID());
  }''')
s=once(s,"e->mine(e,player)&&e.isInvisible()",
       'e->mine(e,player)&&e.isInvisible()&&!PowerArmorEntrySequence655.waiting(e)')
world.write_text(s,encoding="utf8")
# EXIT: user-selected concealment only while opening. Store previous invis
# state, restore exactly at real safe transfer, on invalidation and on logout.
exitFile=J/"powerarmor/PowerArmorExitSequence650.java"
s=exitFile.read_text(encoding="utf8")
s=once(s," private static final Set<UUID> COMMITTING=new HashSet<>();",
''' private static final Set<UUID> COMMITTING=new HashSet<>();
 private static final Map<UUID,Boolean> BEFORE_HIDE_655=new HashMap<>();
 private static void showAfterExit(ServerPlayer p){
  Boolean was=BEFORE_HIDE_655.remove(p.getUUID());
  if(was!=null)p.setInvisible(was);
 }''')
s=once(s,"PENDING.put(id,new Pending(visual,p.position(),p.tickCount+64));",
'''PENDING.put(id,new Pending(visual,p.position(),p.tickCount+64));
  BEFORE_HIDE_655.put(id,p.isInvisible());
  p.setInvisible(true); // invisible ONLY until hatch has fully opened''')
s=once(s,"  }finally{COMMITTING.remove(id);}",
'''  }finally{
   COMMITTING.remove(id);
   showAfterExit(p);  // player now outside and visible, never mid-opening
  }''')
s=once(s,'''  if(x!=null&&!x.preview().isRemoved())x.preview().discard();
 }''',
'''  if(x!=null&&!x.preview().isRemoved())x.preview().discard();
  showAfterExit(p); // death, interruption, logout: never remain hidden
 }''')
s=once(s,'''  COMMITTING.remove(id);
 }
}''',
'''  COMMITTING.remove(id);
  BEFORE_HIDE_655.remove(id);
 }
}''')
assert "p.tickCount+64" in s and "PowerArmorSuitWorld.exit(p)" in s
exitFile.write_text(s,encoding="utf8")
entry=J/"powerarmor/PowerArmorEntrySequence655.java"
assert not entry.exists(),"B655 entry class duplicate"
entry.write_text('''package dev.obsidiannetwork.powerarmor;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** User-driven, server-authoritative rear entry. Visuals never own item stacks.
 * RIGHT CLICK: hatch opens and remains open indefinitely.
 * PHYSICAL STEP-IN: hatch closes, original rollback-safe 80-tick equip executes.
 * Never auto-equip just because the 3-second opening clip finished.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorEntrySequence655 {
 private record Open(ArmorStand suit,PowerArmorVisualEntity visual,boolean marker){}
 private record Closing(ArmorStand suit,Vec3 start,int expiry){}
 private static final Map<UUID,Open> OPEN=new HashMap<>();
 private static final Map<UUID,Closing> CLOSING=new HashMap<>();
 private static final Set<UUID> COMMITTING=new HashSet<>();
 private static final String OPEN_TAG="xsxlabs_b655_entry_open_owner";
 private static final String HIDE_TAG="xsxlabs_v175_temporarily_hidden_world_suit";
 private PowerArmorEntrySequence655(){}
 public static boolean committing(ServerPlayer p){return COMMITTING.contains(p.getUUID());}
 public static boolean waiting(ArmorStand stand){return stand.entityTags().contains(OPEN_TAG);}
 private static boolean owned(ArmorStand stand,ServerPlayer p){
  return stand.entityTags().contains("xsxlabs_power_armor_suit_v17")
    &&stand.entityTags().contains("xsxlabs_power_armor_owner_"+p.getUUID());
 }
 public static void request(ArmorStand stand,ServerPlayer p){
  UUID id=p.getUUID();
  if(OPEN.containsKey(id)||CLOSING.containsKey(id)||!owned(stand,p)||
      stand.isRemoved()||!PowerArmorSuitWorld.full(stand)||
      PowerArmorRuntime.full(p)||
      ArmorLoadoutData.get(p.level().getServer()).has(p))return;
  if(p.distanceToSqr(stand)>20D)return;
  int tier=PowerArmorRuntime.tier(stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  var type=PowerArmorExitSequence650.typeForEntry655(tier);
  if(type==null)return;
  PowerArmorVisualEntity view=new PowerArmorVisualEntity(type,p.level());
  view.setPos(stand.getX(),stand.getY(),stand.getZ());
  view.setYRot(stand.getYRot());view.setYBodyRot(stand.getYBodyRot());
  view.setYHeadRot(stand.getYHeadRot());
  view.addTag("xsxlabs_b655_entry_hold_visual");
  view.begin(true);view.beginPhase(8);
  if(!p.level().addFreshEntity(view))return;
  boolean originalMarker=stand.isMarker();
  stand.addTag(OPEN_TAG);
  stand.addTag(HIDE_TAG);
  stand.setInvisible(true);
  stand.setMarker(true);  // zero hitbox: player can walk INSIDE
  OPEN.put(id,new Open(stand,view,originalMarker));
  p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
     "Power Armor opened. Walk inside the suit to enter."));
 }
 private static void reset(Open o){
  if(!o.visual().isRemoved())o.visual().discard();
  ArmorStand stand=o.suit();
  if(!stand.isRemoved()){
   stand.setMarker(o.marker());
   stand.removeTag(OPEN_TAG);
   stand.removeTag(HIDE_TAG);
   stand.setInvisible(false);
  }
 }
 private static void reset(ServerPlayer p){Open o=OPEN.remove(p.getUUID());if(o!=null)reset(o);}
 private static boolean inside(ServerPlayer p,ArmorStand stand){
  double dx=p.getX()-stand.getX(),dz=p.getZ()-stand.getZ();
  return dx*dx+dz*dz<=.22D && Math.abs(p.getY()-stand.getY())<.65D;
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post e){
  if(!(e.getEntity() instanceof ServerPlayer p))return;
  UUID id=p.getUUID();
  Closing c=CLOSING.get(id);
  if(c!=null){
   if(PowerArmorRuntime.full(p) || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){
    CLOSING.remove(id);
   }else{
    p.setDeltaMovement(Vec3.ZERO);
    p.setPos(c.start().x,c.start().y,c.start().z);
   }
   return;
  }
  Open opened=OPEN.get(id);
  if(opened==null)return;
  ArmorStand stand=opened.suit();
  if(!p.isAlive()||stand.isRemoved()||opened.visual().isRemoved()||
      !owned(stand,p)||!PowerArmorSuitWorld.full(stand)){
   reset(p);return;
  }
  // Do NOT close after a timer. Only the player's real body entering
  // the open armor can initiate the closure.
  if(!inside(p,stand))return;
  OPEN.remove(id);
  if(!opened.visual().isRemoved())opened.visual().discard();
  stand.setMarker(opened.marker());
  stand.removeTag(OPEN_TAG);
  stand.setInvisible(true);
  Vec3 center=new Vec3(stand.getX(),stand.getY(),stand.getZ());
  p.setPos(center.x,center.y,center.z);
  p.setDeltaMovement(Vec3.ZERO);
  COMMITTING.add(id);
  try{PowerArmorSuitWorld.tryEnter(p,stand.getId());}
  finally{COMMITTING.remove(id);}
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));
 }
 @SubscribeEvent public static void logout(PlayerEvent.PlayerLoggedOutEvent e){
  if(e.getEntity() instanceof ServerPlayer p){
   reset(p);CLOSING.remove(p.getUUID());COMMITTING.remove(p.getUUID());
  }
 }
 @SubscribeEvent public static void clone(PlayerEvent.Clone e){
  UUID id=e.getOriginal().getUUID();
  Open o=OPEN.remove(id);if(o!=null)reset(o);
  CLOSING.remove(id);COMMITTING.remove(id);
 }
}
''',encoding="utf8")
# Reuse the registered 24 visual types; no duplicate registration or new items.
s=exitFile.read_text(encoding="utf8")
s=once(s," public static boolean committing(ServerPlayer p){return COMMITTING.contains(p.getUUID());}",
''' public static boolean committing(ServerPlayer p){return COMMITTING.contains(p.getUUID());}
 public static EntityType<PowerArmorVisualEntity> typeForEntry655(int tier){
  return kind(tier);
 }''')
exitFile.write_text(s,encoding="utf8")
print("B655: 24 Recall rear helmet locked; mask byte-exact; real right-click open-until-walk-in; no item transfer until closing; exit invisible until open")
