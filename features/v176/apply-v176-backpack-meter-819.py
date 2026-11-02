#!/usr/bin/env python3
"""B819: actual live Storage Cell used/total meter + Magnet state in side panel.

Reads the three synchronized real StorageCellItem stacks, at most one
snapshot/10 client ticks. No crafting widgets, no network scans, no server load.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
path=J/"client/V176BackpackScreen.java"
s=path.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("B819_SCREEN_DRIFT",s.count(old),old[:80])
 s=s.replace(old,new,1)

change(''' private boolean countSort=false;
 private boolean filterEditor=false;''',
''' private boolean countSort=false;
 private long xsxMeterTick=Long.MIN_VALUE;
 private long xsxMeterUsed=0L,xsxMeterCapacity=0L;
 private boolean filterEditor=false;''')
change('''  g.fill(sx-2,sy-2,sx+SIDE_W,sy+194,0xff4b829d);
  g.fill(sx,sy,sx+SIDE_W-2,sy+192,0xff142d3e);''',
'''  g.fill(sx-2,sy-2,sx+SIDE_W,sy+214,0xff4b829d);
  g.fill(sx,sy,sx+SIDE_W-2,sy+212,0xff142d3e);''')
change('''  g.text(font,"MODULES",187,11,0xffa7d9f0);''',
'''  // Read only the actual synchronized Cell items, never a fictional bag size.
  var world=net.minecraft.client.Minecraft.getInstance().level;
  if(world!=null){
   long now=world.getGameTime();
   if(xsxMeterTick==Long.MIN_VALUE||now<xsxMeterTick||now-xsxMeterTick>=10L){
    xsxMeterTick=now;
    xsxMeterUsed=0L;xsxMeterCapacity=0L;
    for(int slot=1;slot<=3;slot++){
     var stack=menu.getSlot(slot).getItem();
     if(stack.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem cell){
      xsxMeterUsed+=cell.readStore(stack).used();
      xsxMeterCapacity+=cell.tier().capacity();
     }
    }
   }
  }
  var magnet=menu.getSlot(0).getItem();
  var settings=magnet.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
       net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
  g.text(font,magnet.isEmpty()?"MAGNET: NONE":
      settings.getBooleanOr("xsx_v176_magnet_on",false)?"MAGNET: ON":"MAGNET: OFF",
      187,191,0xffa7efbc);
  g.text(font,settings.getBooleanOr("xsx_v176_magnet_whitelist",false)
      ?"WHITELIST":"BLACKLIST",187,202,0xffb6d4e8);
  g.text(font,compact(xsxMeterUsed)+"/"+compact(xsxMeterCapacity),
      187,213,0xffc9f6ff);
  g.text(font,"MODULES",187,11,0xffa7d9f0);''')
change(''' @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''',
''' private static String compact(long v){
  if(v>=1_000_000_000L)return v/1_000_000_000L+"G";
  if(v>=1_000_000L)return v/1_000_000L+"M";
  if(v>=1_000L)return v/1_000L+"k";
  return Long.toString(v);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''')
path.write_text(s,encoding="utf-8")
print("V176_B819_REAL_CELL_USED_TOTAL_AND_MAGNET_STATUS_SIDE_PANEL PASS")
