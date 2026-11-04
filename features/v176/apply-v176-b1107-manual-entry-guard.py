#!/usr/bin/env python3
"""B1107 critical: fail-closed manual walk-in with real server transition proof.

Do not replace the working B655/B662 route: right-click opens, physical walk-in
closes, PowerArmorSuitWorld performs the ONLY item transfer. The original,
item-owning ArmorStand must never be silently concealed when the transfer did
not start, stopped early, timed out, or the player logged out.
"""
import os
from pathlib import Path

def replace_once(src, old, new, name):
    count=src.count(old)
    assert count==1, ("B1107_SOURCE_DRIFT",name,old[:140],count)
    return src.replace(old,new,1)

def world_patch(s):
    old=" private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();"
    new=old+"""
 // B1107: server-authenticated proof: did the ORIGINAL stand enter the
 // transaction state? A successful void method call alone proves nothing.
 public static boolean entryStarted1107(ServerPlayer player,ArmorStand suit){
  Animation state=ACTIVE.get(player.getUUID());
  return state!=null && state.stand()==suit && state.entering()
      && !suit.isRemoved();
 }"""
    return replace_once(s,old,new,"PowerArmorSuitWorld.ACTIVE")

def entry_patch(s):
    anchor=" private static boolean inside(ServerPlayer p,ArmorStand stand){"
    helper=""" // B1107 diagnostic: server log AND direct owner feedback, only on failure.
 private static void fault1107(ServerPlayer p,ArmorStand stand,String why){
  String state="reason="+why+" mk="+PowerArmorRuntime.tier(
      stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0)
      +" suitId="+stand.getId()+" removed="+stand.isRemoved()
      +" complete="+PowerArmorSuitWorld.full(stand)
      +" owner="+owned(stand,p)
      +" wearerFull="+PowerArmorRuntime.full(p)
      +" hasBackup="+ArmorLoadoutData.get(p.level().getServer()).has(p);
  org.slf4j.LoggerFactory.getLogger("xSxLabs/PowerArmorEntry")
      .warn("B1107_MANUAL_ENTRY_FAILED player={} {}",p.getName().getString(),state);
  p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
      "Power Armor entry aborted: "+why+". Original suit retained. See latest.log."));
 }
 // Never fabricate, drop, or duplicate equipment. Make the SAME original
 // ArmorStand and its already-owned item slots visible and interactable.
 private static void recover1107(ServerPlayer p,ArmorStand stand){
  if(stand==null||stand.isRemoved()||!owned(stand,p))return;
  stand.removeTag(OPEN_TAG);
  stand.removeTag(HIDE_TAG);
  stand.setInvisible(false);
 }
"""
    s=replace_once(s,anchor,helper+anchor,"entry.helper")
    old="""   if(PowerArmorRuntime.full(p) || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){
    CLOSING.remove(id);
    restoreVisibility662(p); // real equip succeeded, cancelled, died or timed out
   }else{
    p.setDeltaMovement(Vec3.ZERO);
    p.setPos(c.start().x,c.start().y,c.start().z);
   }"""
    new="""   boolean equipped=PowerArmorRuntime.full(p);
   boolean active=!c.suit().isRemoved()
       &&PowerArmorSuitWorld.entryStarted1107(p,c.suit());
   if(equipped || !active || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){
    CLOSING.remove(id);
    restoreVisibility662(p);
    if(!equipped && !c.suit().isRemoved()){
     recover1107(p,c.suit());
     fault1107(p,c.suit(),!active?"server transition stopped":
         !p.isAlive()?"player no longer alive":"entry timeout");
    }
   }else{
    // Defensive invariant: an untransferred, still-full owned suit is visible.
    // Its cosmetic close animation must not eat the underlying item owner.
    recover1107(p,c.suit());
    p.setDeltaMovement(Vec3.ZERO);
    p.setPos(c.start().x,c.start().y,c.start().z);
   }"""
    s=replace_once(s,old,new,"entry.closing")
    old="""  if(!inside(p,stand))return;
  OPEN.remove(id);"""
    new="""  if(!inside(p,stand))return;
  // Revalidate AT THE PHYSICAL STEP. The player can equip/die/change level
  // or acquire an existing saved loadout between click and walk-in.
  if(PowerArmorRuntime.full(p)||ArmorLoadoutData.get(p.level().getServer()).has(p)
      ||stand.level()!=p.level()||!owned(stand,p)||!PowerArmorSuitWorld.full(stand)){
   fault1107(p,stand,"precondition changed before walk-in");
   reset(p);
   return;
  }
  OPEN.remove(id);"""
    s=replace_once(s,old,new,"entry.precheck")
    old="""  stand.noPhysics=opened.marker();
  stand.removeTag(OPEN_TAG);
  stand.setInvisible(true);"""
    new="""  stand.noPhysics=opened.marker();
  stand.removeTag(OPEN_TAG);
  stand.removeTag(HIDE_TAG);
  // Do not conceal the actual item-owning stand before confirmed transfer.
  stand.setInvisible(false);"""
    s=replace_once(s,old,new,"entry.real-stand")
    old="""  BEFORE_HIDE_662.put(id,p.isInvisible());
  p.setInvisible(true);
  COMMITTING.add(id);
  try{PowerArmorSuitWorld.tryEnter(p,stand.getId());}
  finally{COMMITTING.remove(id);}
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));"""
    new="""  // The real player remains visible until the server actually equips armor.
  // Client phase-9 render suppression is separately guarded by isInvisible().
  COMMITTING.add(id);
  boolean started=false;
  try{
   PowerArmorSuitWorld.tryEnter(p,stand.getId());
   started=PowerArmorSuitWorld.entryStarted1107(p,stand)
       ||PowerArmorRuntime.full(p);
  }catch(RuntimeException error){
   org.slf4j.LoggerFactory.getLogger("xSxLabs/PowerArmorEntry")
       .error("B1107_MANUAL_ENTRY_EXCEPTION suitId="+stand.getId(),error);
  }finally{
   COMMITTING.remove(id);
  }
  if(!started){
   recover1107(p,stand);
   restoreVisibility662(p);
   fault1107(p,stand,"server rejected transition");
   return;
  }
  recover1107(p,stand);
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));"""
    s=replace_once(s,old,new,"entry.transaction")
    old="""   reset(p);CLOSING.remove(p.getUUID());COMMITTING.remove(p.getUUID());
   restoreVisibility662(p); // never persist invisibility across logout"""
    new="""   reset(p);
   Closing interrupted=CLOSING.remove(p.getUUID());
   if(interrupted!=null&&!PowerArmorRuntime.full(p))
    recover1107(p,interrupted.suit());
   COMMITTING.remove(p.getUUID());
   restoreVisibility662(p); // never persist invisibility across logout"""
    s=replace_once(s,old,new,"entry.logout")
    old="""  CLOSING.remove(id);COMMITTING.remove(id);
  Boolean previous=BEFORE_HIDE_662.remove(id);"""
    new="""  Closing interrupted=CLOSING.remove(id);
  if(interrupted!=null && e.getOriginal() instanceof ServerPlayer previousPlayer
      && !PowerArmorRuntime.full(previousPlayer))
   recover1107(previousPlayer,interrupted.suit());
  COMMITTING.remove(id);
  Boolean previous=BEFORE_HIDE_662.remove(id);"""
    s=replace_once(s,old,new,"entry.respawn")
    assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in s
    assert "if(!inside(p,stand))return;" in s
    assert "stand.discard()" not in s and "new ArmorStand(" not in s
    return s

def render_patch(s):
    old="v->v.isExitOpening659(p.getUUID()) || v.isClosingFor659(p.getUUID())).isEmpty();"
    new="v->v.isExitOpening659(p.getUUID()) || (p.isInvisible() && v.isClosingFor659(p.getUUID()))).isEmpty();"
    return replace_once(s,old,new,"client.phase9")

def test_patch(s):
    old='check(player.isInvisible(),"B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP");'
    new='''check(!player.isInvisible(),"B1107_PHYSICAL_ENTRY_PLAYER_VISIBLE");
                  check(!stand.isInvisible(),"B1107_ORIGINAL_WORLD_SUIT_VISIBLE_WHILE_ENTERING");
                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.entryStarted1107(player,stand),
                     "B1107_REAL_SERVER_ENTRY_ANIMATION_STARTED");'''
    s=replace_once(s,old,new,"gametest.visible-player")
    # B1108: the original 24-tier test used to invoke the subscriber directly.
    # That can pass even if the real NeoForge event bus never registered it.
    # Post the actual PlayerTickEvent in the game test to verify registration.
    needle="dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick("
    count=s.count(needle)
    assert count==3,("B1108_REAL_EVENTBUS_FIXTURE_DRIFT",count)
    s=s.replace(needle,"net.neoforged.neoforge.common.NeoForge.EVENT_BUS.post(",3)
    assert s.count("net.neoforged.neoforge.common.NeoForge.EVENT_BUS.post(")==3
    return s

def apply():
    root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
    for rel,fn in (
        ("powerarmor/PowerArmorSuitWorld.java",world_patch),
        ("powerarmor/PowerArmorEntrySequence655.java",entry_patch),
        ("client/PowerArmorExitRender659.java",render_patch),
        ("build103/Build103GameTests.java",test_patch)):
        path=root/rel
        s=path.read_text(encoding="utf-8")
        path.write_text(fn(s),encoding="utf-8")
    print("B1107_MANUAL_ENTRY_REAL_TRANSITION_PROOF_VISIBLE_OWNER_DIAGNOSTIC_ROLLBACK_PASS")

if __name__=="__main__":
    apply()
