#!/usr/bin/env python3
"""B1102 P0: prove a real ArmorStand entry is running; never conceal real items."""
import os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(name,old,new):
 p=j/name
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1102_SOURCE_DRIFT",name,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

change("powerarmor/PowerArmorSuitWorld.java",
 " private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();",
 """ private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();
 // B1102: the original item-owning ArmorStand has an actual pending transition.
 public static boolean isEnteringOriginal1102(ServerPlayer player,ArmorStand suit){
  Animation a=ACTIVE.get(player.getUUID());
  return a!=null && a.stand()==suit && a.entering()
     && !suit.isRemoved() && mine(suit,player) && full(suit);
 }""")

path="powerarmor/PowerArmorEntrySequence655.java"
change(path,
 """  stand.noPhysics=opened.marker();
  stand.removeTag(OPEN_TAG);
  stand.setInvisible(true);""",
 """  stand.noPhysics=opened.marker();
  stand.removeTag(OPEN_TAG);
  // B1102: physical suit must remain visible until actual safe equip.
  stand.setInvisible(false);""")
change(path,
 """  BEFORE_HIDE_662.put(id,p.isInvisible());
  p.setInvisible(true);
  COMMITTING.add(id);""",
 """  // B1102: keep owner visible through server transaction; prevent
  // invisible-player plus invisible-suit loss when transfer is refused.
  COMMITTING.add(id);""")
change(path,
 """   PowerArmorSuitWorld.tryEnter(p,stand.getId());
   transitionStarted=true;""",
 """   PowerArmorSuitWorld.tryEnter(p,stand.getId());
   transitionStarted=PowerArmorSuitWorld.isEnteringOriginal1102(p,stand);
   if(transitionStarted)stand.setInvisible(false);""")
change(path,
 "  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));",
 """  if(!transitionStarted){
   p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
    "Power Armor entry rejected; original suit retained. Retry."));
   return;
  }
  CLOSING.put(id,new Closing(stand,center,p.tickCount+88));""")
change(path,
 """   if(equipped || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){""",
 """   // B1102: if the real transaction stopped without equip, recover NOW.
   boolean running=PowerArmorSuitWorld.isEnteringOriginal1102(p,c.suit());
   if(equipped || !running || p.tickCount>=c.expiry() ||
        !p.isAlive() || c.suit().isRemoved()){""")
# Existing 26.1 real MK1/MK2 roundtrip GameTest previously demanded invisibility.
# Replace with a test of genuine transfer start plus visible actual item owner.
change("build103/Build103GameTests.java",
 '                  check(player.isInvisible(),"B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP");',
 """                  check(!player.isInvisible(),"B1102_PLAYER_MUST_REMAIN_VISIBLE");
                  check(!stand.isInvisible(),"B1102_REAL_SUIT_MUST_REMAIN_VISIBLE");
                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.isEnteringOriginal1102(player,stand),
                    "B1102_REAL_TRANSFER_NOT_STARTED");""")
entry=(j/path).read_text(encoding="utf-8")
world=(j/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
test=(j/"build103/Build103GameTests.java").read_text(encoding="utf-8")
assert "B1102_REAL_TRANSFER_NOT_STARTED" in test
assert "public static boolean isEnteringOriginal1102" in world
assert "transitionStarted=PowerArmorSuitWorld.isEnteringOriginal1102(p,stand);" in entry
assert "if(!transitionStarted){" in entry
assert "stand.discard()" not in entry and "new ArmorStand(" not in entry
print("B1102_REAL_ARMOR_ENTRY_P0_PASS")
