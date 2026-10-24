#!/usr/bin/env python3
"""Build121: clean violet Power Armor FE HUD closer to the vanilla hunger bar.

Runs AFTER Build119 and Build120. Repaints only the PowerArmorBuild98Client HUD.
There are NO changes to FE accounting, energy shield, Elytra or world suits.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorBuild98Client.java"
s=p.read_text(encoding="utf-8")
assert "BUILD119_HUNGER_ALIGNED_COMPACT_HUD" in s
assert "public static void hud(RenderGuiEvent.Post event)" in s
assert "stored+=Math.max(0L,EnergyTool.energy(item));" in s

old='''   // BUILD119_HUNGER_ALIGNED_COMPACT_HUD
   // Vanilla hunger icons occupy centered X + 10..91 and Y = height-39.
   // Keep this slim 80px meter directly ABOVE those icons, never over hearts,
   // food, experience or the armor-icon rows. All units are scaled GUI pixels.
   final int width=80;
   int x=mc.getWindow().getGuiScaledWidth()/2+10;
   int y=mc.getWindow().getGuiScaledHeight()-59;
   GuiGraphicsExtractor g=event.getGuiGraphics();
   int col=fraction<0.15?0xffdf5050:fraction<0.32?0xffe9b34e:0xff63cbea;
   g.fill(x-1,y-2,x+width+1,y+12,0x9b101923);
   g.text(mc.font,"ARMOR FE",x+2,y-1,0xffb9d6df);
   String percent=pct+"%";
   int percentWidth=mc.font.width(percent);
   g.text(mc.font,percent,x+width-percentWidth-1,y-1,col);
   g.fill(x,y+8,x+width,y+10,0xff243642);
   g.fill(x,y+8,x+(int)Math.round(width*fraction),y+10,col);'''
new='''   // BUILD121_UNFRAMED_VIOLET_FE_HUD
   // Vanilla hunger icons begin around screen height-39. The 2px FE strip
   // ends at height-42: just 3 GUI pixels above the hunger row.
   // No oversized panel, outline, or text background.
   final int width=80;
   int x=mc.getWindow().getGuiScaledWidth()/2+10;
   int y=mc.getWindow().getGuiScaledHeight()-52;
   GuiGraphicsExtractor g=event.getGuiGraphics();
   // Purple during normal operation; yellow at 10-25%, red below 10%.
   int col=fraction<0.10D?0xffff4545:fraction<0.25D?0xffffdc45:0xffbf80ff;
   g.text(mc.font,"ARMOR FE",x+2,y-1,col);
   String percent=pct+"%";
   int percentWidth=mc.font.width(percent);
   g.text(mc.font,percent,x+width-percentWidth-1,y-1,col);
   // Only a narrow unobtrusive strip remains; no surrounding dark rectangle.
   g.fill(x,y+8,x+width,y+10,0x66372a48);
   g.fill(x,y+8,x+(int)Math.round(width*fraction),y+10,col);'''

assert s.count(old)==1, ("BUILD121 HUD anchor changed",s.count(old))
s=s.replace(old,new,1)
assert s.count("BUILD121_UNFRAMED_VIOLET_FE_HUD")==1
assert "getGuiScaledWidth()/2+10" in s
assert "getGuiScaledHeight()-52" in s
assert "0xffbf80ff" in s and "0xffffdc45" in s and "0xffff4545" in s
assert "0x9b101923" not in s
assert "g.fill(x-1,y-2,x+width+1,y+12" not in s
assert s.count('g.text(mc.font,"ARMOR FE"')==1
assert "capacity+=Math.max(0L,EnergyTool.capacity(item));" in s
assert "jetThrusters(ClientTickEvent.Post event)" in s
p.write_text(s,encoding="utf-8")
print("BUILD121_UNFRAMED_VIOLET_FE_HUD PASS: borderless 80px violet FE display directly above hunger; yellow/red when low; FE/armor untouched")
