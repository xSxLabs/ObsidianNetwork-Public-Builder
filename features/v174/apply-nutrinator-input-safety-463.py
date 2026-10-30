#!/usr/bin/env python3
"""B463: Nutrinator food-only external item automation.

The real helmet/feeding paste store and 16 upgrades remain UI-accessible,
but item pipes must never pull a player's armor or the speed-card slot.
Input is true modded FOOD-component items, all faces. No FE/fluid bypass.
"""
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"nutrition/NutrinatorBlockEntity.java"
s=p.read_text(encoding="utf-8")
def rep(old,new):
 global s
 assert s.count(old)==1,("B463_NUTRINATOR_CAPABILITY_DRIFT",s.count(old),old[:110])
 s=s.replace(old,new,1)
rep('import net.minecraft.core.BlockPos;',
    'import net.minecraft.core.BlockPos;\nimport net.minecraft.core.Direction;')
rep('import net.minecraft.world.Container;',
    'import net.minecraft.world.WorldlyContainer;')
rep('public final class NutrinatorBlockEntity extends BlockEntity implements Container {',
    '''public final class NutrinatorBlockEntity extends BlockEntity implements WorldlyContainer {
  // B463_FOOD_INPUT_ONLY: only food slot zero is visible to sided item cables.
  private static final int[] EXTERNAL_INPUT_SLOTS={0};''')
rep(' @Override public int getContainerSize(){return 27;}',
    '''  @Override public int[] getSlotsForFace(Direction side){
   return EXTERNAL_INPUT_SLOTS.clone();
  }
  @Override public boolean canPlaceItemThroughFace(int slot,ItemStack stack,Direction side){
   return slot==0&&isFood(stack);
  }
  @Override public boolean canTakeItemThroughFace(int slot,ItemStack stack,Direction side){
   // Neither helmet nor upgrades nor edible input may be stolen by a pipe.
   return false;
  }
  @Override public int getContainerSize(){return 27;}''')
p.write_text(s,encoding="utf-8")
assert "B463_FOOD_INPUT_ONLY" in p.read_text()
print("B463_NUTRINATOR_ITEM_AUTOMATION_PASS: modded food input, helmet/speed protected")
