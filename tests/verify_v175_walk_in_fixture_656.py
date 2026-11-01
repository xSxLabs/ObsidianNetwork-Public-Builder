#!/usr/bin/env python3
"""B656 test remains fail-closed; no shortened item conservation proofs."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text()
assert "for(int openTick=0;openTick<96;openTick++)" in s
assert "PowerArmorEntrySequence655.tick(" in s
assert "player.setPos(stand.getX(),stand.getY(),stand.getZ());" in s
assert "PowerArmorSuitWorld.full(stand)" in s
assert "owned(level,base,player).size()==1" in s
assert "check(stand.isRemoved()" in s
assert "protectionFive.equals(stand.getItemBySlot" in s
assert "protectionFive.equals(player.getItemBySlot" in s
assert s.count("completeExitOpening650(player,level,base);")==2
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
print("B656_ALL_REAL_ROUNDTRIP_ASSERTIONS_RETAINED_ENTRY_OPEN_HOLD_STEPS_CHECKED_PASS")
