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
 "powerarmor/PowerArmorSuitWorld.java",
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
print("B1104_FREEZE175_MANUAL_ENTRY_AND_EXIT_EXACT_SOURCE_PASS")
