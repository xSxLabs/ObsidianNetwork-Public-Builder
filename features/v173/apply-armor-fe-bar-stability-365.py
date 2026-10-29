#!/usr/bin/env python3
"""Build365: stop 13-pixel red armor/tool FE bars flickering at full charge.

Private v1.0.7's EnergyTool.barWidth used integer truncation:
(13 * energy) / capacity. Any one-FE debit from a full charge turned 13 into
12, so wireless topping up and armor consuming even tiny amounts caused a
1px 13<->12 flash on every charge tick.

Round to NEAREST rendered pixel instead. This is only item decoration; the
authoritative FE amount, charging, drains, capacity, tooltip and other FE
users remain precise and untouched. Runs after all earlier energy patches.
"""
import os
from pathlib import Path

src = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/core/EnergyTool.java"
code = src.read_text(encoding="utf-8")

old = (
 "public static int barWidth(ItemStack s){return "
 "(int)Math.max(0L,Math.min(13L,(13L*energy(s))/capacity(s)));}"
)
new = (
 "// V173_B365_STABLE_ARMOR_FE_BAR: nearest visible pixel, not truncation.\n"
 " // Small energy drains from full charge must NOT cause 13->12->13 flicker.\n"
 " public static int barWidth(ItemStack s){return "
 "(int)Math.max(0L,Math.min(13L,"
 "Math.round(13.0D*energy(s)/(double)capacity(s))));}"
)
assert code.count(old) == 1, ("B365_FE_BAR_SOURCE_DRIFT", code.count(old))
assert "public static int barColor(ItemStack s)" in code
assert "public static long energy(ItemStack s)" in code
assert "public static void setEnergy(ItemStack s,long v)" in code
src.write_text(code.replace(old, new, 1), encoding="utf-8")

assert "V173_B365_STABLE_ARMOR_FE_BAR" in src.read_text(encoding="utf-8")
assert old not in src.read_text(encoding="utf-8")
print("V173_B365_STABLE_RED_13PX_FE_DECORATION_PASS")
