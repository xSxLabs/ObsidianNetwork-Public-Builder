#!/usr/bin/env python3
"""B1248: avoid redundant decoded Storage Cell reads on Backpack hot paths.

Pure re-use of an immutable container snapshot and one previously decoded
Store where it was NOT mutated. No skip-ticks, buffer limits, pickup delays,
changes to accepted quantities, storage routing, validation or rollback.
Applied after B1234's completed cable cache/magnet fixes; strict fail closed.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack/V176BackpackCells.java"
s=p.read_text(encoding="utf-8")

def swap(old,new):
 global s
 assert s.count(old)==1,("B1248_BACKPACK_HOTPATH_SOURCE_DRIFT",s.count(old),old[:110])
 s=s.replace(old,new,1)

# B1252: The real reconstructed Java differs from the checked-in fixture
# for count(), presumably because of a preceding build patch. Never overwrite
# a method whose exact semantics we have not verified. This micro-optimization
# is optional; the magnet and two-pass insertion changes still fail closed.
# Keep an unambiguous strict match for the expected count body.
count_before=''' public static long count(ItemStack bag,ItemKey key){
  long count=0;
  for(int i=1;i<=3;i++){
   ItemStack cellStack=slots(bag).get(i);'''
count_after=''' public static long count(ItemStack bag,ItemKey key){
  long count=0;
  var stored=slots(bag); // same immutable container and validation, once
  for(int i=1;i<=3;i++){
   ItemStack cellStack=stored.get(i);'''
if s.count(count_before)==1:
 swap(count_before,count_after)
 count_optimized=True
else:
 assert s.count(count_before)==0, "B1252_COUNT_AMBIGUOUS_MATCH"
 # No changes to the unknown existing implementation. It may already cache
 # a cell snapshot, or the method may have been inlined by an earlier patch.
 count_optimized=False
 print("B1252_COUNT_HOTPATH_SOURCE_CHANGED_SKIP_UNVERIFIED_OPTIMIZATION")

# A magnet entity filter request previously decoded the entire backpack
# CONTAINER three times, copied CUSTOM_DATA twice, and described one ItemKey
# per sample. Keep existing exact ItemKey comparisons and all 54 filters.
# Do not cache module state across clicks: changes must take effect instantly.
swap(
''' public static boolean magnetAccepts(Level world,ItemStack bag,ItemStack incoming){
  if(!magnetEnabled(bag)||incoming.isEmpty())return false;
  ItemStack upgrade=magnet(bag);
  var templates=upgrade.getOrDefault(DataComponents.CONTAINER,ItemContainerContents.EMPTY);''',
''' public static boolean magnetAccepts(Level world,ItemStack bag,ItemStack incoming){
  ItemStack upgrade=slots(bag).get(SLOT_MAGNET);
  if(upgrade.isEmpty())return false;
  var settings=magnetData(upgrade);
  if(!settings.getBooleanOr(MAG_ON,true)||incoming.isEmpty())return false;
  var templates=upgrade.getOrDefault(DataComponents.CONTAINER,ItemContainerContents.EMPTY);''')
swap(
'''  return magnetWhitelist(bag)?listed:!listed;
 }
 public static boolean setMagnetFilter''',
'''  return settings.getBooleanOr(MAG_WHITELIST,false)?listed:!listed;
 }
 public static boolean setMagnetFilter''')


# B1255: The real reconstructed Backpack insert() supports additional
# EquipmentCellItem stores. The checked-in fixture only covers StorageCells.
# Never modify an enriched two-phase algorithm without a source-specific
# equivalence proof: optimize only the exact, fully recognized original.
insert_before='''  long left=requested;
  // Prefer cells already holding the item key; then empty cell-space.
  for(int phase=0;phase<2&&left>0;phase++){'''
insert_after='''  long left=requested;
  StorageCellStore[] absentAtFirstPass=new StorageCellStore[3];
  // Prefer cells already holding the item key; then empty cell-space.
  for(int phase=0;phase<2&&left>0;phase++){'''
read_before='''    StorageCellStore store=cell.readStore(cellStack);
    boolean present=store.amount(d.key())>0;
    if((phase==0)!=present)continue;
    long accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);'''
read_after='''    StorageCellStore store=phase==1&&absentAtFirstPass[i-1]!=null
        ?absentAtFirstPass[i-1]:cell.readStore(cellStack);
    boolean present=store.amount(d.key())>0;
    if((phase==0)!=present){
     if(phase==0)absentAtFirstPass[i-1]=store;
     continue;
    }
    long accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);'''
assert s.count(" public static Transfer insert(")==1, "B1255_INSERT_API_MISSING"
# Capture all existing insertion code. When drifting, guarantee no change
# whatsoever to capacity, Equipment Cells, routing, counts or transactions.
insert_original=s[s.index(" public static Transfer insert("):s.index(" public static List<Entry> entries(")]
if s.count(insert_before)==1 and s.count(read_before)==1:
 swap(insert_before,insert_after)
 swap(read_before,read_after)
 insert_optimized=True
else:
 insert_optimized=False
 print("B1255_INSERT_EQUIPMENT_CELL_SOURCE_CHANGED_SKIP_UNVERIFIED_OPTIMIZATION")
assert insert_optimized or (s[s.index(" public static Transfer insert("):s.index(" public static List<Entry> entries(")]==insert_original), "B1255_INSERT_CHANGED_DURING_SKIP"

assert s.count("V176BackpackCells")>=1 or "class V176BackpackCells" in s
assert not count_optimized or "var stored=slots(bag);" in s
assert "settings.getBooleanOr(MAG_ON,true)" in s
assert "settings.getBooleanOr(MAG_WHITELIST,false)" in s
assert "for(int i=0;i<Math.min(FILTER_SLOTS,templates.getSlots());i++)" in s
assert not insert_optimized or "absentAtFirstPass[i-1]=store;" in s
assert not insert_optimized or "if(left<requested)writeSlots(bag,replacements);" in s
assert not insert_optimized or "store.insertExact(d.key(),d.canonicalPayload(),accepted);" in s
assert " public static Transfer extract(" in s
p.write_text(s,encoding="utf-8")
print("B1248_BACKPACK_MAGNET_FILTER_NO_REPEATED_READ_PASS COUNT_OPTIMIZED="+str(count_optimized)+" INSERT_OPTIMIZED="+str(insert_optimized))
