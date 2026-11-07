#!/usr/bin/env python3
"""B1302: persist each backpack's chosen sort mode on its owned ItemStack.

B816 used menu-local countSort=false and a button toggle with no save.
Use one small CUSTOM_DATA boolean (default false) on the backpack item.
Only commit the next sort state if the original Source's CAS save succeeds.
This works for worn/Curios/held/inventory/placed backpacks and survives
GUI reopening, placing/picking up the backpack, server restart and Cell edits.

Also ensure B1301 new INVENTORY enum case is handled in B810's exhaustive
ItemSource.live() switch. Do not alter recipes, cell NBT, search, filters,
scrolling, capacity, sorting comparator, client packets or gameplay energy.
"""
import os
from pathlib import Path

base=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
menu=base/"backpack/V176BackpackMenu.java"
equipped=base/"backpack/V176BackpackEquipped.java"
m=menu.read_text("utf-8")
e=equipped.read_text("utf-8")

for required in (
 "private boolean countSort=false;",
 "private boolean sort(){",
 "if(countSort)result.sort(java.util.Comparator",
 "private final Source source;",
 "Storage(Source source){super(54);this.source=source;}",
 "private ItemStack live(){",
 "case CHEST->", "case CURIOS_BACK->",
 "case MAIN_HAND->", "case OFF_HAND->",
):
 assert required in m,("B1302_MENU_DRIFT",required)
assert "B1301_INVENTORY_MAGNET_CAS" in e
assert "B1301_INVENTORY_MAGNET_DISCOVERY" in e
assert "case INVENTORY->" in e
assert "case INVENTORY->" not in m

def one(src,old,new,where):
 count=src.count(old)
 assert count==1,("B1302_SOURCE_DRIFT",where,count,old[:180])
 return src.replace(old,new,1)

# Exact B810 ItemSource.live() source switch. Missing new enum case would not
# compile after B1301 even though the magnet finder itself is correct.
m=one(m,
 """    case OFF_HAND->player.getItemInHand(InteractionHand.OFF_HAND);
    case CURIOS_BACK->""",
 """    case OFF_HAND->player.getItemInHand(InteractionHand.OFF_HAND);
    // B1302_INVENTORY_SOURCE: only the original validated slot.
    case INVENTORY->location.index()>=0
         &&location.index()<player.getInventory().getContainerSize()
         ?player.getInventory().getItem(location.index()):ItemStack.EMPTY;
    case CURIOS_BACK->""",
 "exhaustive_B810_inventory_source")

# The sort is an ATTRIBUTE of this specific backpack, not the menu instance.
# These fields live in the existing item CUSTOM_DATA, independent of the
# magnet upgrade's CUSTOM_DATA and of the storage cell CONTAINER.
m=one(m,
 """   Storage(Source source){super(54);this.source=source;}""",
 """   // B1302_SORT_RESTORED: one per-backpack server-side setting.
   Storage(Source source){
    super(54);this.source=source;
    if(source.valid()){
     var data=source.current().getOrDefault(
         net.minecraft.core.component.DataComponents.CUSTOM_DATA,
         net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
     countSort=data.getBooleanOr("xsx_v176_backpack_sort_count",false);
    }
   }""",
 "persistent_sort_load")

m=one(m,
 """   private boolean sort(){
    if(!source.valid())return false;
    countSort=!countSort;page=0;return true;
   }""",
 """   private boolean sort(){
    if(!source.valid())return false;
    // B1302_SORT_SAVE_CAS: keep current list if its source changed.
    boolean requested=!countSort;
    ItemStack updated=source.current().copy();
    var tag=updated.getOrDefault(
        net.minecraft.core.component.DataComponents.CUSTOM_DATA,
        net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
    tag.putBoolean("xsx_v176_backpack_sort_count",requested);
    updated.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
                net.minecraft.world.item.component.CustomData.of(tag));
    if(!source.save(updated))return false;
    countSort=requested;
    page=0;
    return true;
   }""",
 "persist_sort_on_click")

assert "B1302_SORT_RESTORED" in m
assert "B1302_SORT_SAVE_CAS" in m
assert "B1302_INVENTORY_SOURCE" in m
assert "if(countSort)result.sort(java.util.Comparator" in m
assert "source.save(updated)" in m
assert "source.current().copy()" in m
assert "xsx_v176_backpack_sort_count" in m
assert e==equipped.read_text("utf-8")
menu.write_text(m,encoding="utf-8")
print("B1302_BACKPACK_SORT_PER_ITEM_PERSISTENT_REOPEN_PLACED_CAS_PASS")
