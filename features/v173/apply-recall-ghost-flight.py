#!/usr/bin/env python3
"""Build174: damage-free recall flight can phase through any solid blocks.

The *source* ArmorStand and its item stacks remain at the original location
until safe arrival. Collision is still checked when choosing the START
position so there is no unsafe initial entity spawn; movement is ghostlike.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorRecall.java"
s=p.read_text(encoding="utf-8")
old='''    visual.setNoGravity(true);
    visual.begin(false);'''
new='''    // V173_RECALL_GHOST_FLIGHT174: only the disposable display phases.
    // No physical collisions, armor damage, knockback or terrain destruction.
    // The actual owned suit remains completely untouched at its origin.
    visual.setNoGravity(true);
    visual.noPhysics=true;
    visual.setInvulnerable(true);
    visual.begin(false);'''
assert s.count(old)==1,("visual creation changed",s.count(old))
s=s.replace(old,new,1)
old='''   if(!player.level().hasChunkAt(BlockPos.containing(next))
       ||!player.level().noCollision(visual,visual.getBoundingBox().move(move))){
    abort(player,f,"flight path blocked or chunk unloaded.");return;
   }
   visual.setPos(next.x,next.y,next.z);'''
new='''   // V173_RECALL_GHOST_FLIGHT174: never block on walls, roofs or ceilings.
   // setPos does not physically move blocks or collide with other entities.
   // Check ONLY chunk load availability; original armor stays as a backup.
   if(!player.level().hasChunkAt(BlockPos.containing(next))){
    abort(player,f,"flight chunk unloaded.");return;
   }
   visual.setPos(next.x,next.y,next.z);'''
assert s.count(old)==1,("flight block guard changed",s.count(old))
s=s.replace(old,new,1)
# Reassert invulnerability during flight even after a save/restart anomaly.
old='''   Vec3 delta=player.position().subtract(visual.position());'''
new='''   visual.noPhysics=true;
   visual.setInvulnerable(true);
   Vec3 delta=player.position().subtract(visual.position());'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("V173_RECALL_GHOST_FLIGHT174_PASS: no block collision, invulnerable, existing source backup safe")
