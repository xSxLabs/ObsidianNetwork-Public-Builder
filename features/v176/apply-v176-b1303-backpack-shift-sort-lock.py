#!/usr/bin/env python3
"""B1303: Shift freezes the Backpack's live sorted item layout, like Terminal.

The B1302 selected sort mode (COUNT descending / item A-Z) remains stored
per-backpack. On Shift down, snapshot the SERVER's current filtered entries;
while Shift is held, all preview slots AND item clicks use that same snapshot,
even when items are added/removed. On release, restore live authoritative
sorting and clamp scroll. Does NOT freeze actual Storage Cells or transactions.

Client changes send exactly one native menu-button action on key transition,
with no chat/commands, no per-tick network spam and no new custom packets.
New request ids 32960 and 32961 are outside B1234 page ids 192..32959.
All existing shift+drag withdrawal, item cursor/CAS, magnet, filtering and
the persistent countSort mode remain unchanged.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
menu=root/"backpack/V176BackpackMenu.java"
screen=root/"client/V176BackpackScreen.java"
m=menu.read_text(encoding="utf-8")
s=screen.read_text(encoding="utf-8")

def once(src,old,new,label):
 n=src.count(old)
 assert n==1,("B1303_SOURCE_DRIFT",label,n,old[:170])
 return src.replace(old,new,1)

for required in (
 "B1302_SORT_RESTORED",
 "B1302_SORT_SAVE_CAS",
 'tag.putBoolean("xsx_v176_backpack_sort_count",requested)',
 "private java.util.List<V176BackpackCells.Entry> resultEntries()",
 "private boolean countSort=false;",
 "if(!source.valid())return java.util.List.of();",
 "java.util.List.copyOf(result)",
 "private boolean page(int delta)",
 "if(action==2)return sort(server);",
 "if(action>=192&&action<=32959)",
 "tag.putLong(\"xsx_v176_preview_total\",entry.count());",
 "tag.putInt(\"xsx_v176_scroll_page\",page);",
 "int position=page*9+slot-4",
):
 assert required in m,("B1303_MENU_EXPECTED_DRIFT",required)
for required in (
 "xsxShiftVisited.clear();",
 "xsxShiftVisited.add(id)",
 "private void button(int action){",
 " @Override protected void containerTick(){",
 "  super.containerTick();",
 "double mx=event.x(),my=event.y(); int button=event.button();",
 'Component.literal("SORT"),b->{',
 "countSort=!countSort;",
 "button(2);",
 "xsxSyncServerScroll();",
 "xsxDraggingScrollbar",
 "xsxPendingScroll",
):
 assert required in s,("B1303_SCREEN_EXPECTED_DRIFT",required)
assert "B1303_SHIFT_SORT_LOCK" not in m+s
assert "32960" not in m+s and "32961" not in m+s
assert " @Override public boolean keyPressed(" not in s
assert " @Override public boolean keyReleased(" not in s

# Freeze only the visible entries' order and descriptors; the actual
# backpack's stored cells are NEVER locked or duplicated.
m=once(m,
"""  private boolean countSort=false;""",
"""  private boolean countSort=false;
   // B1303_SHIFT_SORT_LOCK: menu-local transient layout snapshot.
   // Never serialize it to the Backpack; only the chosen sort mode persists.
   private boolean xsxShiftLayoutFrozen=false;
   private java.util.List<V176BackpackCells.Entry> xsxShiftEntries=java.util.List.of();
   private boolean xsxSetShiftLayout(boolean freeze){
    if(!source.valid())return false;
    if(freeze&&!xsxShiftLayoutFrozen){
     xsxShiftEntries=java.util.List.copyOf(resultEntries());
     xsxShiftLayoutFrozen=true;
    }else if(!freeze&&xsxShiftLayoutFrozen){
     xsxShiftLayoutFrozen=false;
     xsxShiftEntries=java.util.List.of();
     // Source contents may have changed during the hold; force one fresh
     // live sort and clamp the existing scrolling row after release.
     cacheSource=ItemStack.EMPTY;
     cacheTick=Long.MIN_VALUE;
     int last=filterEditor?1:Math.max(0,(resultEntries().size()-45+8)/9);
     page=Math.max(0,Math.min(last,page));
    }
    return true;
   }""",
"shift_snapshot_fields")

m=once(m,
"""  private java.util.List<V176BackpackCells.Entry> resultEntries(){
   if(!source.valid())return java.util.List.of();""",
"""  private java.util.List<V176BackpackCells.Entry> resultEntries(){
   if(!source.valid())return java.util.List.of();
    // Preview AND extraction resolve the same immutable entry-to-slot
    // mapping until Shift is released; no ghost misrouting on live insert.
    if(xsxShiftLayoutFrozen)return xsxShiftEntries;""",
"authoritative_frozen_results")

m=once(m,
"""   tag.putLong("xsx_v176_preview_total",entry.count());""",
"""   tag.putLong("xsx_v176_preview_total",entry.count());
   // B1303_SORT_MODE_SYNC: expose the current persisted server-side mode
   // only in read-only preview metadata, never in real stored item NBT.
   tag.putBoolean("xsx_v176_backpack_sort_count",countSort);""",
"read_only_mode_metadata")

m=once(m,
"""  if(action==2)return sort(server);""",
"""  // Only one transition packet on Shift press/release, no menu packets/tick.
  if(action==32960||action==32961){
   boolean changed=storage.xsxSetShiftLayout(action==32960);
   if(changed)broadcastChanges();
   return changed;
  }
  if(action==2)return sort(server);""",
"validated_shift_button_router")

# The page-click ids are 192..32959. Never overload a valid old command.
assert "action>=192&&action<=32959" in m
assert "if(action==32960||action==32961)" in m
assert "page=Math.max(0,Math.min(last,page));" in m
assert "if(xsxShiftLayoutFrozen)return xsxShiftEntries;" in m
assert "xsxShiftEntries=java.util.List.copyOf(resultEntries());" in m
assert "source.save(updated)" in m

# Client: wire held Shift transitions via the existing vanilla menu button
# transport. Poll also handles Shift held BEFORE opening the GUI; key methods
# and mouse-click entry make ordinary press/release and first Shift click prompt.
s=once(s,
""" private boolean countSort=false;""",
""" private boolean countSort=false;
 // B1303_SHIFT_SORT_LOCK: no continuous packets, only state transitions.
 private boolean xsxShiftLockedSent=false;
 private net.minecraft.client.gui.components.Button xsxSortButton=null;
 private void xsxSyncShiftLayout(boolean shift){
  if(xsxShiftLockedSent==shift)return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player==null||mc.gameMode==null||mc.player.containerMenu!=menu)return;
  button(shift?32960:32961);
  xsxShiftLockedSent=shift;
 }
 private void xsxUpdateSortLabel(){
  if(xsxSortButton!=null)xsxSortButton.setMessage(
      Component.literal(countSort?"M ↓":"A-Z"));
 }
 private void xsxReadSortMode(){
  if(filterEditor)return;
  var preview=menu.getSlot(4).getItem();
  if(preview.isEmpty())return;
  var tag=preview.getOrDefault(
      net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
  if(!tag.contains("xsx_v176_backpack_sort_count"))return;
  boolean actual=tag.getBooleanOr("xsx_v176_backpack_sort_count",false);
  if(actual!=countSort){countSort=actual;xsxUpdateSortLabel();}
 }""",
"client_state_and_label")

s=once(s,
""" @Override protected void containerTick(){
  super.containerTick();""",
""" @Override protected void containerTick(){
  super.containerTick();
  // 26.1: Shift state comes from real KeyEvent and MouseButtonEvent modifiers.
  // Screen.hasShiftDown() no longer exists; no toggled-sneak polling here.
  xsxReadSortMode();""",
"sort_mode_client_sync_event_driven_shift")

s=once(s,
"""  double mx=event.x(),my=event.y(); int button=event.button();""",
"""  xsxSyncShiftLayout(event.hasShiftDown());
  double mx=event.x(),my=event.y(); int button=event.button();""",
"freeze_before_mouse_action")

# If keyboard is pressed/released between client ticks, send transition at
# the event boundary too; the original search/close key handling remains
# entirely in super. No changes to the existing mouse drag handlers.
s=once(s,
""" private void button(int action){""",
""" @Override public boolean keyPressed(net.minecraft.client.input.KeyEvent event){
  xsxSyncShiftLayout(event.hasShiftDown());
  return super.keyPressed(event);
 }
 @Override public boolean keyReleased(net.minecraft.client.input.KeyEvent event){
  xsxSyncShiftLayout(event.hasShiftDown());
  return super.keyReleased(event);
 }
 private void button(int action){""",
"immediate_key_transitions")

# Rename the existing SORT button to accurately expose the two distinct
# modes. Preserve its ONLY action: server-side action 2 toggles countSort.
needle='Component.literal("SORT"),b->{'
assert s.count(needle)==1,("B1303_SORT_BUTTON_NOT_FOUND",s.count(needle))
i=s.index(needle)
begin=s.rfind("addRenderableWidget(",0,i)
end=s.find(".build());",i)
assert begin>=0 and end>i and end-begin<550,("B1303_SORT_BUTTON_BODY_DRIFT",begin,end)
end+=len(".build());")
part=s[begin:end]
assert part.count("countSort=!countSort;")==1
assert part.count("button(2);")==1
part=part.replace("addRenderableWidget(","xsxSortButton=addRenderableWidget(",1)
part=part.replace('Component.literal("SORT")','Component.literal("A-Z")',1)
part=part.replace("countSort=!countSort;","countSort=!countSort;\n         xsxUpdateSortLabel();",1)
s=s[:begin]+part+s[end:]
assert "xsxSortButton=addRenderableWidget(" in s
assert 'Component.literal("A-Z")' in s
assert 'countSort?"M ↓":"A-Z"' in s
assert "xsxReadSortMode();" in s
assert s.count(" @Override public boolean mouseDragged(")==1
assert s.count(" @Override public boolean mouseReleased(")==1
assert "xsxShiftVisited.clear();" in s
assert "xsxShiftVisited.add(id)" in s

# Fail closed BEFORE writing either live generated Java source file.
menu.write_text(m,encoding="utf-8")
screen.write_text(s,encoding="utf-8")
print("B1303_BACKPACK_SHIFT_SERVER_SNAPSHOT_COUNT_DESC_AZ_SORT_PERSIST_BUTTON_ONLY_PASS")
