#!/usr/bin/env python3
"""Build119: compact Power Armor energy HUD above the vanilla hunger bar.

After Build98 HUD creation and all previous Build118 overlays, replace only
the positioning and painting of the FE percentage. All gameplay, FE balances,
armor station, forcefield, and first-person textures remain exactly as before.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorBuild98Client.java"
source=p.read_text(encoding="utf-8")
assert "BUILD98_POWER_ARMOR_VISUAL_AND_PLACEMENT" in source
assert "public static void hud(RenderGuiEvent.Post event)" in source
assert "capacity+=Math.max(0L,EnergyTool.capacity(item));" in source
old='''   int x=mc.getWindow().getGuiScaledWidth()/2-91;
   int y=mc.getWindow().getGuiScaledHeight()-70;
   GuiGraphicsExtractor g=event.getGuiGraphics();
   int col=fraction<0.15?0xffdf5050:fraction<0.32?0xffe9b34e:0xff63cbea;
   g.fill(x-1,y-2,x+91,y+10,0x9b101923);
   g.fill(x,y+5,x+90,y+8,0xff243642);
   g.fill(x,y+5,x+(int)Math.round(90*fraction),y+8,col);
   g.text(mc.font,"POWER ARMOR",x,y-5,0xffb9d6df);
   g.text(mc.font,pct+"%",x+72,y-5,col);'''
new='''   // BUILD119_HUNGER_ALIGNED_COMPACT_HUD
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
assert source.count(old)==1, ("Build98 HUD block drift",source.count(old))
source=source.replace(old,new,1)
assert source.count("BUILD119_HUNGER_ALIGNED_COMPACT_HUD")==1
assert "getGuiScaledWidth()/2+10" in source
assert "getGuiScaledHeight()-59" in source
assert "final int width=80;" in source
assert "mc.font.width(percent)" in source
assert 'g.text(mc.font,"ARMOR FE"' in source
assert 'stored+=Math.max(0L,EnergyTool.energy(item));' in source
assert "jetThrusters(ClientTickEvent.Post event)" in source
assert "renderArm" not in source
p.write_text(source,encoding="utf-8")
print("BUILD119_HUNGER_ALIGNED_COMPACT_HUD PASS: 80px FE bar above hunger, text right-aligned, all armor and FE logic unchanged")
