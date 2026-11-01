#!/usr/bin/env python3
"""B662: extend existing original MK1/MK2 roundtrip GameTest with visibility."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf8")
def replace(x,y):
 global s
 assert s.count(x)==1,("B662_GAMETEST_DRIFT",x[:100],s.count(x))
 s=s.replace(x,y,1)
replace(
'''                  // Now actually walk to the middle of the zero-collision
                  // open suit; only this physically triggers closing.
                  player.setPos(stand.getX(),stand.getY(),stand.getZ());''',
'''                  // B662: right-click and hold-open must NEVER hide the
                  // real player. Only crossing the suit threshold does.
                  check(!player.isInvisible(),"B662 player hidden before physical entry");
                  // Now actually walk to the middle of the zero-collision
                  // open suit; only this physically triggers closing.
                  player.setPos(stand.getX(),stand.getY(),stand.getZ());''')
replace(
'''                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  completeTransition(player);''',
'''                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  check(player.isInvisible(),"B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP");
                  check(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),
                    "B662 no early transfer while hidden");
                  completeTransition(player);''')
replace(
'''                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  check(stand.isRemoved(),''',
'''                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  check(!player.isInvisible(),"B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE");
                  check(stand.isRemoved(),''')
assert "B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP" in s
assert "B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE" in s
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
assert s.count("completeExitOpening650(player,level,base);")==2
p.write_text(s,encoding="utf8")
print("B662_MK1_MK2_REAL_WALK_IN_VISIBILITY_GAMETEST_INSTALLED")
