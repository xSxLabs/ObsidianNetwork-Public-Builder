#!/usr/bin/env python3
"""Invalidate stale wireless antenna menus only when their visible roster changes.

Wire AFTER management + menu sync-cache. An open menu initially receives an
ID/name snapshot. A remote rename, create or delete must not leave clickable
client labels referring to a different server-side selection. Close stale menus
safely on the normal stillValid check, without re-filtering networks every tick.
No new packets, network scans, FE changes or automatic chunk tickets.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"


def replace(path, before, after):
    file = root / path
    source = file.read_text()
    assert source.count(before) == 1, (
        f"wireless roster guard anchor drift: {path}: {before[:90]!r}"
    )
    file.write_text(source.replace(before, after, 1))


data = "wireless/WirelessNetworkData.java"
replace(
    data,
    " private final LinkedHashMap<String,Entry> networks=new LinkedHashMap<>();",
    """ private final LinkedHashMap<String,Entry> networks=new LinkedHashMap<>();
 // Transient version: the persisted entries remain the only authoritative state.
 private long rosterRevision;
 public long rosterRevision(){return rosterRevision;}""",
)
replace(
    data,
    "  networks.put(created.id(),created);setDirty();return created;",
    "  networks.put(created.id(),created);rosterRevision++;setDirty();return created;",
)
replace(
    data,
    """  networks.put(id,new Entry(id,name,old.owner(),old.chargingMask()));
  setDirty();return true;""",
    """  networks.put(id,new Entry(id,name,old.owner(),old.chargingMask()));
  rosterRevision++;setDirty();return true;""",
)
replace(
    data,
    "  networks.remove(id);setDirty();return true;",
    "  networks.remove(id);rosterRevision++;setDirty();return true;",
)

menu = "menu/WirelessNetworkMenu.java"
replace(
    menu,
    " private final List<String> ids=new ArrayList<>();",
    """ private final List<String> ids=new ArrayList<>();
 // Cheap integer comparison on ordinary server ticks; roster recheck on edits.
 private long observedRosterRevision;""",
)
replace(
    menu,
    "  pos=p.immutable();device=be;data=d;addDataSlots(d);",
    """  pos=p.immutable();device=be;data=d;addDataSlots(d);
  observedRosterRevision=be!=null&&inv.player instanceof ServerPlayer owner
   ?WirelessNetworkData.get(owner.level().getServer()).rosterRevision():-1L;""",
)
replace(
    menu,
    """ public boolean stillValid(Player p){
  return p.distanceToSqr(pos.getX()+0.5,pos.getY()+0.5,pos.getZ()+0.5)<=64.0;
 }""",
    """  public boolean stillValid(Player p){
   if(p.distanceToSqr(pos.getX()+0.5,pos.getY()+0.5,pos.getZ()+0.5)>64.0)return false;
   if(!(p instanceof ServerPlayer owner))return true;
   // Closing an antenna, unloading it or changing worlds invalidates its GUI.
   if(device==null||device.isRemoved()||device.getLevel()!=owner.level()
      ||owner.level().getBlockEntity(pos)!=device||!device.canConfigure(owner))return false;
   var storage=WirelessNetworkData.get(owner.level().getServer());
   long revision=storage.rosterRevision();
   if(revision!=observedRosterRevision){
    // No list allocation or filtering unless some network was created,
    // renamed or deleted. Unrelated owners' changes need not close this menu.
    var fresh=storage.available(owner);
    boolean matches=fresh.size()==ids.size();
    for(int i=0;matches&&i<fresh.size();i++){
     var entry=fresh.get(i);
     matches=ids.get(i).equals(entry.id())&&names.get(i).equals(entry.name());
    }
    if(!matches){
     owner.sendSystemMessage(net.minecraft.network.chat.Component.literal(
      "Wireless networks changed. Reopen this antenna to refresh the list."));
     return false;
    }
    observedRosterRevision=revision;
   }
   return true;
  }""",
)
print("WIRELESS_MENU_ROSTER_INVALIDATION_V1 PASS")
