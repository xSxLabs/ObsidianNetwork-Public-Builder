#!/usr/bin/env python3
"""B657: NeoForge 26.1 API compile fixes only for B655 entry helper.
ArmorStand has no getYBodyRot(); its setMarker is PRIVATE. Use the
public inherited noPhysics flag to prevent collisions during walk-in.
Restore the prior flag after exit/abort; preserve all item safeguards.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorEntrySequence655.java"
s=p.read_text(encoding="utf8")
for a,b in (
 ("view.setYBodyRot(stand.getYBodyRot());","view.setYBodyRot(stand.getYRot());"),
 ("boolean originalMarker=stand.isMarker();","boolean originalMarker=stand.noPhysics;"),
 ("stand.setMarker(true);  // zero hitbox: player can walk INSIDE",
  "stand.noPhysics=true;  // vanilla ArmorStand passes through player while open"),
 ("stand.setMarker(o.marker());","stand.noPhysics=o.marker();"),
 ("stand.setMarker(opened.marker());","stand.noPhysics=opened.marker();")
):
 assert s.count(a)==1,("B657_FIX_ANCHOR",a,s.count(a))
 s=s.replace(a,b,1)
assert "setMarker(" not in s and "getYBodyRot" not in s
assert s.count("noPhysics=")==3 and s.count("isMarker(")==0
assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in s
p.write_text(s,encoding="utf8")
print("B657_NEOFORGE_26_1_ENTRY_STAND_API: no private setMarker; no removed getYBodyRot; noPhysics restored after walk-in")
