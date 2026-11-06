#!/usr/bin/env python3
"""B1234 Backpack scroll: smooth local wheel/thumb, bounded absolute-page packets.

One server-validated page jump per client tick at most; never send a command
per pixel, never walk five pages with five network packets.
Drag stops at true server-synced last page instead of fixed 24-row thumb.
Apply after B1230 and B1225 in the active v1.7.6 reconstruction.
"""
import os
import re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel, old, new):
    f=J/rel
    s=f.read_text(encoding="utf-8")
    assert s.count(old)==1,("B1234_SCROLL_SOURCE_DRIFT",rel,s.count(old),old[:110])
    f.write_text(s.replace(old,new,1),encoding="utf-8")

menu="backpack/V176BackpackMenu.java"
screen="client/V176BackpackScreen.java"

# Server validates every page against the current filtered live item list.
change(menu,
'''  private boolean page(int delta){
''',
'''  private int xsxMaximumPage(){
   if(!source.valid())return 0;
   if(filterEditor)return 1;
   return Math.min(32767,Math.max(0,(resultEntries().size()-45+8)/9));
  }
  private boolean page(int delta){
''')
change(menu,
''' private final Storage storage;
''',
''' private final Storage storage;
 private int xsxClientMaxPage=0;
 private int xsxClientPage=0;
 // 16-bit vanilla container data; 32767 is a conservative protocol bound.
 public int xsxMaxScrollPage(){return xsxClientMaxPage;}
 public int xsxCurrentScrollPage(){return xsxClientPage;}
''')
change(menu,
'''  this.storage=storage;
''',
'''  this.storage=storage;
  addDataSlot(new net.minecraft.world.inventory.DataSlot(){
   @Override public int get(){return storage.source.valid()?
       storage.xsxMaximumPage():xsxClientMaxPage;}
   @Override public void set(int v){xsxClientMaxPage=Math.max(0,v);}
  });
  addDataSlot(new net.minecraft.world.inventory.DataSlot(){
   @Override public int get(){return storage.source.valid()?storage.page:xsxClientPage;}
   @Override public void set(int v){xsxClientPage=Math.max(0,v);}
  });
''')
change(menu,
'''  if(action==1)return page(server,1);''',
'''  if(action==1)return page(server,1);
  // One atomic absolute jump replaces N synthetic next/previous clicks.
  // All coordinates are clamped by Storage.page() against live server data.
  if(action>=192&&action<=32959)return page(server,(action-192)-storage.page);''')

change(screen,
''' private int wheelCooldown=0;''',
''' // Client may redraw at full FPS. Send at most one absolute page per tick.
 private int xsxQueuedPage=-1;
 private long xsxLastScrollPacketTick=Long.MIN_VALUE;
 private double xsxWheelCarry=0.0D;
 private boolean xsxDraggingScrollbar=false;''')

# At most one pending navigation button per client tick, replacing a 5 tick
# delay on every click and wheel event. Release always flushes final position.
change(screen,
'''  if(wheelCooldown>0)wheelCooldown--;''',
'''  xsxFlushScroll(false);''')

change(screen,
''' private void button(int action){''',
''' private int xsxScrollMax(){
  return filterEditor?1:Math.max(0,menu.xsxMaxScrollPage());
 }
 private void xsxSetScrollRow(int target){
  int clamped=Math.max(0,Math.min(xsxScrollMax(),target));
  if(filterEditor){
   if(filterPage==clamped)return;
   filterPage=clamped;
  }else{
   if(scrollRow==clamped)return;
   scrollRow=clamped;
  }
  xsxQueuedPage=clamped;
  xsxFlushScroll(false);
 }
 private void xsxJumpFromScrollbar(double relativeY){
  int max=xsxScrollMax();
  // The thumb moves over 73 screen pixels and remains within its track.
  double p=Math.max(0.0D,Math.min(1.0D,(relativeY-47.0D)/73.0D));
  xsxSetScrollRow((int)Math.round(p*max));
 }
 private void xsxFlushScroll(boolean force){
  if(xsxQueuedPage<0)return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.player.containerMenu!=menu){
   xsxQueuedPage=-1;
   return;
  }
  long tick=mc.level.getGameTime();
  if(!force&&tick==xsxLastScrollPacketTick)return;
  xsxLastScrollPacketTick=tick;
  button(192+xsxQueuedPage);
  xsxQueuedPage=-1;
 }
 private void button(int action){''')

# Rendering references actual server-synced last page, not scrollRow*3
# which stopped moving after row 24 even for enormous cell inventories.
change(screen,
'''  int thumbY=y+39+Math.min(73,scrollRow*3);''',
'''  int maxRow=xsxScrollMax();
  int shownRow=filterEditor?filterPage:scrollRow;
  int thumbY=y+39+(maxRow<=0?0:(int)Math.round(
      73.0D*Math.min(shownRow,maxRow)/maxRow));''')

f=J/screen
src=f.read_text(encoding="utf-8")
a=src.find(" @Override public boolean mouseScrolled(")
b=src.find(" @Override protected void extractTooltip(",a)
assert a>=0 and b>a and src.count(" @Override public boolean mouseScrolled(")==1, "B1234_WHEEL_BOUNDARY_DRIFT"
wheel=''' @Override public boolean mouseScrolled(double mx,double my,double scrollX,double scrollY){
  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if(x>=8&&x<180&&y>=38&&y<129&&scrollY!=0.0D){
   // Native fractional high-resolution scroll wheels are accumulated.
   xsxWheelCarry+=scrollY;
   int rows=(int)xsxWheelCarry;
   xsxWheelCarry-=rows;
   if(rows!=0)xsxSetScrollRow((filterEditor?filterPage:scrollRow)-rows);
   return true;
  }
  return super.mouseScrolled(mx,my,scrollX,scrollY);
 }
 @Override public boolean mouseDragged(net.minecraft.client.input.MouseButtonEvent event,
      double dragX,double dragY){
  if(xsxDraggingScrollbar&&event.button()==0){
   xsxJumpFromScrollbar(event.y()-getTopPos());
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
match=re.search(pattern,src,re.DOTALL)
assert match is not None and len(match.group())<800,("B1234_CLICK_SCROLLBAR_DRIFT",src.count("scrollX>=173"))
src=src[:match.start()]+'''  if(button==0&&scrollX>=173&&scrollX<180&&scrollY>=38&&scrollY<129){
   xsxDraggingScrollbar=true;
   xsxJumpFromScrollbar(scrollY);
   return true;
  }'''+src[match.end():]
# A click away should not retain an unbounded drag state.
anchor='  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);'
assert src.count(anchor)==1
src=src.replace(anchor,'  xsxDraggingScrollbar=false;\n'+anchor,1)
assert "wheelCooldown" not in src
assert "xsxFlushScroll(false);" in src
assert "xsxDraggingScrollbar" in src
assert "xsxMaxScrollPage()" in src
f.write_text(src,encoding="utf-8")
print("B1234_BACKPACK_SCROLL_DRAG_FRACTIONAL_WHEEL_ABSOLUTE_PAGE_BOUNDED_NET_PASS")
