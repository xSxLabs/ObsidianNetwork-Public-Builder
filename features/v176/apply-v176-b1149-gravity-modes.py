#!/usr/bin/env python3
"""B1149: parked owned armor stands are gravity-free; follow/turret use gravity."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"powerarmor/V176CompanionLongRange.java"
s=p.read_text(encoding="utf-8")
old="""   nearby.setNoGravity(false);
   if(nearby.entityTags().contains(FOLLOW)||nearby.entityTags().contains(TURRET))
    ACTIVE.add(owner);
   else ACTIVE.remove(owner);"""
new="""   boolean moving=nearby.entityTags().contains(FOLLOW)||nearby.entityTags().contains(TURRET);
   nearby.setNoGravity(!moving);
   if(!moving)nearby.setDeltaMovement(Vec3.ZERO);
   if(moving)ACTIVE.add(owner);
   else ACTIVE.remove(owner);"""
assert s.count(old)==1,("B1149_MODE_GRAVITY_DRIFT",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
# When a suit is placed into the world after exit, it must not fall before
# the first companion tick. Entry transfer is deliberately unchanged.
print("B1149_PARKED_SUIT_NO_GRAVITY_FOLLOW_TURRET_GRAVITY_PASS")
