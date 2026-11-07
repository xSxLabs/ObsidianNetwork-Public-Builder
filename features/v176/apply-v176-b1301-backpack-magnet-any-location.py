#!/usr/bin/env python3
"""B1301: make enabled backpack magnet work from every owned location.

Existing B1234 already selects CHEST / Curios / MAIN_HAND / OFF_HAND; B1273
already supplies the autonomous placed BE ticker. Extend ONLY magnet selection
and CAS persistence to ordinary PlayerInventory slots (main+hotbar).
Preserve priority and all existing equipped, placed, range, item filters,
batching, drop-shrink-after-persist, GUI and cable behavior. No world scan
if no live enabled bag; only one 36/41-slot lightweight inventory pass/tick.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
eq=root/"backpack/V176BackpackEquipped.java"
mag=root/"backpack/V176BackpackMagnetEvents.java"
placed=root/"backpack/V176BackpackPlacedMagnet.java"
block=root/"backpack/NetworkBackpackBlock.java"
be=root/"backpack/NetworkBackpackBlockEntity.java"

src=eq.read_text("utf-8")
mag_src=mag.read_text("utf-8")
placed_src=placed.read_text("utf-8")
block_src=block.read_text("utf-8")
be_src=be.read_text("utf-8")

for required in (
 "public static Located activeMagnet(ServerPlayer player)",
 "V176BackpackCuriosCompat",
 "case CHEST->", "case CURIOS_BACK->",
 "case MAIN_HAND->", "case OFF_HAND->",
 "player.getItemInHand(InteractionHand.OFF_HAND)",
 "V176BackpackCells.magnetEnabled(off)",
 "public static Located active(ServerPlayer player)",
):
 assert required in src,("B1301_EXISTING_MAGNET_SOURCE_DRIFT",required)
for required in (
 "V176BackpackEquipped.activeMagnet(player)",
 "location.persist(player,updated);",
 "remainder.shrink(pickup.amount());",
 "private static final double RANGE=8.0D;",
 "if(pickups.isEmpty())return",
 "V176BackpackCells.magnetAccepts(",
):
 assert required in mag_src,("B1301_PLAYER_MAGNET_DRIFT",required)
for required in (
 "if(!(world instanceof ServerLevel server)||!bag.xsxPlacedMagnetActive())",
 "bag.replaceBackpack(original,next)",
 "remainder.shrink(pickup.amount())",
 "private static final double RANGE=8.0D;",
):
 assert required in placed_src,("B1301_PLACED_MAGNET_DRIFT",required)
assert "V176BackpackPlacedMagnet::tick" in block_src
assert "xsxPlacedMagnetActive()" in be_src
assert "INVENTORY" not in src and "B1301_INVENTORY" not in src

def swap(old,new,label):
 global src
 count=src.count(old)
 assert count==1,("B1301_MAGNET_SOURCE_DRIFT",label,count)
 src=src.replace(old,new,1)

swap("public enum Where { CHEST, CURIOS_BACK, MAIN_HAND, OFF_HAND }",
     "public enum Where { CHEST, CURIOS_BACK, MAIN_HAND, OFF_HAND, INVENTORY }",
     "new_inventory_location")

# This is an exact slot CAS. Same matching/rollback behavior as CHEST/HANDS:
# any concurrent GUI or other modification vetoes world-item consumption.
swap("""    case OFF_HAND->{
     if(!ItemStack.matches(player.getItemInHand(InteractionHand.OFF_HAND),stack))
      throw new IllegalStateException("off-hand backpack changed during transaction");
     player.setItemInHand(InteractionHand.OFF_HAND,updated);
    }""",
"""    case OFF_HAND->{
     if(!ItemStack.matches(player.getItemInHand(InteractionHand.OFF_HAND),stack))
      throw new IllegalStateException("off-hand backpack changed during transaction");
     player.setItemInHand(InteractionHand.OFF_HAND,updated);
    }
    // B1301_INVENTORY_MAGNET_CAS: location is a real server inventory slot.
    // Only replace the matching original bag, never a backpack in another
    // slot; scanner does not mutate containers or send chat/network spam.
    case INVENTORY->{
     var inventory=player.getInventory();
     if(index<0||index>=inventory.getContainerSize()
        ||!ItemStack.matches(inventory.getItem(index),stack))
      throw new IllegalStateException("inventory backpack changed during transaction");
     inventory.setItem(index,updated);
    }""","inventory_atomic_persist")

# Target only the magnet-specific search. active() and worn() are used
# by GUI/shortcut commands and intentionally remain unchanged.
start=src.index(" public static Located activeMagnet(ServerPlayer player){")
end=src.index(" public static Located active(ServerPlayer player){",start)
region=src[start:end]
assert region.count("  return null;")==1
assert region.count("return new Located(Where.OFF_HAND,-1,off);")==1
assert region.rstrip().endswith("}")
region=region.replace(
"""  return null;
 }""",
"""  // B1301_INVENTORY_MAGNET_DISCOVERY: hotbar + ordinary inventory slots.
  // Already-selected hand and worn/Curios bags retain their old priority.
  // A fixed <=41-slot scan per player tick is cheaper than a world entity
  // query and never invokes any Storage Cell decode for non-backpack items.
  var inventory=player.getInventory();
  for(int i=0;i<inventory.getContainerSize();i++){
   ItemStack candidate=inventory.getItem(i);
   if(candidate.getItem() instanceof NetworkBackpackItem
       &&V176BackpackCells.magnetEnabled(candidate))
    return new Located(Where.INVENTORY,i,candidate);
  }
  return null;
 }""")
assert "return new Located(Where.INVENTORY,i,candidate)" in region
src=src[:start]+region+src[end:]
assert src.count("B1301_INVENTORY_MAGNET_CAS")==1
assert src.count("B1301_INVENTORY_MAGNET_DISCOVERY")==1
assert "location.persist(player,updated);" in mag_src
assert "bag.replaceBackpack(original,next)" in placed_src
# Source validation completed without a write: change only the one Java file.
eq.write_text(src,encoding="utf-8")
print("B1301_BACKPACK_MAGNET_WORN_CURIOS_HAND_INVENTORY_PLACED_CAS_8_BLOCKS_PASS")
