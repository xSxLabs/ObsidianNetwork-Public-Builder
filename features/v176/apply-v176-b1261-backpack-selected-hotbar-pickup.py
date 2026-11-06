#!/usr/bin/env python3
"""B1261: sneak-right-click a placed Backpack into the selected EMPTY hotbar slot.

Server authoritative; no inventory search, overflow drop, replacement of a
held item, or changes to the stored Backpack's cells, modules or components.
The BE is emptied before block removal to prevent its drop hook from cloning
the populated item. The original item is restored on removal failure.
This is applied after all existing v1.7.6 Backpack changes and fails closed.
"""
import os
from pathlib import Path

path = Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack/NetworkBackpackBlock.java"
src = path.read_text(encoding="utf-8")

old = """  if(player.isShiftKeyDown()){
   ItemStack original=bag.takeBackpack();
   if(original.isEmpty())return InteractionResult.FAIL;
   if(!server.getInventory().add(original))
    net.minecraft.world.Containers.dropItemStack(world,server.getX(),server.getY(),server.getZ(),original);
   world.removeBlock(pos,false);
   return InteractionResult.SUCCESS;
  }"""

new = """  if(player.isShiftKeyDown()){
   // Take ONLY into the currently selected, empty main-hand hotbar slot.
   // No search, forced stacking, overwriting or world-drop fallback.
   var inventory=server.getInventory();
   int selected=inventory.getSelectedSlot();
   if(!net.minecraft.world.entity.player.Inventory.isHotbarSlot(selected)
       ||!inventory.getItem(selected).isEmpty())return InteractionResult.FAIL;
   if(bag.getBackpack().isEmpty())return InteractionResult.FAIL;
   // Ownership leaves the BE before block removal, so preRemoveSideEffects
   // cannot emit a second, fully populated Backpack item.
   ItemStack original=bag.takeBackpack();
   if(original.isEmpty())return InteractionResult.FAIL;
   inventory.setItem(selected,original);
   if(!world.removeBlock(pos,false)){
    // Failed world removal: put the EXACT original stack back into the BE.
    // Never leave a second inventory owner or lose cells/upgrades.
    inventory.setItem(selected,ItemStack.EMPTY);
    bag.setBackpack(original);
    return InteractionResult.FAIL;
   }
   return InteractionResult.SUCCESS;
  }"""

assert src.count(old)==1,("B1261_BACKPACK_PICKUP_SOURCE_DRIFT",src.count(old))
assert "public static InteractionResult interactAt(" in src
assert "public ItemStack getBackpack()" not in src
assert src.count("useWithoutItem(")==1
assert src.count("useItemOn(")==1
assert "V176BackpackOpen.openPlaced(server,pos)" in src
assert "server.getInventory().add(original)" in src
src=src.replace(old,new,1)
assert "server.getInventory().add(original)" not in src
assert "Containers.dropItemStack" not in src
assert "bag.takeBackpack()" in src and "bag.setBackpack(original);" in src
path.write_text(src,encoding="utf-8")
print("B1261_BACKPACK_SELECTED_EMPTY_HOTBAR_PICKUP_FAIL_CLOSED_PASS")
