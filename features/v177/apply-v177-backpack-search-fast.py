#!/usr/bin/env python3
"""v1.7.7: responsive backpack search without re-sorting the entire list per key.

Keep vanilla ChestMenu previews/clicks server authoritative. Cached order and
lowercase registry keys are rebuilt ONLY when the real storage component,
committed placed-backpack cable revision, or persistent sort mode changes.
A typed query filters the already sorted entries; the screen coalesces bursts
to at most one current-query server command per client game tick.
Only changes generated v1.7.7 Java after every v1.7.6 backpack patch.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
menu=root/"backpack/V176BackpackMenu.java"
screen=root/"client/V176BackpackScreen.java"
m=menu.read_text(encoding="utf-8")
s=screen.read_text(encoding="utf-8")

def replace_one(source,old,new,label):
 count=source.count(old)
 assert count==1,("V177_FAST_BACKPACK_SEARCH_SOURCE_DRIFT",label,count)
 return source.replace(old,new,1)

for needle in (
 "B1302_SORT_RESTORED",
 "B1303_SHIFT_SORT_LOCK",
 "B1304_REAL_NAME_AZ",
 "cacheContainer==content",
 "cacheCableRevision==liveCableRevision",
 "private java.util.List<V176BackpackCells.Entry> resultEntries()",
 "if(xsxShiftLayoutFrozen)return xsxShiftEntries;",
 "cacheEntries=java.util.List.copyOf(result);",
 "source.save(updated)",
):
 assert needle in m,("V177_FAST_SEARCH_MENU_PREREQUISITE",needle)
for needle in (
 "searchBox.setResponder(value->{pendingSearch=value;searchDelay=25;});",
 " @Override protected void containerTick(){",
 "  super.containerTick();",
 "xsxSyncServerScroll();",
 "xsxShiftVisited.add(id)",
 "private void button(int action){",
):
 assert needle in s,("V177_FAST_SEARCH_SCREEN_PREREQUISITE",needle)

m=replace_one(m,
 """  private java.util.List<V176BackpackCells.Entry> cacheEntries=java.util.List.of();""",
 """  private java.util.List<V176BackpackCells.Entry> cacheEntries=java.util.List.of();
  // V177_FAST_SEARCH: separate the expensive unfiltered sort from the query.
  // Neither cached list is an inventory: real extraction remains server-side.
  private ItemStack xsxSearchSource=ItemStack.EMPTY;
  private net.minecraft.world.item.component.ItemContainerContents xsxSearchContainer=null;
  private long xsxSearchCableRevision=Long.MIN_VALUE;
  private boolean xsxSearchSort=false;
  private java.util.List<V176BackpackCells.Entry> xsxSearchSorted=java.util.List.of();
  private java.util.List<String> xsxSearchKeys=java.util.List.of();""",
 "persistent server search base cache")

start_text="   var result=new java.util.ArrayList<>(V176BackpackCells.entries(live));"
stop_text="   cacheTick=tick;"
assert m.count(start_text)==1,("V177_FAST_SEARCH_LIST_START",m.count(start_text))
a=m.index(start_text)
b=m.index(stop_text,a)
original=m[a:b]
for token in (
 "result.removeIf(e->{",
 "if(countSort)result.sort(java.util.Comparator",
 "B1304_REAL_NAME_AZ",
 "names.get(e)",
 "codec.recreate(entry.descriptor(),1)",
):
 assert token in original,("V177_FAST_SEARCH_SORT_SHAPE",token)

replacement="""   // The exact stored cell snapshot, cable commit revision and mode determine
   // the sorted base. Typing must never decode/sort every item again.
   boolean xsxRebuildSearch=xsxSearchSource!=live
       ||xsxSearchContainer!=content
       ||xsxSearchCableRevision!=liveCableRevision
       ||xsxSearchSort!=countSort;
   if(xsxRebuildSearch){
    var all=new java.util.ArrayList<>(V176BackpackCells.entries(live));
    if(countSort)all.sort(java.util.Comparator
        .comparingLong(V176BackpackCells.Entry::count).reversed()
        .thenComparing(e->e.descriptor().key().itemId().toString()));
    else {
     // Preserve B1304's displayed-name A-Z behavior, once per cell revision.
     var player=(source instanceof ItemSource item?item.player:
          ((BlockSource)source).player);
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(
          player.level().registryAccess());
     var names=new java.util.IdentityHashMap<V176BackpackCells.Entry,String>(
          Math.max(16,all.size()));
     for(var entry:all){
      String display;
      try{
       display=codec.recreate(entry.descriptor(),1)
           .getHoverName().getString().toLowerCase(java.util.Locale.ROOT);
      }catch(RuntimeException undecodable){
       display=entry.descriptor().key().itemId().toString();
      }
      names.put(entry,display);
     }
     all.sort(java.util.Comparator
         .comparing((V176BackpackCells.Entry e)->names.get(e))
         .thenComparing(e->e.descriptor().key().itemId().toString()));
    }
    var keys=new java.util.ArrayList<String>(all.size());
    for(var entry:all)
     keys.add(entry.descriptor().key().itemId().toString()
         .toLowerCase(java.util.Locale.ROOT));
    xsxSearchSorted=java.util.List.copyOf(all);
    xsxSearchKeys=java.util.List.copyOf(keys);
    xsxSearchSource=live;
    xsxSearchContainer=content;
    xsxSearchCableRevision=liveCableRevision;
    xsxSearchSort=countSort;
   }
   // This inexpensive filter is the ONLY work repeated for each new query.
   // Preserve the exact server-side sorted indices for preview and withdrawal.
   var result=new java.util.ArrayList<V176BackpackCells.Entry>();
   for(int i=0;i<xsxSearchSorted.size();i++)
    if(xsxSearchKeys.get(i).contains(query))result.add(xsxSearchSorted.get(i));
"""
m=m[:a]+replacement+m[b:]

s=replace_one(s,
 """  searchBox.setResponder(value->{pendingSearch=value;searchDelay=25;});""",
 """  searchBox.setResponder(value->xsxQueueSearch(value));""",
 "remove 25-tick debounce and coalesce direct editbox responder")

# The old B1225 debounce waits 25 game ticks AFTER typing stops,
# or about 1.25 seconds. Remove it entirely; do not add another timer.
s=replace_one(s,
 """ private String pendingSearch="";
 private int searchDelay=-1;""",
 """ // V177_FAST_SEARCH: no artificial 25-tick delay.""",
 "delete 1.25s debounce fields")
start="  if(searchDelay>0&&--searchDelay==0&&!filterEditor){"
assert s.count(start)==1,("V177_FAST_SEARCH_DEBOUNCE_GATE_DRIFT",s.count(start))
a=s.index(start)
# Search the generated Java source as literal text with a bounded method end.
b=s.find("\n  }",a)
assert b>a and b-a<600,("V177_FAST_SEARCH_DEBOUNCE_END_DRIFT",a,b)
s=s[:a]+"  xsxFlushSearch();"+s[b+len("\n  }"):]

s=replace_one(s,
 """ private void button(int action){""",
 """ // V177_FAST_SEARCH: keep only the latest query when a player types many
 // characters in one tick. The input widget itself remains immediate.
 // Avoid Brigadier spam and a server-side rebuild backlog. NO client
 // inventory prediction: every withdraw still checks the real server menu.
 private String xsxPendingSearch=null;
 private long xsxLastSearchPacketTick=Long.MIN_VALUE;
 private void xsxQueueSearch(String value){
  xsxPendingSearch=value;
  xsxFlushSearch();
 }
 private void xsxFlushSearch(){
  if(xsxPendingSearch==null||filterEditor)return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.player.containerMenu!=menu)return;
  long tick=mc.level.getGameTime();
  if(tick==xsxLastSearchPacketTick)return;
  String current=xsxPendingSearch.replace("\\r","").replace("\\n","").trim();
  xsxPendingSearch=null;
  xsxLastSearchPacketTick=tick;
  command(current.isBlank()?"networkbackpack search clear":"networkbackpack search "+current);
 }
 private void button(int action){""",
 "single latest query per tick")

s=replace_one(s,
 """ @Override protected void containerTick(){
  super.containerTick();""",
 """ @Override protected void containerTick(){
  super.containerTick();
  xsxFlushSearch();""",
 "flush final query next tick")

assert m.count("V177_FAST_SEARCH")==1
assert s.count("V177_FAST_SEARCH")==2
assert "V176BackpackCells.entries(live)" in m
assert "if(xsxShiftLayoutFrozen)return xsxShiftEntries;" in m
assert "cacheEntries=java.util.List.copyOf(result);" in m
assert "if(xsxSearchKeys.get(i).contains(query))" in m
assert "xsxSearchCableRevision!=liveCableRevision" in m
assert s.count("searchBox.setResponder(value->xsxQueueSearch(value));")==1
assert "searchDelay" not in s and "pendingSearch" not in s
assert "xsxFlushSearch();" in s
assert "button(192+xsxPendingScroll);" in s
assert "xsxShiftVisited.add(id)" in s

# Fail closed before writing either file; preserve every v1.7.6 patch.
menu.write_text(m,encoding="utf-8")
screen.write_text(s,encoding="utf-8")
print("V177_BACKPACK_SEARCH_SORT_ONCE_PER_STORAGE_REVISION_ONE_QUERY_PACKET_PER_TICK_PASS")
