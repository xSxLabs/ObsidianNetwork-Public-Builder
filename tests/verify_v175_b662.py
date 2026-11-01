#!/usr/bin/env python3
"""B662 source and MK1/MK2 live GameTest contract: conceal only during walk-in."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
s=(J/"powerarmor/PowerArmorEntrySequence655.java").read_text(encoding="utf8")
r=(J/"client/PowerArmorExitRender659.java").read_text(encoding="utf8")
v=(J/"powerarmor/PowerArmorVisualEntity.java").read_text(encoding="utf8")
w=(J/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf8")
f=(J/"build103/Build103GameTests.java").read_text(encoding="utf8")
assert "BEFORE_HIDE_662.put(id,p.isInvisible());" in s
assert "p.setInvisible(true);" in s
assert s.index("if(!inside(p,stand))return;") < s.index("BEFORE_HIDE_662.put")
assert s.index("BEFORE_HIDE_662.put") < s.index("PowerArmorSuitWorld.tryEnter(p,stand.getId());")
assert s.count("restoreVisibility662(p)") == 2
assert "Boolean previous=BEFORE_HIDE_662.remove(id)" in s
assert "next.setInvisible(previous)" in s
assert "return;" in s and "CLOSING.put(id,new Closing(stand,center,p.tickCount+88))" in s
assert "v->v.isExitOpening659(p.getUUID()) || v.isClosingFor659(p.getUUID())" in r
assert "RenderPlayerEvent.Pre" in r and "e.setCanceled(true)" in r
assert "entityData.get(V175_PHASE)==9" in v
assert "visual.beginPhase(9)" in w
assert "B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP" in f
assert "B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE" in f
assert "for(int openTick=0;openTick<96;openTick++)" in f
assert "for(int step=0;step<64;step++)" in f
assert "PowerArmorSuitWorld.exit(p)" in (J/"powerarmor/PowerArmorExitSequence650.java").read_text(encoding="utf8")
print("B662_ENTRY_SUIT_CONCEAL_AND_RECOVERY_GATE_PASS")
