#!/usr/bin/env python3
"""B653 no second vanilla arm/head motion on the actual armor-owning stand."""
import os
from pathlib import Path
s=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java").read_text()
assert "-15F*open" not in s and "-28F*open" not in s
for x in ("setLeftArmPose","setRightArmPose","setHeadPose"):
 assert s.count(x+"(new net.minecraft.core.Rotations(0F,0F,0F))")==1,x
assert "PowerArmorExitSequence650.request(player)" in s
assert "PowerArmorExitReveal649.begin(player)" not in s
print("B653_SERVER_FALLBACK_STATIONARY_ARM_HEAD_PASS")
