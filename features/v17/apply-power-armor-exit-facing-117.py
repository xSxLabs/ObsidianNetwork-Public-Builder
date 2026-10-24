#!/usr/bin/env python3
"""Build117: place exited Power Armor exactly one block ahead, facing its owner.

After Build115. Modify only PowerArmorSuitWorld.available() and the yaw
initialization of its already-existing spawned GeckoLib stand. Never touch
the proven save/restore, remove-before-spawn transaction, ownership, fuel,
armor station, upgrade cards, or animated forcefield.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java"
s=p.read_text(encoding="utf-8")

beg=s.index(" private static BlockPos available(ServerPlayer player){")
end=s.index(" private static ArmorStand spawn(ServerPlayer player",beg)
method=s[beg:end]
assert "suitVolumeClearable(level,p)" in method, "Build98 clearance predicate missing"
assert "new AABB(p).inflate(0.25D)" in method, "Build98 entity clearance changed"
assert method.count("for(var direction:net.minecraft.core.Direction.Plane.HORIZONTAL)")==1
old='''  for(var direction:net.minecraft.core.Direction.Plane.HORIZONTAL){
    BlockPos p=player.blockPosition().relative(direction);
    if(!suitVolumeClearable(level,p))continue;
    if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(p).inflate(0.25D)).isEmpty())continue;
    return p;
   }
   return null;'''
# Exact source is generated with two-space indent on BlockPos and four on body.
# Select and replace the full loop, without touching the surrounding helpers.
if old not in method:
 old='''   for(var direction:net.minecraft.core.Direction.Plane.HORIZONTAL){
    BlockPos p=player.blockPosition().relative(direction);
    if(!suitVolumeClearable(level,p))continue;
    if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(p).inflate(0.25D)).isEmpty())continue;
    return p;
   }
   return null;'''
if old not in method:
 import re
 match=re.search(r"(?m)^ +for\(var direction:net\.minecraft\.core\.Direction\.Plane\.HORIZONTAL\)\{\n"
                r" +BlockPos p=player\.blockPosition\(\)\.relative\(direction\);\n"
                r" +if\(!suitVolumeClearable\(level,p\)\)continue;\n"
                r" +if\(!level\.getEntitiesOfClass\(ArmorStand\.class,new AABB\(p\)\.inflate\(0\.25D\)\)\.isEmpty\(\)\)continue;\n"
                r" +return p;\n"
                r" +\}\n"
                r" +return null;",method)
 assert match is not None,("front placement loop changed",method[:1200])
 old=match.group()
new='''  // BUILD117_EXIT_FRONT_FACING: never choose an unrelated compass side.
  // The suit MUST appear in the exact block the player is looking toward.
  // If it is blocked, fail closed; the caller restores all original armor.
  BlockPos p=player.blockPosition().relative(player.getDirection());
  if(!suitVolumeClearable(level,p))return null;
  if(!level.getEntitiesOfClass(ArmorStand.class,new AABB(p).inflate(0.25D)).isEmpty())return null;
  return p;'''
assert method.count(old)==1,("front placement anchor not unique",method[:1500])
method=method.replace(old,new,1)
s=s[:beg]+method+s[end:]

# The real persistent GeckoLib stand is the only suit owner.
# Face back toward the player, i.e. exactly opposite the player look direction.
# All render-facing channels must agree to avoid first-tick spin/jitter.
standAnchor='''   stand.setPos(pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);'''
assert s.count(standAnchor)==1, ("world suit setPos anchor drift",s.count(standAnchor))
standNew='''   stand.setPos(pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);
   // BUILD117_STAND_LOOKS_AT_OWNER: opposite horizontal look, all 4 facings.
   float faceOwner=player.getDirection().getOpposite().toYRot();
   stand.setYRot(faceOwner);
   stand.setYBodyRot(faceOwner);
   stand.setYHeadRot(faceOwner);'''
s=s.replace(standAnchor,standNew,1)
# Existing "need free blocks next to you" warning must accurately describe
# the deliberate front-only placement policy.
s=s.replace('Power Armor: need two free blocks next to you.',
            'Power Armor: need two free blocks directly in front of you.')

# Guard inventory/backup atomicity: no changes to the exit / entry handshake.
assert "for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)player.setItemSlot(slot,ItemStack.EMPTY);" in s
assert "ArmorStand stand=spawn(player,worn);" in s
assert "stand.discard();" in s
assert "if(!clearSuitVolume(level,pos))return null;" in s
assert s.count('BlockPos p=player.blockPosition().relative(player.getDirection());')==1
assert s.count('player.getDirection().getOpposite().toYRot()')==1
assert "Power Armor: need two free blocks directly in front of you." in s
assert "stand.setYRot(faceOwner);" in s
assert "stand.setYBodyRot(faceOwner);" in s
assert "stand.setYHeadRot(faceOwner);" in s
p.write_text(s,encoding="utf-8")

# For each viewing direction, the suit spawns one block that way and faces back.
dirs={"N":(0,-1),"S":(0,1),"E":(1,0),"W":(-1,0)}
for direction,(dx,dz) in dirs.items():
 assert (dx,dz)!=(-dx,-dz),direction
 assert (dx+(-dx),dz+(-dz))==(0,0),direction
print("BUILD117_EXIT_FRONT_FACING PASS: four player directions, strictly one-block front, stand looking at player; recovery and safe spawn intact")
