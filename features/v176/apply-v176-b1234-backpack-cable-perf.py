#!/usr/bin/env python3
"""B1234: amortize placed Backpack Item Cable slot/capacity queries.

The NeoForge handler previously rebuilt/sorted ALL real cell entries for
size/getResource/getAmount/isValid/getCapacity and scanned all stores AGAIN
for every capacity query. A cable probing every slot therefore did repeated
O(number-of-item-types) work on each tick.

Cache the immutable cable view only while BOTH the owned ItemStack identity
and immutable CONTAINER component are unchanged, and while the B1230
committed-transfer generation is unchanged. In-place extract, detached
insert, external GUI mutation, pickup/replacement and transaction rollback
all invalidate on their next query, without a tick-based stale window.
"""
import os
from pathlib import Path

TARGET = "backpack/NetworkBackpackBlockEntity.java"
path = Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"/TARGET

def swap(old, new):
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    assert count == 1, ("B1234_CABLE_PERF_SOURCE_DRIFT", count, old[:120])
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

swap(
''' private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
''' // Item Cables query every slot several times on each tick. The stored
 // cell container is an immutable DataComponent; every real cell-content
 // change installs a NEW container. ItemStack identity also changes on
 // B1225 detached insert, B1230 GUI CAS and transaction rollback.
 private ItemStack xsxCableCacheStack=null;
 private net.minecraft.world.item.component.ItemContainerContents xsxCableCacheContainer=null;
 private long xsxCableCacheRevision=Long.MIN_VALUE;
 private java.util.List<V176BackpackCells.Entry> xsxCableEntries=java.util.List.of();
 private java.util.List<net.neoforged.neoforge.transfer.item.ItemResource> xsxCableResources=java.util.List.of();
 private long xsxCableCapacity=0L;
 private long xsxCableUsed=0L;
 private void xsxRefreshCableView(){
  var container=backpack.isEmpty()?null:
      backpack.get(net.minecraft.core.component.DataComponents.CONTAINER);
  if(xsxCableCacheStack==backpack
      &&xsxCableCacheContainer==container
      &&xsxCableCacheRevision==xsxCableCommitRevision)return;
  if(level==null||backpack.isEmpty()){
   xsxCableEntries=java.util.List.of();
   xsxCableResources=java.util.List.of();
   xsxCableCapacity=0L;
   xsxCableUsed=0L;
  }else{
   var entries=V176BackpackCells.entries(backpack);
   var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
   var resources=new java.util.ArrayList<net.neoforged.neoforge.transfer.item.ItemResource>(entries.size());
   for(var entry:entries)
    resources.add(net.neoforged.neoforge.transfer.item.ItemResource.of(
        codec.recreate(entry.descriptor(),1)));
   xsxCableEntries=entries;
   xsxCableResources=java.util.List.copyOf(resources);
   xsxCableCapacity=V176BackpackCells.capacity(backpack);
   xsxCableUsed=V176BackpackCells.used(backpack);
  }
  xsxCableCacheStack=backpack;
  xsxCableCacheContainer=container;
  xsxCableCacheRevision=xsxCableCommitRevision;
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''')

swap(
'''    private java.util.List<V176BackpackCells.Entry> list(){
     if(backpack.isEmpty()||level==null)return java.util.List.of();
     return V176BackpackCells.entries(backpack);
    }''',
'''    private java.util.List<V176BackpackCells.Entry> list(){
     xsxRefreshCableView();
     return xsxCableEntries;
    }''')

swap(
'''    @Override public net.neoforged.neoforge.transfer.item.ItemResource getResource(int i){
     var entries=list();
     if(i<0||i>=entries.size())return net.neoforged.neoforge.transfer.item.ItemResource.EMPTY;
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     return net.neoforged.neoforge.transfer.item.ItemResource.of(
       codec.recreate(entries.get(i).descriptor(),1));
    }''',
'''    @Override public net.neoforged.neoforge.transfer.item.ItemResource getResource(int i){
     xsxRefreshCableView();
     return i<0||i>=xsxCableResources.size()
        ?net.neoforged.neoforge.transfer.item.ItemResource.EMPTY
        :xsxCableResources.get(i);
    }''')

swap(
'''    @Override public long getAmountAsLong(int i){
     var entries=list();return i>=0&&i<entries.size()?entries.get(i).count():0L;
    }''',
'''    @Override public long getAmountAsLong(int i){
     xsxRefreshCableView();
     return i>=0&&i<xsxCableEntries.size()?xsxCableEntries.get(i).count():0L;
    }''')

swap(
'''    @Override public long getCapacityAsLong(int i,
      net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty())return 0L;
     var entries=list();
     if(i<0||i>entries.size())return 0L;
     long stored=i<entries.size()?entries.get(i).count():0L;
     if(resource.isEmpty())
      return Math.min(Integer.MAX_VALUE,Math.max(stored,V176BackpackCells.capacity(backpack)));
     if(!isValid(i,resource))return 0L;
     long free=Math.max(0L,V176BackpackCells.capacity(backpack)-V176BackpackCells.used(backpack));
     return Math.min((long)Integer.MAX_VALUE,stored+free);
    }''',
'''    @Override public long getCapacityAsLong(int i,
      net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty())return 0L;
     xsxRefreshCableView();
     if(i<0||i>xsxCableEntries.size())return 0L;
     long stored=i<xsxCableEntries.size()?xsxCableEntries.get(i).count():0L;
     if(resource.isEmpty())
      return Math.min(Integer.MAX_VALUE,Math.max(stored,xsxCableCapacity));
     if(!isValid(i,resource))return 0L;
     long free=Math.max(0L,xsxCableCapacity-xsxCableUsed);
     return Math.min((long)Integer.MAX_VALUE,stored+free);
    }''')

swap(
'''    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty()||resource.isEmpty()
        ||resource.getItem() instanceof NetworkBackpackItem)return false;
     var entries=list();
     if(i<0||i>entries.size()||V176BackpackCells.capacity(backpack)<=0L)return false;
     // Occupied indices may accept only the exact existing item and components.
     // The final empty virtual index admits new types into installed real cells.
     if(i==entries.size())return true;
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     return resource.equals(net.neoforged.neoforge.transfer.item.ItemResource.of(
       codec.recreate(entries.get(i).descriptor(),1)));
    }''',
'''    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty()||resource.isEmpty()
        ||resource.getItem() instanceof NetworkBackpackItem)return false;
     xsxRefreshCableView();
     if(i<0||i>xsxCableEntries.size()||xsxCableCapacity<=0L)return false;
     // Existing slots only accept exact item+components; the virtual last
     // slot admits new types. Neither cells nor upgrades are exposed.
     if(i==xsxCableEntries.size())return true;
     return resource.equals(xsxCableResources.get(i));
    }''')

swap(
'''     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     if(!net.neoforged.neoforge.transfer.item.ItemResource.of(
          codec.recreate(d,1)).equals(wanted))return 0;''',
'''     // The same exact resource was already decoded for this slot view.
     if(!xsxCableResources.get(i).equals(wanted))return 0;''')

# Cache GUI visible item list beyond a single tick as long as exact source
# component and B1230 transaction revision remain unchanged. In-place cable
# mutation installs a new immutable CONTAINER component on the same stack.
menu=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack/V176BackpackMenu.java"
view=menu.read_text(encoding="utf-8")
def replace_view(old,new):
 global view
 assert view.count(old)==1,("B1234_GUI_CACHE_DRIFT",view.count(old),old[:110])
 view=view.replace(old,new,1)
replace_view(
'''  private ItemStack cacheSource=ItemStack.EMPTY;
  private long cacheCableRevision=Long.MIN_VALUE;''',
'''  private ItemStack cacheSource=ItemStack.EMPTY;
  private net.minecraft.world.item.component.ItemContainerContents cacheContainer=null;
  private long cacheCableRevision=Long.MIN_VALUE;''')
replace_view(
'''   if(cacheTick==tick&&cacheSource==live
        &&cacheCableRevision==liveCableRevision
        &&cacheQuery.equals(query)&&cacheSort==countSort)return cacheEntries;''',
'''   var content=live.get(net.minecraft.core.component.DataComponents.CONTAINER);
   if(cacheSource==live&&cacheContainer==content
        &&cacheCableRevision==liveCableRevision
        &&cacheQuery.equals(query)&&cacheSort==countSort)return cacheEntries;''')
replace_view(
'''   cacheTick=tick;
   cacheSource=live;
   cacheCableRevision=liveCableRevision;''',
'''   cacheTick=tick;
   cacheSource=live;
   cacheContainer=content;
   cacheCableRevision=liveCableRevision;''')
assert "cacheContainer==content" in view
assert "cacheCableRevision==liveCableRevision" in view
menu.write_text(view,encoding="utf-8")

source=path.read_text(encoding="utf-8")
assert source.count("V176BackpackCells.entries(backpack)") == 1
assert source.count("V176BackpackCells.capacity(backpack)") == 1
assert source.count("V176BackpackCells.used(backpack)") == 1
assert "cableJournal.updateSnapshots(tx)" in source
assert "xsxCableCommitRevision++;" in source
assert "backpack=updated;" in source
assert "backpack=before.copy();" in source
assert "if(i==xsxCableEntries.size())return true;" in source
print("B1234_BACKPACK_CABLE_CACHED_VIEW_CONTAINER_REVISION_ROLLBACK_PASS")
