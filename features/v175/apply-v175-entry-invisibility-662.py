#!/usr/bin/env python3
"""B662: hide the actual wearer the instant physical walk-in begins.
Keep all MK1-24 armor pieces, Recall, FE, storage, recipes, 40-tick transfer
and the right-click open-until-walk-in behavior unchanged.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(path,before,after):
 p=J/path
 src=p.read_text(encoding="utf8")
 n=src.count(before)
 assert n==1,("B662_SOURCE_DRIFT",path,before[:110],n)
 p.write_text(src.replace(before,after,1),encoding="utf8")

# The client already has the exact owner UUID and synchronized animation phase.
# Reuse the proven exit render-state suppression: when phase 9 is active,
# hide the REAL player (skin, armor, held models) and never the GeckoLib shell.
edit("client/PowerArmorExitRender659.java",
    'v->v.isExitOpening659(p.getUUID())).isEmpty();',
    'v->v.isExitOpening659(p.getUUID()) || v.isClosingFor659(p.getUUID())).isEmpty();')
edit("client/PowerArmorExitRender659.java",
    ' * Phase 9 entry is never hidden by this guard.',
    ' * Phase 9 entry is hidden from physical step-in until close/transfer ends.')

# Vanilla invisible flag is authoritative for multiplayer. Preserve its
# ORIGINAL state (including potion/modded invisibility) through equip/failure.
# Owner-specific client render guard also hides armor layers that vanilla
# invisible flags alone do not remove.
entry="powerarmor/PowerArmorEntrySequence655.java"
edit(entry,
''' private static final Set<UUID> COMMITTING=new HashSet<>();
 private static final String OPEN_TAG''',
''' private static final Set<UUID> COMMITTING=new HashSet<>();
 private static final Map<UUID,Boolean> BEFORE_HIDE_662=new HashMap<>();
 private static void restoreVisibility662(ServerPlayer p){
  Boolean previous=BEFORE_HIDE_662.remove(p.getUUID());
  if(previous!=null)p.setInvisible(previous);
 }
 private static final String OPEN_TAG''')
edit(entry,
'''    CLOSING.remove(id);
   }else{
    p.setDeltaMovement(Vec3.ZERO);''',
'''    CLOSING.remove(id);
    restoreVisibility662(p); // real equip succeeded, cancelled, died or timed out
   }else{
    p.setDeltaMovement(Vec3.ZERO);''')
edit(entry,
'''  p.setPos(center.x,center.y,center.z);
  p.setDeltaMovement(Vec3.ZERO);
  COMMITTING.add(id);''',
'''  p.setPos(center.x,center.y,center.z);
  p.setDeltaMovement(Vec3.ZERO);
  // The threshold is the REAL physical walk-in, never the earlier right-click.
  // Hide before beginning the item-safe equip transaction, including for peers.
  BEFORE_HIDE_662.put(id,p.isInvisible());
  p.setInvisible(true);
  COMMITTING.add(id);''')
edit(entry,
'''   reset(p);CLOSING.remove(p.getUUID());COMMITTING.remove(p.getUUID());
  }
 }
 @SubscribeEvent public static void clone''',
'''   reset(p);CLOSING.remove(p.getUUID());COMMITTING.remove(p.getUUID());
   restoreVisibility662(p); // never persist invisibility across logout
  }
 }
 @SubscribeEvent public static void clone''')
edit(entry,
'''  CLOSING.remove(id);COMMITTING.remove(id);
 }
}''',
'''  CLOSING.remove(id);COMMITTING.remove(id);
  Boolean previous=BEFORE_HIDE_662.remove(id);
  if(previous!=null && e.getEntity() instanceof ServerPlayer next)
   next.setInvisible(previous); // respawn after interrupted closing
 }
}''')
# Genuine world transaction can fail before scheduling CLOSING. Make sure
# restore does not depend on COMMITTING. Expiration path is independent.
src=(J/entry).read_text(encoding="utf8")
assert "p.tickCount+88" in src and "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in src
assert src.count("restoreVisibility662(p)") == 2
assert "p.setInvisible(true);" in src
assert "visual.beginPhase(9)" in (J/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf8")
assert "v.isClosingFor659(p.getUUID())" in (J/"client/PowerArmorExitRender659.java").read_text(encoding="utf8")
print("B662_OWNER_SPECIFIC_MULTIPLAYER_ENTRY_HIDE_AND_RECOVERY_PASS")
