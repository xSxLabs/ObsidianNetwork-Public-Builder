#!/usr/bin/env python3
"""B537: user-requested bottom-left Power Armor FE and NutriPaste HUD.

Both meters use the same screen-edge anchor, independent of hotbar, armor
icons, health, hunger and Minecraft GUI scale. Keep existing energy/paste
accounting and percent calculations; move/render ONLY the HUD geometry.
Run after B533 NutriPaste injection and B119 compact Power Armor HUD.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorBuild98Client.java"
s=p.read_text(encoding="utf-8")
assert "BUILD119_HUNGER_ALIGNED_COMPACT_HUD" in s, "B537_MISSING_VANILLA_FE_HUD"
assert "B533_NUTRIPASTE_ARMOR_ROW" in s, "B537_MISSING_NUTRIPASTE_HUD"
assert "B537_HUD_BOTTOM_LEFT_FE" not in s, "B537_ALREADY_APPLIED"

def replace(old,new):
 global s
 count=s.count(old)
 assert count==1, ("B537_HUD_POSITION_SOURCE_DRIFT",old,count)
 s=s.replace(old,new,1)

# Tiny stacked meters, above the extreme bottom edge to leave room for
# hotbar/experience/chat's input line. Left x=8 means "screen corner" at
# every resolution (rather than relative to screen center).
replace("int x=mc.getWindow().getGuiScaledWidth()/2+10;",
        "int x=8; // B537_HUD_BOTTOM_LEFT_FE")
replace("int y=mc.getWindow().getGuiScaledHeight()-59;",
        "int y=mc.getWindow().getGuiScaledHeight()-61;")
# Remove the opaque-looking backing rectangle, leaving text + narrow FE bar.
replace("g.fill(x-1,y-2,x+width+1,y+12,0x9b101923);",
        "// B537_NO_OPAQUE_FE_PANEL: transparent background, only meter line")
# The paste line sits ABOVE the FE line, not the vanilla armor icons.
replace("int pasteWidth=70,px=mc.getWindow().getGuiScaledWidth()/2-91;",
        "int pasteWidth=80,px=8; // B537_HUD_BOTTOM_LEFT_PASTE")
replace("int py=mc.getWindow().getGuiScaledHeight()-66;",
        "int py=mc.getWindow().getGuiScaledHeight()-85;")
assert "int x=8;" in s and "int pasteWidth=80,px=8;" in s
assert "getGuiScaledHeight()-61" in s and "getGuiScaledHeight()-85" in s
assert 'g.text(mc.font,"ARMOR FE"' in s
assert 'String pasteLabel="PASTE "+pastePct+"%";' in s
assert 'g.fill(px,py+10,px+pasteWidth,py+12,0x88435855);' in s
assert "0x9b101923" not in s
p.write_text(s,encoding="utf-8")
print("B537_BOTTOM_LEFT_STACKED_TRANSPARENT_POWER_ARMOR_FE_AND_NUTRIPASTE_PASS")
