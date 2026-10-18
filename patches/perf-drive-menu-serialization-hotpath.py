#!/usr/bin/env python3
"""Avoid repeated 64k Equipment/Storage cell serialization in a Drive GUI.

The original DriveMenu.getItem delegates each read to cellInventory.getResource,
which materializes full live cell payload (potentially thousands of items).
Cache ONLY one per-menu read-only slot snapshot per tick, invalidated whenever
the menu changes a slot. The BE's authoritative getItem/mutators, transaction
and full save/remove/drop serialization remain unchanged. Also make
occupiedSlots inspect unchanged slot shells, not materialized cell contents.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
drive = root / "blockentity/StorageDriveBlockEntity.java"
menu = root / "menu/DriveMenu.java"

def change(file, old, new):
    s = file.read_text(encoding="utf-8")
    assert s.count(old) == 1, (str(file), old[:95], s.count(old))
    file.write_text(s.replace(old, new, 1), encoding="utf-8")

change(drive,
"""   public int occupiedSlots() {
      int n = 0;

      for (int i = 0; i < StorageDriveRuntime.SLOTS; i++) {
         if (!((ItemResource)this.cellInventory.getResource(i)).isEmpty()) {
            n++;
         }
      }

      return n;
   }""",
"""   public int occupiedSlots() {
      // XSXLABS_DRIVE_FAST_OCCUPANCY_V1: slot count reads the item shells,
      // not the complete live cell NBT (materializeSlot serializes every cell).
      int n = 0;
      for (ItemStack shell : this.cellInventory.copyToList()) {
         if (!shell.isEmpty()) n++;
      }
      return n;
   }""")

change(menu,
"""   private static final class DriveContainer implements Container {
      private final StorageDriveBlockEntity be;

      private DriveContainer(StorageDriveBlockEntity be) {""",
"""   private static final class DriveContainer implements Container {
      private final StorageDriveBlockEntity be;
      // XSXLABS_DRIVE_GUI_TICK_SNAPSHOT_V1: immutable per-menu tick view.
      // Mutations always use the live BE and invalidate these read-only values.
      private final ItemStack[] cached = new ItemStack[8];
      private final boolean[] present = new boolean[8];
      private long cachedTick = Long.MIN_VALUE;

      private void invalidate() {
         cachedTick = Long.MIN_VALUE;
         java.util.Arrays.fill(present, false);
      }

      private DriveContainer(StorageDriveBlockEntity be) {""")

change(menu,
"""      public ItemStack getItem(int slot) {
         return this.be.cellStack(slot);
      }""",
"""      public ItemStack getItem(int slot) {
         if (slot < 0 || slot >= 8) return ItemStack.EMPTY;
         if (this.be.getLevel() == null) return this.be.cellStack(slot);
         long tick = this.be.getLevel().getGameTime();
         if (cachedTick != tick) {
            java.util.Arrays.fill(present, false);
            cachedTick = tick;
         }
         if (!present[slot]) {
            cached[slot] = this.be.cellStack(slot);
            present[slot] = true;
         }
         // Defensive copy: never expose or mutate the cached stack instance.
         return cached[slot].copy();
      }""")

change(menu,
"""      public ItemStack removeItem(int slot, int count) {
         return count <= 0 ? ItemStack.EMPTY : this.be.removeCellAt(slot);
      }""",
"""      public ItemStack removeItem(int slot, int count) {
         if (count <= 0) return ItemStack.EMPTY;
         ItemStack result = this.be.removeCellAt(slot);
         invalidate();
         return result;
      }""")
change(menu,
"""      public ItemStack removeItemNoUpdate(int slot) {
         return this.be.removeCellAt(slot);
      }""",
"""      public ItemStack removeItemNoUpdate(int slot) {
         ItemStack result = this.be.removeCellAt(slot);
         invalidate();
         return result;
      }""")

change(menu,
"""      public void setChanged() {
         this.be.setChanged();
      }""",
"""      public void setChanged() {
         invalidate();
         this.be.setChanged();
      }""")
change(menu,
"""      public void setItem(int slot, ItemStack stack) {
         ItemStack current = this.be.cellStack(slot);""",
"""      public void setItem(int slot, ItemStack stack) {
         invalidate();
         ItemStack current = this.be.cellStack(slot);""")
change(menu,
"""      public void clearContent() {
         for (int i = 0; i < CELL_SLOTS; i++) {""",
"""      public void clearContent() {
         invalidate();
         for (int i = 0; i < CELL_SLOTS; i++) {""")
print("DRIVE_FAST_OCCUPANCY_V1 PASS; DRIVE_GUI_TICK_SNAPSHOT_V1 PASS")
