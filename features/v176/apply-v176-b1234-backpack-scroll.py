#!/usr/bin/env python3
"""B1234: responsive Backpack scrollbar, high-res mouse wheel, no chat spam.

The client opens a vanilla GENERIC_9x6 ChestMenu; DO NOT add custom menu
DataSlots or call server-only menu methods from its screen. Use an absolute
page target with the pre-existing validated container-button channel instead.
Coalesce rapid input into <=1 pending page button per client tick; never
send dozens of chat commands or repeat 5-tick cooldowns. Preserve existing
45 previews, module slot ownership, filter editor, and server-side bounds.
"""
import os
import re
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def replace(rel,old,new):
 f=root/rel
 s=f.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1234_SCROLL_DRIFT",rel,s.count(old),old[:100])
 f.write_text(s.replace(old,new,1),encoding="utf-8")

menu="backpack/V176BackpackMenu.java"
screen="client/V176BackpackScreen.java"
# Absolute-position input with server bounds. Packet Button ID is VarInt.
replace(menu,
'''  if(action==1)return page(server,1);''',
'''  if(action==1)return page(server,1);
  // One packet jumps to the final requested row, not N chat commands.
  // Storage.page() clamps against the actual filtered, live item list.
  if(action>=192&&action<=32959)
   return page(server,(action-192)-storage.page);''')

replace(screen,
''' private int wheelCooldown=0;''',
''' // Optimistic rendering at client frame rate, once-per-tick network flush.
 private int xsxPendingScroll=-1;
 private long xsxLastScrollPacketTick=Long.MIN_VALUE;
 private double xsxWheelAccumulator=0.0D;
 private boolean xsxDraggingScrollbar=false;
 private int xsxDragStartY=0;
 private int xsxDragStartRow=0;''')
replace(screen,'''  if(wheelCooldown>0)wheelCooldown--;''',
'''  xsxFlushScroll(false);''')

replace(screen,
''' private void button(int action){''',
''' private int xsxScrollLimit(){return filterEditor?1:32767;}
 private void xsxScrollTo(int target){
  int row=Math.max(0,Math.min(xsxScrollLimit(),target));
  if(filterEditor){
   if(filterPage==row)return;
   filterPage=row;
  }else{
   if(scrollRow==row)return;
   scrollRow=row;
  }
  xsxPendingScroll=row;
  xsxFlushScroll(false);
 }
 private void xsxFlushScroll(boolean force){
  if(xsxPendingScroll<0)return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.player.containerMenu!=menu){
   xsxPendingScroll=-1;
   return;
  }
  long tick=mc.level.getGameTime();
  if(!force&&tick==xsxLastScrollPacketTick)return;
  xsxLastScrollPacketTick=tick;
  button(192+xsxPendingScroll);
  xsxPendingScroll=-1;
 }
 private void button(int action){''')

f=root/screen
src=f.read_text(encoding="utf-8")
a=src.find(" @Override public boolean mouseScrolled(")
b=src.find(" @Override protected void extractTooltip(",a)
assert a>=0 and b>a and src.count(" @Override public boolean mouseScrolled(")==1,"B1234_WHEEL_BOUNDARY"
wheel=''' @Override public boolean mouseScrolled(double mx,double my,double scrollX,double scrollY){
  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if(x>=8&&x<180&&y>=38&&y<129&&scrollY!=0.0D){
   xsxWheelAccumulator+=scrollY;
   int rows=(int)xsxWheelAccumulator;
   xsxWheelAccumulator-=rows;
   if(rows!=0)xsxScrollTo((filterEditor?filterPage:scrollRow)-rows);
   return true;
  }
  return super.mouseScrolled(mx,my,scrollX,scrollY);
 }
 @Override public boolean mouseDragged(net.minecraft.client.input.MouseButtonEvent event,
      double dragX,double dragY){
  if(xsxDraggingScrollbar&&event.button()==0){
   int y=(int)event.y()-getTopPos();
   // Each two cursor pixels moves a real 9-item row. Drag can be repeated
   // for inventories with >24 rows; no hard capped item count.
   xsxScrollTo(xsxDragStartRow+(int)Math.round((y-xsxDragStartY)*0.5D));
   return true;
  }
  return super.mouseDragged(event,dragX,dragY);
 }
 @Override public boolean mouseReleased(net.minecraft.client.input.MouseButtonEvent event){
  if(xsxDraggingScrollbar&&event.button()==0){
   xsxDraggingScrollbar=false;
   xsxFlushScroll(true);
   return true;
  }
  return super.mouseReleased(event);
 }
'''
src=src[:a]+wheel+src[b:]

pattern=r'  if\(button==0&&scrollX>=173&&scrollX<180&&scrollY>=38&&scrollY<129\)\{\s*int delta=.*?\n   return true;\n  \}'
m=re.search(pattern,src,re.DOTALL)
assert m is not None and len(m.group())<800,("B1234_SCROLLBAR_CLICK_DRIFT",src.count("scrollX>=173"))
src=src[:m.start()]+'''  if(button==0&&scrollX>=173&&scrollX<180&&scrollY>=38&&scrollY<129){
   xsxDraggingScrollbar=true;
   xsxDragStartY=scrollY;
   xsxDragStartRow=filterEditor?filterPage:scrollRow;
   int thumb=39+Math.min(73,xsxDragStartRow*3);
   // Track-click moves by 5 rows, drag remains per-pixel responsive.
   if(scrollY<thumb)xsxScrollTo(xsxDragStartRow-5);
   else if(scrollY>thumb+16)xsxScrollTo(xsxDragStartRow+5);
   return true;
  }'''+src[m.end():]
anchor='  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);'
assert src.count(anchor)==1
src=src.replace(anchor,'  xsxDraggingScrollbar=false;\n'+anchor,1)
assert "wheelCooldown" not in src
assert "xsxFlushScroll(false);" in src
assert "xsxDraggingScrollbar" in src
assert "192+xsxPendingScroll" in src
assert "sendCommand(" not in src[src.index(" @Override public boolean mouseScrolled("):src.index(" @Override protected void extractTooltip(")]
f.write_text(src,encoding="utf-8")
print("B1234_BACKPACK_SCROLL_PER_PIXEL_WHEEL_COALESCE_NO_COMMAND_SPAM_PASS")
