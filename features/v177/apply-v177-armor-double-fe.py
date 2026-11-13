#!/usr/bin/env python3
"""Double the existing 1.7.7 Power Armor FE capacity again (4M base -> 16M); retain other EnergyTool users."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/core/EnergyTool.java"
s=p.read_text(encoding="utf-8")
old="public static long capacity(ItemStack s){return Math.max(1,s.getMaxDamage());}"
new="""public static long capacity(ItemStack s){
 long base=Math.max(1L,(long)s.getMaxDamage());
 return s.getItem() instanceof dev.obsidiannetwork.powerarmor.PowerArmorItem
     ? Math.min(Long.MAX_VALUE/4L,base)*4L : base;
}"""
assert s.count(old)==1,("V177_ARMOR_DOUBLE_FE_CAPACITY_DRIFT",s.count(old))
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("V177_POWER_ARMOR_FE_CAPACITY_X4_BASE_16M_ONLY_PASS")
