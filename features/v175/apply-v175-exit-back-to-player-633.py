#!/usr/bin/env python3
"""B633/v1.7.5: after unequip, place the free-standing armor with its BACK to the
player, still exactly one block directly ahead. Do not change item ownership,
normal enter/exit choreography, recall, visual rigs or the frozen v1.7.4 branch.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java"
s = p.read_text(encoding="utf-8")
old = "   // BUILD117_STAND_LOOKS_AT_OWNER: opposite horizontal look, all 4 facings.\n   float faceOwner=player.getDirection().getOpposite().toYRot();\n   stand.setYRot(faceOwner);\n   stand.setYBodyRot(faceOwner);\n   stand.setYHeadRot(faceOwner);"
new = "   // V175_B633_EXIT_BACK_TO_PLAYER: keep front-block placement, turn\n   // the entire standing suit AWAY from the player (back toward wearer).\n   // All three yaw channels stay synchronized: no animation snap/jitter.\n   float faceAway=player.getDirection().toYRot();\n   stand.setYRot(faceAway);\n   stand.setYBodyRot(faceAway);\n   stand.setYHeadRot(faceAway);"
assert s.count(old) == 1, ("B633_STAND_YAW_ANCHOR_DRIFT", s.count(old))
assert "BUILD117_EXIT_FRONT_FACING" in s
assert s.count("BlockPos p=player.blockPosition().relative(player.getDirection());") == 1
assert "if(!clearSuitVolume(level,pos))return null;" in s
assert "ArmorStand stand=spawn(player,worn);" in s
assert "for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)" in s
assert "stand.discard();" in s

result = s.replace(old, new, 1)
assert "player.getDirection().getOpposite().toYRot()" not in result
assert result.count("player.getDirection().toYRot()") == 1
assert "stand.setYRot(faceAway);" in result
assert "stand.setYBodyRot(faceAway);" in result
assert "stand.setYHeadRot(faceAway);" in result
p.write_text(result, encoding="utf-8")
print("V175_B633_EXIT_BACK_TO_PLAYER_PASS: one block ahead; back to player; all 4 directions; armor transfer/recall unchanged")
