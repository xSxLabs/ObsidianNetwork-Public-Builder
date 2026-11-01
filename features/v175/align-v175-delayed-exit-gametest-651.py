#!/usr/bin/env python3
"""B651: preserve original MK1/MK2 GameTest duplicate/backup assertions;
simulate B650's 42 server tick staged exit before checking world suit.
The first 41 ticks assert the player STILL owns the armor. Test only.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
anchor="              @Override public void run(GameTestHelper helper){"
addon='''              // B651: exactly 42 exit preview ticks, BEFORE the atomic transfer.
              // Preserve all unchanged MK1/MK2 armor duplication and backup checks.
              private static void completeExitOpening650(
                  net.minecraft.server.level.ServerPlayer player,
                  net.minecraft.server.level.ServerLevel level,BlockPos base){
                for(int step=0;step<42;step++){
                  player.tickCount++;
                  dev.obsidiannetwork.powerarmor.PowerArmorExitSequence650.tick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
                  if(step<41){
                    check(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),
                      "player lost original armor before hatch opened at tick "+step);
                    check(owned(level,base,player).isEmpty(),
                      "premature owned world suit before opening at tick "+step);
                  }
                }
                check(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),
                  "real armor not transferred after rear hatch opened");
              }
'''
assert s.count(anchor)==1,s.count(anchor)
s=s.replace(anchor,addon+anchor,1)
a='''                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,"first exit failed, tier "+tier);
                  completeTransition(player);'''
b='''                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,"first exit failed, tier "+tier);
                  completeExitOpening650(player,level,base);
                  completeTransition(player);'''
assert s.count(a)==1,s.count(a);s=s.replace(a,b,1)
a='''                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,
                    "exit after entering failed, tier "+tier);
                  completeTransition(player);'''
b='''                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,
                    "exit after entering failed, tier "+tier);
                  completeExitOpening650(player,level,base);
                  completeTransition(player);'''
assert s.count(a)==1,s.count(a);s=s.replace(a,b,1)
assert s.count("completeExitOpening650(player,level,base);")==2
assert s.count("PowerArmorExitSequence650.tick(")==1
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
p.write_text(s,encoding="utf-8")
print("B651_TEST_ONLY_REAL_EXIT_GATE: player owns suit for first 41 ticks, transfer at 42, old MK1/MK2 checks retained")
