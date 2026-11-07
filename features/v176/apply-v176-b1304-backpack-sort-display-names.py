#!/usr/bin/env python3
"""B1304: true item-name A-Z sorting, not mod-namespace registry ID order.

The B816 A-Z comparator compared "modid:item", which puts all of one mod
before another even when their displayed names alphabetize differently.
Resolve visible ItemStack hover names ONCE per distinct filtered list entry
during an existing menu cache rebuild. Comparator uses precomputed strings
(O(N) label conversions + O(N log N) comparisons), not repeated per-comparison
stack decoding. B1234's immutable-container cache still avoids rebuilding
every tick when entries did not change.

MENGE ↓ remains the original exact 64-bit count descending. B1302 persists
only the selected mode. B1303 Shift freezes the exact server sorted list and
click mapping. No data migration, new packets, item transfers or cell changes.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack/V176BackpackMenu.java"
s=p.read_text("utf-8")
for key in (
 "B1302_SORT_RESTORED",
 "B1302_SORT_SAVE_CAS",
 "B1303_SHIFT_SORT_LOCK",
 "xsxShiftEntries=java.util.List.copyOf(resultEntries());",
 "if(xsxShiftLayoutFrozen)return xsxShiftEntries;",
 "cacheEntries=java.util.List.copyOf(result);",
 "if(countSort)result.sort(java.util.Comparator",
 "V176BackpackCells.Entry::count).reversed()",
 "private java.util.List<V176BackpackCells.Entry> resultEntries()",
):
 assert key in s,("B1304_SORT_SOURCE_DRIFT",key)
old="""   // The default is a stable item-identity sort, not unordered HashMap order.
   else result.sort(java.util.Comparator.comparing(
      e->e.descriptor().key().itemId().toString()));"""
new="""    // B1304_REAL_NAME_AZ: alphabetical by displayed item name, NOT the
    // registry namespace. Resolve labels ONCE before O(N log N) sorting.
    // Keep exact descriptors and native items untouched.
    else {
     var player=(source instanceof ItemSource item?item.player:
          ((BlockSource)source).player);
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(
          player.level().registryAccess());
     var names=new java.util.IdentityHashMap<V176BackpackCells.Entry,String>(
          Math.max(16,result.size()));
     for(var entry:result){
      String display;
      try{
       display=codec.recreate(entry.descriptor(),1)
           .getHoverName().getString().toLowerCase(java.util.Locale.ROOT);
      }catch(RuntimeException undecodable){
       // A bad third-party item descriptor must not crash the whole screen.
       display=entry.descriptor().key().itemId().toString();
      }
      names.put(entry,display);
     }
     result.sort(java.util.Comparator
         .comparing((V176BackpackCells.Entry e)->names.get(e))
         .thenComparing(e->e.descriptor().key().itemId().toString()));
    }"""
assert s.count(old)==1,("B1304_AZ_COMPARATOR_DRIFT",s.count(old))
assert s.count("if(countSort)result.sort(")==1
assert "xsxShiftLayoutFrozen" in s
changed=s.replace(old,new,1)
assert changed.count("B1304_REAL_NAME_AZ")==1
assert "V176BackpackCells.Entry::count).reversed()" in changed
assert "xsx_v176_backpack_sort_count" in changed
assert "if(xsxShiftLayoutFrozen)return xsxShiftEntries;" in changed
assert "names.get(e)" in changed
assert "codec.recreate(entry.descriptor(),1)" in changed
assert "source.save(updated)" in changed
p.write_text(changed,encoding="utf-8")
print("B1304_BACKPACK_NAME_AZ_REAL_DISPLAY_64BIT_COUNT_DESC_CACHED_SHIFT_SNAPSHOT_PASS")
