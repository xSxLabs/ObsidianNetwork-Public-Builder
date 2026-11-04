#!/usr/bin/env python3
"""B1104: prove the actual generated manual-entry runtime matches freeze 1.7.5.

B1103 GameTests simulate all 24 tiers and both Curios configurations, but
the earlier B1096/B1102 entry patches changed the shipped behavior compared
to the user's confirmed good freeze/v1.7.5-build662. Compare the exact
generated class bytes from immediately after unchanged B662 overlay with
all final v1.7.6 generated runtime classes. Anything touching these
four classes must be reviewed before it can ship. V1.7.6's rest is untouched.
"""
import hashlib,os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
baseline=Path("/tmp/xsxlabs-v175-entry-freeze")
classes={
 "powerarmor/PowerArmorEntrySequence655.java",
 "powerarmor/PowerArmorExitSequence650.java",
 "client/PowerArmorExitRender659.java",
}
for rel in sorted(classes):
 original=baseline/Path(rel).name
 final=root/rel
 assert original.is_file(),("B1104_BASELINE_MISSING",rel)
 assert final.is_file(),("B1104_RUNTIME_MISSING",rel)
 a=original.read_bytes()
 b=final.read_bytes()
 assert a==b,("B1104_FREEZE_175_SOURCE_DRIFT",rel,
   hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest())
 print("B1104_FREEZE_175_MATCH",rel,hashlib.sha256(b).hexdigest())

# 1.7.6 adds legitimate world / turret logic: compare only the manual-enter
# dispatch methods, not the entire world class.
source175=(baseline/"PowerArmorSuitWorld.java").read_text(encoding="utf-8")
source176=(root/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
def method(source,signature):
 a=source.index(signature)
 i=source.index("{",a)
 depth=0
 for j in range(i,len(source)):
  if source[j]=="{":depth+=1
  elif source[j]=="}":
   depth-=1
   if depth==0:return source[a:j+1]
 raise AssertionError(("B1106_BAD_METHOD",signature))
for name in (" public static void tryEnter(ServerPlayer player,int entityId){",
 " private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){"):
 assert method(source175,name)==method(source176,name),("B1106_MANUAL_ENTRY_SOURCE_DRIFT",name)
assert "PowerArmorEntrySequence655.request(stand,player);" in source176
assert "if(!PowerArmorEntrySequence655.committing(player))" in source176
assert "case 9 -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK9.get();" in source176

e=(root/"powerarmor/PowerArmorEntrySequence655.java").read_text()
w=(root/"powerarmor/PowerArmorSuitWorld.java").read_text()
render=(root/"client/PowerArmorExitRender659.java").read_text()
assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in e
assert "private static void restoreVisibility662(ServerPlayer p)" in e
assert "if(!inside(p,stand))return;" in e
assert "stand.setInvisible(true);" in e
assert "B1096_ENTRY_ROLLBACK_VISIBILITY" not in e
assert "isEnteringOriginal1102" not in w
assert "v.isClosingFor659(p.getUUID())" in render
assert "v.isExitOpening659(p.getUUID())" in render
print("B1106_FREEZE175_MANUAL_ENTRY_METHODS_AND_176_WORLD_FEATURES_PASS")
