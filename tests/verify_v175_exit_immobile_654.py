#!/usr/bin/env python3
"""B654: server and client exit-lock source contract; preserve item transfer."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
s=(J/"powerarmor/PowerArmorExitSequence650.java").read_text()
v=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
c=(J/"client/PowerArmorExitInputLock654.java").read_text()
f=(J/"build103/Build103GameTests.java").read_text()
assert "visual.setExitOwner654(p.getUUID());" in s
assert "public static void pre(PlayerTickEvent.Pre e)" in s
assert "hold(p,x);" in s and "hold(p,pending);" in s
assert "p.setDeltaMovement(Vec3.ZERO);" in s
assert "p.setPos(origin.x,origin.y,origin.z);" in s
assert "distanceToSqr(pending.start())>1.0D" not in s
assert "if(p.tickCount<pending.deadline())return;" in s
assert "p.tickCount+64" in s
assert "PowerArmorSuitWorld.exit(p)" in s
assert "setInvisible(" not in s and "setInvisible(" not in c
assert "builder.define(EXIT_OWNER_654,\"\");" in v
assert "entityData.get(V175_PHASE)==7" in v
assert "entityData.get(EXIT_OWNER_654).equals(uuid.toString())" in v
assert "p.input=ZERO_INPUT;" in c and "p.input=previousInput;" in c
assert "v->v.isOpeningFor654(p.getUUID())" in c
assert "ClientTickEvent.Pre" in c and "ClientTickEvent.Post" in c
assert "setDeltaMovement(Vec3.ZERO)" in c
assert "for(int step=0;step<64;step++)" in f
assert "POWER_ARMOR_REAL_ROUNDTRIP_V69" in f
assert "PowerArmorExitReveal649" not in s
print("B654_EXIT_FREEZE_BOTH_SIDES_NO_CANCEL_FULL_64_TICK_TRANSFER_PASS")
