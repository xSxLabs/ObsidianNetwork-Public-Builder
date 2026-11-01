#!/usr/bin/env python3
"""B658 preserves original 2x roundtrip and held-open ownership assertions."""
import os
from pathlib import Path
s=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java").read_text()
assert s.count("player.setPos(base.getX()+0.5D,base.getY(),base.getZ()+0.5D);")==2
assert "for(int openTick=0;openTick<96;openTick++)" in s
assert "for(int step=0;step<64;step++)" in s
assert s.count("completeExitOpening650(player,level,base);")==2
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
assert 'protection5_roundtrip=true' in s
print("B658_TEST_ONLY_RESET_POS_KEEP_ALL_CONSERVATION_CHECKS_PASS")
