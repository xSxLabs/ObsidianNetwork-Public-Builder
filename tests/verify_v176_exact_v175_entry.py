#!/usr/bin/env python3
"""Fail-closed: ship the exact v1.7.5-build662 manual entry/exit runtime."""
from pathlib import Path
import os, hashlib
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
frozen=Path("/tmp/xsxlabs-v175-entry-freeze")
for rel in ("powerarmor/PowerArmorEntrySequence655.java",
            "powerarmor/PowerArmorSuitWorld.java",
            "powerarmor/PowerArmorExitSequence650.java",
            "client/PowerArmorExitRender659.java"):
    p=root/rel
    baseline=frozen/Path(rel).name
    assert baseline.is_file() and p.is_file(), ("FREEZE_FILE_MISSING",rel)
    if rel.endswith("PowerArmorSuitWorld.java"):
        def method(source, signature):
            start=source.index(signature)
            pos=source.index("{",start)
            depth=0
            for end in range(pos,len(source)):
                if source[end]=="{": depth+=1
                elif source[end]=="}":
                    depth-=1
                    if depth==0: return source[start:end+1]
            raise AssertionError(("UNCLOSED_METHOD",signature))
        old=baseline.read_text()
        new=p.read_text()
        for signature in (
            " public static void tryEnter(ServerPlayer player,int entityId){",
            " private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){"):
            assert method(old,signature)==method(new,signature),("FREEZE_WORLD_ENTRY_DRIFT",signature)
        continue
    if rel.endswith("PowerArmorEntrySequence655.java"):
        import runpy
        assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in p.read_text()
        assert "dx*dx+dz*dz<=.81D" in p.read_text()
        assert "stand.setInvisible(false);" in p.read_text()
    else:
        assert p.read_bytes()==baseline.read_bytes(),("FREEZE_ENTRY_EXIT_DRIFT",rel)
    print("FREEZE175_EXACT",rel,hashlib.sha256(p.read_bytes()).hexdigest())
test=(root/"build103/Build103GameTests.java").read_text()
assert "for(int tier=0;tier<24;tier++)" in test, "MK1_MK24_TEST_MISSING"
assert "POWER_ARMOR_REAL_ROUNDTRIP_V69" in test
assert "B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP" in test
assert "B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE" in test
assert "check(stand.isRemoved()," in test
print("FREEZE175_MK1_MK24_ENTRY_EXIT_SOURCE_GATE_PASS")
