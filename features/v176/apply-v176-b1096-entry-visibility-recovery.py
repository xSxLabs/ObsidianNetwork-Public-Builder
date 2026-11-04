#!/usr/bin/env python3
"""B1096: fail-safe after physical power-armor entry.

B655/B662 hid the stand and the wearer on walk-in, but when the underlying
equip transaction refused or timed out CLOSING was removed without unhiding
the still-owned stand. Restore the existing original stand and its item stacks
(never spawn or copy armor), and ensure the player render guard stops when the
server restores player visibility. This is recovery, not a new equip route.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
entry=J/"powerarmor/PowerArmorEntrySequence655.java"
s=entry.read_text(encoding="utf-8")
anchor=" private static boolean inside(ServerPlayer p,ArmorStand stand){"
helper=""" // B1096_ENTRY_ROLLBACK_VISIBILITY: a failed transfer must never leave
 // the ORIGINAL still-owned world suit invisible after the close animation.
 // Inventory and item ownership remain solely in PowerArmorSuitWorld.
 private static void restoreFailedSuit1096(ServerPlayer p,ArmorStand stand){
  if(stand==null||stand.isRemoved())return;
  if(!owned(stand,p))return; // never touch a different player's ArmorStand
  stand.removeTag(OPEN_TAG);
  stand.removeTag(HIDE_TAG);
  stand.setInvisible(false);
  stand.noPhysics=false;
  stand.setChangedForViewer1096();
 }
"""
# ArmorStand has no setChangedForViewer1096; vanilla entity flags/tag changes
# are synchronized by setInvisible and the existing EquipmentSlot data tracker.
helper=helper.replace("  stand.setChangedForViewer1096();\n","")
assert s.count(anchor)==1,("B1096_INSIDE_ANCHOR",s.count(anchor))
assert s.count("private static void restoreFailedSuit1096")==0
s=s.replace(anchor,helper+anchor,1)
old="""   if(PowerArmorRuntime.full(p) || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){
    CLOSING.remove(id);
    restoreVisibility662(p); // real equip succeeded, cancelled, died or timed out
   }else{"""
new="""   boolean equipped=PowerArmorRuntime.full(p);
   if(equipped || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){
    CLOSING.remove(id);
    restoreVisibility662(p); // release BOTH wearer skin and armor visibility
    if(!equipped && !c.suit().isRemoved()){
     restoreFailedSuit1096(p,c.suit());
     if(p.isAlive())p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
       "Power Armor entry was not completed. Your original suit is visible again."));
    }
   }else{"""
assert s.count(old)==1,("B1096_STUCK_CLOSING_SOURCE_DRIFT",s.count(old))
s=s.replace(old,new,1)
# If tryEnter throws, the CLOSING tick never starts. The old finally removed
# COMMITTING but stranded both invisible player and invisible ArmorStand.
old="""  COMMITTING.add(id);
  try{PowerArmorSuitWorld.tryEnter(p,stand.getId());}
  finally{COMMITTING.remove(id);}
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));"""
new="""  COMMITTING.add(id);
  boolean transitionStarted=false;
  try{
   PowerArmorSuitWorld.tryEnter(p,stand.getId());
   transitionStarted=true;
  }finally{
   COMMITTING.remove(id);
   if(!transitionStarted){
    restoreVisibility662(p);
    restoreFailedSuit1096(p,stand);
   }
  }
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));"""
assert s.count(old)==1,("B1096_TRANSACTION_START_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
# Logout during a pending unsuccessful entry must not persist an invisible
# still-full suit; no creation, deletion, equipment transfer or duplication.
old="   reset(p);CLOSING.remove(p.getUUID());COMMITTING.remove(p.getUUID());\n   restoreVisibility662(p);"
new="""   reset(p);
   Closing unfinished=CLOSING.remove(p.getUUID());
   if(unfinished!=null&&!PowerArmorRuntime.full(p))
    restoreFailedSuit1096(p,unfinished.suit());
   COMMITTING.remove(p.getUUID());
   restoreVisibility662(p);"""
assert s.count(old)==1,("B1096_LOGOUT_RECOVERY_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
old="  CLOSING.remove(id);COMMITTING.remove(id);\n  Boolean previous=BEFORE_HIDE_662.remove(id);"
new="""  Closing unfinished=CLOSING.remove(id);
  if(unfinished!=null && e.getOriginal() instanceof ServerPlayer oldPlayer
     && !PowerArmorRuntime.full(oldPlayer))
   restoreFailedSuit1096(oldPlayer,unfinished.suit());
  COMMITTING.remove(id);
  Boolean previous=BEFORE_HIDE_662.remove(id);"""
assert s.count(old)==1,("B1096_CLONE_RECOVERY_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
for token in (
    "PowerArmorSuitWorld.tryEnter(p,stand.getId());",
    "if(!inside(p,stand))return;",
    "BEFORE_HIDE_662.put(id,p.isInvisible());",
    "restoreVisibility662(p)",
    "CLOSING.put(id,new Closing(stand,center,p.tickCount+88));",
    "stand.noPhysics=opened.marker();",
):
    assert token in s,("B1096_ENTRY_SAFETY_DRIFT",token)
assert "new ArmorStand(" not in s and "new ItemStack(" not in s and "stand.discard()" not in s
entry.write_text(s,encoding="utf-8")

# B662's client guard can keep an already-equipped player invisible because
# a decorative phase-9 visual lingers. Only suppress while server says the
# actual wearer is invisible; do not change the original exit guard.
render=J/"client/PowerArmorExitRender659.java"
t=render.read_text(encoding="utf-8")
old="v->v.isExitOpening659(p.getUUID()) || v.isClosingFor659(p.getUUID())).isEmpty();"
new="v->v.isExitOpening659(p.getUUID()) || (p.isInvisible() && v.isClosingFor659(p.getUUID()))).isEmpty();"
assert t.count(old)==1,("B1096_CLIENT_RENDER_STUCK_HIDE",t.count(old))
assert "RenderPlayerEvent.Pre<?>" in t
t=t.replace(old,new,1)
render.write_text(t,encoding="utf-8")
print("B1096_ENTRY_TIMEOUT_CANCEL_LOGOUT_RESTORE_ORIGINAL_SUIT_AND_WEARER_VISIBILITY_PASS")
