#!/usr/bin/env python3
"""B636: align CI-only MK1/MK2 item roundtrip to B634's 48-tick normal animation.

The legacy Build69 test simulates exactly 20 PlayerTickEvents and then requires
the persistent, item-owning stand to be visible. Normal hatch/faceplate motion
now takes 48 ticks, so that check was testing an intentionally hidden owner
mid-animation. Change ONLY the temporary headless GameTest fixture.
No shipped runtime, textures, recall, armor inventory or source are modified.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
assert world.count("new Animation(stand,48,entering,")==3,"B636 normal duration drift"
assert "int t=49-animation.ticks();" in world,"B636 animation phase drift"
assert "V175_B633_EXIT_BACK_TO_PLAYER" in world,"B636 B633 exit orientation missing"

p=J/"build103/Build103GameTests.java"
before=p.read_text(encoding="utf-8")
old="""              private static void completeTransition(net.minecraft.server.level.ServerPlayer player){
                for(int i=0;i<20;i++)
                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.transitionTick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
              }"""
new="""              // V175_B636_48_TICK_ROUNDTRIP: simulate the complete, real 48-tick
              // opening/closing lifecycle BEFORE asserting restored visibility
              // and transferring the exact four original item stacks.
              private static void completeTransition(net.minecraft.server.level.ServerPlayer player){
                for(int i=0;i<48;i++)
                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.transitionTick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
              }"""
assert before.count(old)==1,("B636 Build69 fixture drift",before.count(old))
assert before.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
assert "check(!stand.isInvisible(),\"exited suit is invisible, tier \"+tier);" in before
after=before.replace(old,new,1)
assert after.count("V175_B636_48_TICK_ROUNDTRIP")==1
assert len(after)-len(before)==len(new)-len(old)
p.write_text(after,encoding="utf-8")
print("V175_B636_48_TICK_ROUNDTRIP_PASS: real 48-tick opening and closing completed before world-suit visibility/duplication tests")
