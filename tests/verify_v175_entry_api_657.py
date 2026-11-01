#!/usr/bin/env python3
"""Check B657 NeoForge public APIs without relaxing B655/B656 item proof."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
s=(J/"powerarmor/PowerArmorEntrySequence655.java").read_text()
assert "getYBodyRot" not in s and "setMarker(" not in s
assert "view.setYBodyRot(stand.getYRot());" in s
assert "stand.noPhysics=true;" in s
assert "stand.noPhysics=o.marker();" in s
assert "stand.noPhysics=opened.marker();" in s
assert "if(!inside(p,stand))return;" in s
assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in s
print("B657_SUPPORTED_ARMORSTAND_COLLISION_FREE_WALK_IN_PASS")
