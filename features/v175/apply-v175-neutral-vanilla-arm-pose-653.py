#!/usr/bin/env python3
"""B653: Remove hidden vanilla ArmorStand arm/head pitch during hatch opening.
B652 already freezes the whole GeckoLib arms. In B651's compiled Java,
the real owned ArmorStand STILL pitched its left and right arms by -15deg
and whole helmet by -28deg via fallback pose(), causing visual regressions.
Reset only fallback poses; preserve original item ownership, FE and recall.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java"
s=p.read_text(encoding="utf-8")
for old,new in (
 ("stand.setLeftArmPose(new net.minecraft.core.Rotations(-15F*open,0F,-spread));",
  "stand.setLeftArmPose(new net.minecraft.core.Rotations(0F,0F,0F)); // B653 stationary left arm"),
 ("stand.setRightArmPose(new net.minecraft.core.Rotations(-15F*open,0F,spread));",
  "stand.setRightArmPose(new net.minecraft.core.Rotations(0F,0F,0F)); // B653 stationary right arm"),
 ("stand.setHeadPose(new net.minecraft.core.Rotations(-28F*open,0F,0F));",
  "stand.setHeadPose(new net.minecraft.core.Rotations(0F,0F,0F)); // B653 stationary helmet; mask opens independently"),
):
 assert s.count(old)==1,("B653 fallback drift",old,s.count(old))
 s=s.replace(old,new,1)
assert s.count("setLeftArmPose(")==1 and s.count("setRightArmPose(")==1
assert "PowerArmorExitSequence650.request(player)" in s
assert "PowerArmorExitReveal649.begin(player)" not in s
p.write_text(s,encoding="utf-8")
print("B653_WORLD_STAND_LEFT_RIGHT_ARMS_AND_HEAD_NEUTRAL_NO_EXTRA_SWING_PASS")
