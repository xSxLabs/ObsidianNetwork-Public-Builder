#!/usr/bin/env python3
"""B1085: Update the world Turret aim during cooldown, not only when firing.

After B1028, the suit yaw/right-arm pose is updated only after both canSpawn
and canTurretFire return true. Keep the existing server-authoritative target
range, loaded-world and raycast checks; update rendering pose first, while the
rate/FE/bystander/projectile rules remain unchanged.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/V176CompanionMode.java"
s=p.read_text(encoding="utf-8")
original=s
cooldown="   if(!V176MicroMgRules.canSpawn(EnergyTool.energy(chest),now,last))return;\n"
assert s.count(cooldown)==1,("B1085_COOLDOWN_DRIFT",s.count(cooldown))
comment="   // Actual target orientation after line-of-sight and energy validation:"
assert s.count(comment)==1,("B1085_TURRET_AIM_ANCHOR_DRIFT",s.count(comment))
a=s.index(comment)
end=s.index("   var shot=new V176MicroMgProjectile(",a)
pose=s[a:end]
for requirement in ("suit.setYRot(xsxYaw);","suit.setYBodyRot(xsxYaw);",
                    "suit.setYHeadRot(xsxYaw);","suit.setRightArmPose("):
    assert requirement in pose,("B1085_MISSING_AIM",requirement)
# Never fire without the original FE/rate/protection gates.
assert "V176MicroMgRules.canTurretFire(" in s and "if(!world.isLoaded(enemy.blockPosition()))continue;" in s
assert "ClipContext.Block.COLLIDER" in s and "V176MicroMgRules.AUTO_TARGET_RANGE_SQ" in s
assert s.index(cooldown)<s.index("   for(Monster enemy:enemies){")<s.index(
    "   if(!V176MicroMgRules.canTurretFire(")<a
# Remove the old pose from the shot-only path.
s=s[:a]+s[end:]
s=s.replace(cooldown,"",1)
gate="   if(!V176MicroMgRules.canTurretFire("
assert s.count(gate)==1
# Aim even when on cooldown or out of FE; only shot creation remains gated.
s=s.replace(gate,pose+cooldown+gate,1)
assert s.index("if(!world.isLoaded(enemy.blockPosition()))continue;")<s.index(comment)
assert s.index("ClipContext.Block.COLLIDER")<s.index(comment)
assert s.index(comment)<s.index("if(!V176MicroMgRules.canSpawn(")<s.index(
    "if(!V176MicroMgRules.canTurretFire(")<s.index("var shot=new V176MicroMgProjectile(")
assert original.count("var shot=new V176MicroMgProjectile(")==s.count("var shot=new V176MicroMgProjectile(")==1
assert original.count("EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)")==s.count("EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)")==1
assert "if(player.getDeltaMovement().lengthSqr()>0.0025D" in s, "B1085_FOLLOW_PRIORITY_REGRESSED"
p.write_text(s,encoding="utf-8")
print("B1085_TURRET_TARGET_TRACKS_DURING_COOLDOWN_WITH_UNCHANGED_FE_PROJECTILE_GATES_PASS")
