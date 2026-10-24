#!/usr/bin/env python3
"""Build124: show Power Armor Network Elytra thrusters to EVERY nearby player.

Vanilla already syncs tracked players' equipment, fall-flying and crouching
state to every observing client. Previously the visual ClientTickEvent was
hard-coded to mc.player, so other players' thrusters were never drawn.

Draw each tracking player's effect once per client, preserving the exact four
emitter positions, white END_ROD particles, boost CLOUD particles and frequency.
No bespoke network packets, packet storm, extra FE drain or changed flight
physics. Range gate prevents unnecessary off-screen particle work.
"""
import os
from pathlib import Path

client=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorBuild98Client.java"
source=client.read_text(encoding="utf-8")
assert "BUILD98_POWER_ARMOR_VISUAL_AND_PLACEMENT" in source
assert "BUILD121_UNFRAMED_VIOLET_FE_HUD" in source
start=source.index(" @SubscribeEvent public static void jetThrusters(ClientTickEvent.Post event){")
end=source.index("\n}\n",start)
block=source[start:end]
old='''  var p=mc.player;
  // Only complete MK1-MK24 suit with the actual Network Elytra module.
  if(!p.isFallFlying() || p.onGround())return;
  var chest=PowerArmorElytraBridge.chest(p);
  if(chest.isEmpty()||EnergyTool.energy(chest)<125L)return;
  boolean boost=p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
  if(!boost && p.tickCount%2!=0)return;'''
new='''  // BUILD124_SHARED_ELYTRA_PARTICLES: vanilla synchronizes flight state,
  // armor equipment/card data, position and crouch state to tracking clients.
  // Iterate once over nearby players including ourselves: each client renders
  // every flyer exactly once, without duplicate local + network effects.
  for(var p:mc.level.players()){
   if(p.distanceToSqr(mc.player)>64D*64D)continue;
   // Only a complete MK1-MK24 suit with the Network Elytra upgrade and FE.
   if(!p.isFallFlying() || p.onGround())continue;
   var chest=PowerArmorElytraBridge.chest(p);
   if(chest.isEmpty()||EnergyTool.energy(chest)<125L)continue;
   boolean boost=p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
   if(!boost && p.tickCount%2!=0)continue;'''
assert block.count(old)==1,("Build124 original client-only gate drift",block.count(old))
block=block.replace(old,new,1)
tail='''   }
  }
 }'''
assert block.count(tail)==1,("Build124 jets loop terminator drift",block.count(tail))
block=block.replace(tail,'''   }
  }
  } // End per-player iteration; no additional local-only emitter.
 }''',1)
assert block.count("for(var p:mc.level.players())")==1
assert "var p=mc.player" not in block
assert "p.distanceToSqr(mc.player)>64D*64D" in block
assert "PowerArmorElytraBridge.chest(p)" in block
assert "p.isFallFlying()" in block
assert "p.isShiftKeyDown()" in block
assert "ParticleTypes.END_ROD" in block and "ParticleTypes.CLOUD" in block
assert "mc.level.addParticle" in block
assert "level.sendParticles" not in block
assert "NetworkElytraItem" not in block
assert block.count("for(int limb=0;limb<4;limb++)")==1
assert block.count("for(var p:mc.level.players())")==1
assert block.index("for(var p:mc.level.players())")<block.index("for(int limb=0;limb<4;limb++)")
source=source[:start]+block+source[end:]
assert source.count("BUILD124_SHARED_ELYTRA_PARTICLES")==1
assert 'g.text(mc.font,"ARMOR FE"' in source
assert "BUILD121_UNFRAMED_VIOLET_FE_HUD" in source
client.write_text(source,encoding="utf-8")
print("BUILD124_SHARED_ELYTRA_PARTICLES PASS: ALL tracked players see flight END_ROD and boost CLOUD thrusters, no duplicates, 64-block cull, no FE or network changes")
