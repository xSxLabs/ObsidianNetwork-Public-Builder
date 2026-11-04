#!/usr/bin/env python3
"""B1091: aim an autonomous turret before firing authorization and cooldown.

The weapon's pose must track its selected visible target every check, even
if FE/cooldown rules reject a shot. Keep target visibility, ownership, all
existing capability/FE transactions, the projectile and shot gate unchanged.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/V176CompanionMode.java"
s=p.read_text(encoding="utf-8")
original=s
comment="// Actual target orientation after line-of-sight and energy validation:"
shot="var shot=new V176MicroMgProjectile("
gate="if(!V176MicroMgRules.canTurretFire("
assert s.count(comment)==1,("B1091_TURRET_POSE_DRIFT",s.count(comment))
assert s.count(shot)==1 and s.count(gate)==1,("B1091_SHOT_GATE_DRIFT",s.count(shot),s.count(gate))
assert s.index(gate)<s.index(comment)<s.index(shot)
a=s.rfind("\n",0,s.index(comment))+1
b=s.rfind("\n",0,s.index(shot))+1
pose=s[a:b]
for invariant in ("suit.setYRot(xsxYaw);","suit.setYBodyRot(xsxYaw);",
                  "suit.setYHeadRot(xsxYaw);","suit.setRightArmPose("):
    assert invariant in pose,("B1091_POSE_PART_MISSING",invariant)
assert "if(!world.isLoaded(enemy.blockPosition()))continue;" in original
assert "ClipContext.Block.COLLIDER" in original
assert "V176MicroMgRules.AUTO_TARGET_RANGE_SQ" in original
assert original.index("ClipContext.Block.COLLIDER")<original.index(gate)
assert original.count("EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)")==1

# Remove pose from the old shot-only location.
s=s[:a]+s[b:]
# The old cooldown guard may be formatted differently by B729/B757.
# Move exactly the existing one-line return guard if present; do NOT
# duplicate it, synthesize one, or weaken the authoritative canTurretFire.
cooldown_needle="V176MicroMgRules.canSpawn("
found=s.count(cooldown_needle)
assert found<=1,("B1091_MULTIPLE_RATE_GATES",found)
cooldown=""
if found:
    at=s.index(cooldown_needle)
    lo=s.rfind("\n",0,at)+1
    hi=s.find("\n",at)
    if hi<0:hi=len(s)
    else:hi+=1
    cooldown=s[lo:hi]
    assert "if" in cooldown and "return;" in cooldown and cooldown.endswith("\n"),(
        "B1091_COOLDOWN_NOT_SIMPLE_GUARD",cooldown_needle)
    assert lo<s.index("for(Monster enemy:enemies){"),(
        "B1091_COOLDOWN_NOT_EARLY")
    s=s[:lo]+s[hi:]
# The target raycast must be passed before either rate guard.
gate_at=s.index(gate)
gate_line=s.rfind("\n",0,gate_at)+1
assert s.index("ClipContext.Block.COLLIDER")<gate_line
s=s[:gate_line]+pose+cooldown+s[gate_line:]

assert s.index(comment)<s.index(gate)<s.index(shot)
assert s.index("ClipContext.Block.COLLIDER")<s.index(comment)
if cooldown:
    assert s.index(comment)<s.index(cooldown_needle)<s.index(gate)
assert s.count(gate)==original.count(gate)==1
assert s.count(shot)==original.count(shot)==1
assert s.count(cooldown_needle)==original.count(cooldown_needle)
assert s.count("EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)")==1
assert "if(player.getDeltaMovement().lengthSqr()>0.0025D" in s
p.write_text(s,encoding="utf-8")
print("B1091_TURRET_LIVE_POSE_BEFORE_COOLDOWN_AND_SHOT_GATES_PASS")
