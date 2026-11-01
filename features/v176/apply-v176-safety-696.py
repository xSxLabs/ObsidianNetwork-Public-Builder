#!/usr/bin/env python3
"""v1.7.6 B696: projectile bystander safety, suit targeting and mode cleanup.

Runs only after the existing B676 FE/projectile/companion overlays.
No change to Recall, entry/exit, variant textures or old armor stations.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel, before, after):
    path=J/rel
    src=path.read_text(encoding="utf-8")
    assert src.count(before)==1, ("V176_B696_SOURCE_DRIFT",rel,src.count(before),before[:90])
    path.write_text(src.replace(before,after,1),encoding="utf-8")

# A real nearby suit must have BOTH the dedicated marker and exact owner tag.
# Vanilla armor stands belonging to others must never hijack the radial wheel.
edit("client/V176CompanionClient.java",
 '''    new AABB(mc.player.blockPosition()).inflate(16.0D),s->{
      int tier=PowerArmorRuntime.tier(s.getItemBySlot(EquipmentSlot.HEAD),0);''',
 '''    new AABB(mc.player.blockPosition()).inflate(16.0D),s->{
      if(!s.entityTags().contains("xsxlabs_power_armor_suit_v17") ||
         !s.entityTags().contains("xsxlabs_power_armor_owner_"+mc.player.getUUID()))return false;
      int tier=PowerArmorRuntime.tier(s.getItemBySlot(EquipmentSlot.HEAD),0);''')

# Projectiles are physically simulated, and can pass a player/pet before reaching
# a targeted monster. Never deal auto-turret damage to that bystander.
edit("powerarmor/V176MicroMgProjectile.java",
 '''      &&!(target instanceof Player && !(owner instanceof Player))){
    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);''',
 '''      &&!(target instanceof Player && !(owner instanceof Player))
      &&(!entityTags().contains("xsxlabs_v176_automatic_bullet")
         ||(target instanceof net.minecraft.world.entity.monster.Monster
            &&!target.isAlliedTo(owner)))){
    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);''')
edit("powerarmor/V176MicroMgProjectile.java",
 'if(!level().isClientSide()&&tickCount>12)discard(); // never unbounded',
 'if(!level().isClientSide()&&tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks')

# The turret's shot is explicitly marked, even when the shooter is a Player.
edit("powerarmor/V176CompanionMode.java",
 '   shot.setOwner(player);\n   shot.setPos(start.x,start.y,start.z);',
 '   shot.setOwner(player);\n   shot.addTag("xsxlabs_v176_automatic_bullet");\n   shot.setPos(start.x,start.y,start.z);')

# Cooldown must recover on a dimension/time discontinuity, not lock forever.
edit("powerarmor/V176MicroMgFire.java",
 '  long previous=LAST.getOrDefault(p.getUUID(),-1L);',
 '  long previous=LAST.getOrDefault(p.getUUID(),-1L);\n  if(previous>now)previous=-1L;')
edit("powerarmor/V176CompanionMode.java",
 '  long now=world.getGameTime(),last=LAST_SHOT.getOrDefault(suit,-1L);',
 '  long now=world.getGameTime(),last=LAST_SHOT.getOrDefault(suit,-1L);\n  if(last>now)last=-1L;')

# Keep actionbar *event only* for Follow and Turret. Do not add heartbeat.
assert '" Mode: "+(was?"OFF":"ON")' in (J/"powerarmor/V176CompanionMode.java").read_text()
assert "display(player," in (J/"powerarmor/V176CompanionMode.java").read_text()
print("V176_B696_PROJECTILE_BYSTANDER_AND_OWNER_FILTER_PASS")
