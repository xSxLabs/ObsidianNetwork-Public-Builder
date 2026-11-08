#!/usr/bin/env python3
"""v1.7.7: keep real server-owned sleeping state instead of flickering pose."""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/V176PowerSleepServer.java"
s=p.read_text(encoding="utf-8")
def replace_once(old,new):
 global s
 assert s.count(old)==1,("V177_SLEEP_DRIFT",old[:120],s.count(old))
 s=s.replace(old,new,1)

replace_once(
 'import net.neoforged.neoforge.event.tick.PlayerTickEvent;',
 'import net.neoforged.neoforge.event.tick.PlayerTickEvent;\n'
 'import net.neoforged.neoforge.event.entity.player.CanContinueSleepingEvent;')
replace_once(
 '   p.setPose(Pose.STANDING);',
 '   // Release Minecraft sleepingPos as well as the visual pose.\n'
 '   if(p.isSleeping())p.stopSleepInBed(true,true);\n'
 '   else p.setPose(Pose.STANDING);')
replace_once(
 '  SLEEPING.put(p,0);\n  p.setPose(Pose.SLEEPING);',
 '  SLEEPING.put(p,0);\n'
 '  // setPose alone is overwritten by vanilla pose updates every tick.\n'
 '  // startSleeping creates the actual sleepingPos / synced sleep state.\n'
 '  p.startSleeping(p.blockPosition());')
replace_once(
 '  p.setDeltaMovement(Vec3.ZERO);\n  p.setPose(Pose.SLEEPING);',
 '  p.setDeltaMovement(Vec3.ZERO);\n'
 '  if(!p.isSleeping())p.startSleeping(p.blockPosition());')
replace_once(
 ' @SubscribeEvent public static void tick(PlayerTickEvent.Post event){',
 ''' // Without a bed the default Minecraft test would wake the player each tick.
 // Only our explicit active, validated armor-sleep session is exempt.
 @SubscribeEvent public static void continueSleeping(CanContinueSleepingEvent event){
  if(event.getEntity() instanceof ServerPlayer player
      &&SLEEPING.containsKey(player)&&PowerArmorRuntime.full(player)
      &&player.level() instanceof ServerLevel w&&night(w)
      &&!hostile(player)&&player.isAlive())
   event.setContinueSleeping(true);
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post event){''')
p.write_text(s,encoding="utf-8")
print("V177_POWERARMOR_SLEEP_PERSISTENT_STATE_PATCHED")
