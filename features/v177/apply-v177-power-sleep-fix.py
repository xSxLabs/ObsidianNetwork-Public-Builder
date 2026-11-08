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
# Minecraft 26.1 stores gamerules as typed GameRule<Integer> values.
# Mirror the vanilla percentage rounding and count real bed sleepers together
# with armor sleepers; NEVER require everyone in SLEEPING.
replace_once(
 'import net.minecraft.world.entity.Pose;',
 'import net.minecraft.world.entity.Pose;\n'
 'import net.minecraft.world.level.gamerules.GameRules;')
replace_once(
 '''  for(ServerPlayer other:world.players()){
   if(other.isAlive()&&!other.isSpectator()&&!SLEEPING.containsKey(other))
    return; // never skip another player's night without their consent
  }''',
 '''  // Vanilla-style percentage: ceil(eligible * percentage / 100), minimum 1.
  // 0% means one sleeper, 1% with up to 100 players means one sleeper,
  // 100% means everyone, and values >100 cannot pass the night.
  // Count real bed sleepers AND players resting in Power Armor.
  int percentage=world.getGameRules().get(GameRules.PLAYERS_SLEEPING_PERCENTAGE);
  int eligible=0,sleepers=0;
  for(ServerPlayer other:world.players()){
   if(!other.isAlive()||other.isSpectator())continue;
   eligible++;
   if(other.isSleeping()||SLEEPING.containsKey(other))sleepers++;
  }
  long needed=Math.max(1L,(eligible*(long)percentage+99L)/100L);
  if(sleepers<needed)return;''')
p.write_text(s,encoding="utf-8")
print("V177_POWERARMOR_SLEEP_GAMERULE_PERCENTAGE_AND_BED_SLEEPERS_PATCHED")
