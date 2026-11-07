#!/usr/bin/env python3
"""B1274: exact live Backpack scroll extent, dynamic thumb and authoritative sync.

GENERIC_9x6's client has no custom DataSlots and cannot infer how many stored
item types exist from 45 visible previews. Send total result count and actual
SERVER page inside existing read-only preview metadata (never real items).
This travels in vanilla slot sync with no extra chat command or custom packet.
The server already clamps page after SEARCH and after item changes to the
maximum valid 9-item row offset. The client clamps wheel, drag and thumb to
that limit and reconciles from actual server page metadata.

B891 uses 9 entries per scroll position, 45 visible entries. The 45/9
distinction is essential: rows, not 45-item jumps. No change to clicks,
item ownership, magnet, filter settings, or stored inventory.
"""
# B1280 full NeoForge verification: placed 8-block magnet, live-scroll bounds,
# lossless high-throughput cable runtime. No throttling and no item duplication.
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
menu=root/"backpack/V176BackpackMenu.java"
screen=root/"client/V176BackpackScreen.java"
m=menu.read_text("utf-8")
s=screen.read_text("utf-8")

def once(src,old,new,label):
 n=src.count(old)
 assert n==1,("B1274_SCROLL_SOURCE_DRIFT",label,n)
 return src.replace(old,new,1)

# The 45 previews carry synthetic metadata, not actual stored item NBT.
m=once(m,
'''   tag.putLong("xsx_v176_preview_total",entry.count());''',
'''   tag.putLong("xsx_v176_preview_total",entry.count());
   // Authoritative filtered item-type count and actual 9-entry row offset.
   // Vanilla ChestMenu syncs this metadata with the first visible preview.
   // Never alter the real Stored ItemStack or cell component.
   tag.putInt("xsx_v176_scroll_total_types",resultEntries().size());
   tag.putInt("xsx_v176_scroll_page",page);''',"server live preview metadata")

# All scroll operations consult the actual server-published last row:
# ceil((types-45)/9), not arbitrary 32767.
s=once(s,
''' private int xsxScrollLimit(){return filterEditor?1:32767;}''',
''' private int xsxServerResultCount(){
  if(filterEditor)return V176BackpackCellsFallback.FILTER_SIZE;
  var preview=menu.getSlot(4).getItem();
  if(preview.isEmpty())return 0;
  var tag=preview.getOrDefault(
      net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
  return Math.max(0,tag.getIntOr("xsx_v176_scroll_total_types",0));
 }
 private int xsxScrollLimit(){
  if(filterEditor)return 1;
  // B891 pages advance by NINE entries with 45 simultaneous previews.
  int total=xsxServerResultCount();
  return Math.min(32767,Math.max(0,(total-45+8)/9));
 }
 private int xsxObservedServerPage=-1;
 private void xsxSyncServerScroll(){
  if(filterEditor)return;
  var preview=menu.getSlot(4).getItem();
  if(preview.isEmpty()){
   // Empty result set: never display or drag an obsolete scrollbar.
   if(xsxPendingScroll<0){scrollRow=0;xsxObservedServerPage=-1;}
   return;
  }
  var tag=preview.getOrDefault(
      net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
  int serverPage=Math.max(0,Math.min(xsxScrollLimit(),
      tag.getIntOr("xsx_v176_scroll_page",0)));
  if(serverPage!=xsxObservedServerPage){
   xsxObservedServerPage=serverPage;
   // Do not interrupt an optimistic local drag awaiting its next packet.
   if(xsxPendingScroll<0&&!xsxDraggingScrollbar)scrollRow=serverPage;
  }
  scrollRow=Math.max(0,Math.min(xsxScrollLimit(),scrollRow));
 }
 private int xsxThumbHeight(){
  int types=filterEditor?54:xsxServerResultCount();
  if(types<=45)return 90;
  return Math.max(16,Math.min(90,(int)Math.round(90.0D*45.0D/types)));
 }
 private int xsxThumbTop(){
  int travel=90-xsxThumbHeight(),last=xsxScrollLimit();
  return 38+(last<=0?0:(int)Math.round(((double)travel*scrollRow)/last));
 }'''.replace("V176BackpackCellsFallback.FILTER_SIZE","54"),
"client authoritative scroll range")

# This field is initialized by normal default when screen opens. No state
# change to another player's menu or server packet handler.
# Replace the existing fixed 0.5 row/pixel drag slope with the exact variable
# track travel, so dragging end->end reaches exactly the last item row.
s=once(s,
'''   xsxScrollTo(xsxDragStartRow+(int)Math.round((y-xsxDragStartY)*0.5D));''',
'''   int travel=Math.max(1,90-xsxThumbHeight());
   int last=xsxScrollLimit();
   xsxScrollTo(xsxDragStartRow+(int)Math.round(
       ((double)(y-xsxDragStartY)*last)/travel));''',"responsive drag reaches actual end")

s=once(s,
'''   int thumb=39+Math.min(73,xsxDragStartRow*3);''',
'''   int thumb=xsxThumbTop();''',"track click current thumb")

s=once(s,
'''   else if(scrollY>thumb+16)xsxScrollTo(xsxDragStartRow+5);''',
'''   else if(scrollY>thumb+xsxThumbHeight())xsxScrollTo(xsxDragStartRow+5);''',
"track click true thumb size")

# B902's actual render variable is thumbY (not thumb). B1280 failed
# closed on that exact mismatch. Match both size and coordinates only once.
pattern=r'(?m)\bint thumbY\s*=\s*y\s*\+\s*39\s*\+\s*Math\.min\(73,\s*scrollRow\s*\*\s*3\s*\)\s*;'
hits=list(re.finditer(pattern,s))
assert len(hits)==1,("B1274_THUMB_DRAW_SOURCE_DRIFT",len(hits))
s=s[:hits[0].start()]+'int thumbY=y+xsxThumbTop();'+s[hits[0].end():]
pattern2=r'(?m)\bg\.fill\(x\s*\+\s*174\s*,\s*thumbY\s*,\s*x\s*\+\s*178\s*,\s*thumbY\s*\+\s*16\s*,'
matches=list(re.finditer(pattern2,s))
assert len(matches)==1,("B1274_THUMB_SIZE_SOURCE_DRIFT",len(matches))
s=re.sub(pattern2,'g.fill(x+174,thumbY,x+178,thumbY+xsxThumbHeight(),',s,count=1)

# Every frame observes server updates, not just when scrolling.
pattern3=r'(?m)(@Override public void extractBackground\([^\n]*\)\{\s*\n\s*int x=getLeftPos\(\),y=getTopPos\(\),h=getImageHeight\(\);)'
match=re.search(pattern3,s)
assert match is not None,("B1274_RENDER_SYNC_DRIFT",s.count("void extractBackground("))
s=s[:match.end()]+ '\n  xsxSyncServerScroll();'+s[match.end():]

assert 'return Math.min(32767,Math.max(0,(total-45+8)/9));' in s
assert 'tag.getIntOr("xsx_v176_scroll_page",0)' in s
assert "xsxWheelAccumulator" in s
assert "xsxPendingScroll" in s
assert "xsxDraggingScrollbar" in s
assert "xsxThumbTop()" in s and "xsxThumbHeight()" in s
assert 'tag.putInt("xsx_v176_scroll_total_types",resultEntries().size());' in m
assert "int position=page*9+slot-4;" in m
# Match the actual B817 filter-editor-aware server page bound. Ignore
# formatting/indent only; the math and filter behavior must be exact.
normalized=re.sub(r'\s+','',m)
assert (
 "intlast=filterEditor?1:Math.max(0,(resultEntries().size()-45+8)/9);" in normalized
 or "intlast=Math.max(0,(resultEntries().size()-45+8)/9);" in normalized
 ),("B1274_SERVER_ROW_BOUNDS_DRIFT",normalized.count("resultEntries().size()-45+8"))
# Both Java files remain unchanged if any guard fails.
menu.write_text(m,"utf-8")
screen.write_text(s,"utf-8")
print("B1274_BACKPACK_LIVE_DYNAMIC_SCROLLBAR_SERVER_PAGE_RANGE_PASS")
