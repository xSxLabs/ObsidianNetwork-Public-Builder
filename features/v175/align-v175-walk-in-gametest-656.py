#!/usr/bin/env python3
"""B656: adapt real MK1/MK2 GameTest for intentional open-until-walk-in.
Preserve every earlier original-armor, five-card and anti-dupe assertion.
Test must enforce NO equipment transfer while the player is outside.
Only temporary GameTest fixture is changed; packaged source unchanged.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf8")
anchor='''                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==vanilla[i],
                    "early item overwrite from repeated entry packet "+i);
                  completeTransition(player);'''
replacement='''                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==vanilla[i],
                    "early item overwrite from repeated entry packet "+i);
                  // B656: Right click MUST only open. Even after the entire
                  // 3s opening animation, all real parts stay on the stand.
                  // No timer is ever permitted to auto-equip the player.
                  for(int openTick=0;openTick<96;openTick++){
                    player.tickCount++;
                    dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                      new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  }
                  check(owned(level,base,player).size()==1,
                    "right click lost original real armor stand while opening");
                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.full(stand),
                    "right click transferred real items before player stepped in");
                  check(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),
                    "player wore power suit before physically stepping inside");
                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==vanilla[i],
                    "vanilla armor overwritten while open "+i);
                  // Now actually walk to the middle of the zero-collision
                  // open suit; only this physically triggers closing.
                  player.setPos(stand.getX(),stand.getY(),stand.getZ());
                  player.tickCount++;
                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  completeTransition(player);
                  player.tickCount++;
                  dev.obsidiannetwork.powerarmor.PowerArmorEntrySequence655.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));'''
assert s.count(anchor)==1,("B656 fixture drift",s.count(anchor))
s=s.replace(anchor,replacement,1)
assert s.count('POWER_ARMOR_REAL_ROUNDTRIP_V69')==2
assert s.count('completeExitOpening650(player,level,base);')==2
assert s.count('PowerArmorEntrySequence655.tick(')==3
assert s.count('for(int openTick=0;openTick<96;openTick++)')==1
assert 'check(stand.isRemoved(),"entered world suit still exists, tier "+tier);' in s
assert 'protection5_roundtrip=true' in s
p.write_text(s,encoding="utf8")
print("B656_GAME_TEST: wait 96 ticks WITHOUT transfer, physically step in, 80-tick closing then conserved MK1+MK2 suits")
