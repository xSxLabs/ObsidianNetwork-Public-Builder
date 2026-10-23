#!/usr/bin/env python3
"""Unify Armor Station GUI and sneak-click stack caps after Build49."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor"
menu=root/"ArmorStationMenu.java"
s=menu.read_text()
old='''   case "protection","fire_protection","blast_protection",
        "projectile_protection","feather_falling" -> 5;'''
new='''   case "protection","fire_protection","blast_protection",
        "projectile_protection","feather_falling" -> 5;
   case "strength","speed","haste" -> 3;
   case "resistance","regeneration","jump_boost" -> 2;'''
assert s.count(old)==1, "Armor Station upgrade cap anchor drift"
menu.write_text(s.replace(old,new,1))
block=root/"ArmorStationBlock.java"
b=block.read_text()
assert "ArmorStationMenu.maxCardCount(card.upgradeId)" in b, "Sneak-click must use shared caps"
assert "new java.util.HashSet<>(java.util.Arrays.asList(entries)).size()>=15" in b, "Distinct-slot guard missing"
print("BUILD78_EFFECT_CAPS_PASS: station menu and sneak-click agree on potion-card levels")
