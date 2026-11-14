#!/usr/bin/env python3
"""v1.7.7: lossless builder-tool Backpack ITEM-capability read-side cache.

Construction Wands and Building Gadgets still withdraw real resources from
real Storage Cells with the original NeoForge ItemAccess exchange/transaction.
Only the expensive sorted/decoded item VIEW is cached per capability handler,
keyed by the exact immutable ItemResource and count, never by a game tick.
"""
import os
from pathlib import Path

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack/V176BackpackBuilderSupply.java"
source=path.read_text(encoding="utf-8")

def replace(old,new):
 global source
 count=source.count(old)
 assert count==1,("V177_BUILDER_SUPPLY_PERF_DRIFT",count,old[:110])
 source=source.replace(old,new,1)

replace(
''' private List<V176BackpackCells.Entry> entries(){
  ItemStack stack=bag();
  return stack.isEmpty()?List.of():V176BackpackCells.entries(stack);
 }''',
''' // Builder integrations call size/getResource/getAmount/capacity many times
 // per placed block. Reconstruct sorted REAL Cell contents once per immutable
 // ItemAccess resource. No TTL: a changed Container/Cell component refreshes
 // on the very next query, including after transaction rollback.
 private ItemResource xsxViewSource=ItemResource.EMPTY;
 private long xsxViewAmount=Long.MIN_VALUE;
 private boolean xsxViewValid=false;
 private List<V176BackpackCells.Entry> xsxViewEntries=List.of();
 private List<ItemResource> xsxViewResources=List.of();
 private void xsxRefreshView(){
  ItemResource current=access.getResource();
  long amount=access.getAmount();
  if(xsxViewValid&&amount==xsxViewAmount
      &&(current==xsxViewSource||current.equals(xsxViewSource)))return;
  // Mark invalid before rebuilding: failure may NEVER expose an old list.
  xsxViewValid=false;
  xsxViewEntries=List.of();
  xsxViewResources=List.of();
  if(!current.isEmpty()&&amount==1L){
   ItemStack stack=current.toStack(1);
   if(stack.getItem() instanceof NetworkBackpackItem){
    List<V176BackpackCells.Entry> entries=V176BackpackCells.entries(stack);
    var level=world();
    MinecraftItemStackCodec codec=level==null?null:
        new MinecraftItemStackCodec(level.registryAccess());
    var decoded=new java.util.ArrayList<ItemResource>(entries.size());
    for(var entry:entries)decoded.add(resourceOf(entry,codec));
    xsxViewEntries=entries;
    xsxViewResources=List.copyOf(decoded);
   }
  }
  xsxViewSource=current;
  xsxViewAmount=amount;
  xsxViewValid=true;
 }
 private List<V176BackpackCells.Entry> entries(){
  xsxRefreshView();
  return xsxViewEntries;
 }''')
replace(
''' private ItemResource resourceOf(V176BackpackCells.Entry entry){
  var world=world();
  if(world!=null){
   var codec=new MinecraftItemStackCodec(world.registryAccess());
   return ItemResource.of(codec.recreate(entry.descriptor(),1));
  }''',
''' private ItemResource resourceOf(V176BackpackCells.Entry entry,MinecraftItemStackCodec codec){
  if(codec!=null){
   return ItemResource.of(codec.recreate(entry.descriptor(),1));
  }''')
replace(
''' @Override public ItemResource getResource(int index){
  var entries=entries();
  return index>=0&&index<entries.size()?resourceOf(entries.get(index)):ItemResource.EMPTY;
 }''',
''' @Override public ItemResource getResource(int index){
  xsxRefreshView();
  return index>=0&&index<xsxViewResources.size()
      ?xsxViewResources.get(index):ItemResource.EMPTY;
 }''')
replace(
'''  return resource.equals(resourceOf(entries.get(index)))?entries.get(index).count():0L;''',
'''  return resource.equals(xsxViewResources.get(index))?entries.get(index).count():0L;''')
replace(
'''  ItemStack before=bag();
  if(before.isEmpty())return 0;
  var list=V176BackpackCells.entries(before);
  if(index<0||index>=list.size())return 0;
  var entry=list.get(index);
  // Exact item AND component match before any transactional mutation.
  if(!requested.equals(resourceOf(entry)))return 0;''',
'''  // Reject missing or mismatched resources BEFORE copying/decoding cells.
  // This is a read-only snapshot of the CURRENT exact ItemAccess resource.
  xsxRefreshView();
  if(index<0||index>=xsxViewEntries.size())return 0;
  var entry=xsxViewEntries.get(index);
  // Exact item AND component match before any transactional mutation.
  if(!requested.equals(xsxViewResources.get(index)))return 0;
  ItemStack before=bag();
  if(before.isEmpty())return 0;''')
replace(
'''  if(access.exchange(ItemResource.of(updated),1,tx)!=1)return 0;
  return accepted;''',
'''  if(access.exchange(ItemResource.of(updated),1,tx)!=1){
   xsxViewValid=false; // a failed exchange can change the local transaction view
   return 0;
  }
  xsxViewValid=false; // root commit OR rollback must re-read canonical contents
  return accepted;''')
assert source.count("V176BackpackCells.entries(")==1
assert source.count("V176BackpackCells.extract(world,updated,entry.descriptor(),n)")==1
assert source.count("access.exchange(ItemResource.of(updated),1,tx)")==1
assert "return 0; // Supply-only." in source
assert "xsxViewValid=false;" in source
path.write_text(source,encoding="utf-8")
print("V177_BUILDER_SUPPLY_CACHED_EXACT_ITEM_VIEW_REAL_TRANSACTIONAL_EXTRACTION_PASS")
