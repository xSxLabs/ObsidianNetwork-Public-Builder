#!/usr/bin/env python3
"""B636 confirms the post-injection GameTest measures the actual 48-tick lifecycle."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
fixture=(J/"build103/Build103GameTests.java").read_text()
assert world.count("new Animation(stand,48,entering,")==3
assert "int t=49-animation.ticks();" in world
assert "V175_B633_EXIT_BACK_TO_PLAYER" in world
assert fixture.count("V175_B636_48_TICK_ROUNDTRIP")==1
assert "for(int i=0;i<48;i++)" in fixture
assert "for(int i=0;i<20;i++)\n                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.transitionTick(" not in fixture
assert "POWER_ARMOR_REAL_ROUNDTRIP_V69 PASS tier=MK" in fixture
assert "check(!stand.isInvisible(),\"exited suit is invisible, tier \"+tier);" in fixture
assert "POWER_ARMOR_UPGRADES" in fixture
assert "helper.succeed();" in fixture
print("V175_B636_48_TICK_CI_GATE_PASS: real and simulated phase lengths match; item/upgrade/visibility checks preserved")
