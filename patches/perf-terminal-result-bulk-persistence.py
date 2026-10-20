#!/usr/bin/env python3
"""Batch result-slot persistence: skip per-slot writes while the crafting result is being consumed.

The terminal already has a batchingCraftMutation window around ResultSlot.onTake,
followed by a full slotsChanged invocation and a transactional setCraftGrid call.
Before this patch PersistentCraftingContainer.persistSlot still wrote each changed
slot individually *inside* that window. Flush once in finally, also on exceptions
after a partial mutation, then let the existing recipe/result sync proceed.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/menu/StorageTerminalMenu.java"
s = p.read_text(encoding="utf-8")
marker = "XSXLABS_CRAFT_RESULT_BATCH_PERSIST_V1"
assert marker not in s and "XSXLABS_TERMINAL_BULK_GRID_PERSISTENCE_V1" in s
assert s.count("private final class PersistentCraftingContainer extends TransientCraftingContainer") == 1
assert s.count("private final class NetworkResultSlot extends ResultSlot") == 1
assert s.count("this.batchingCraftMutation = true;") >= 1
assert s.count("public void setCraftGrid(ItemStack[] stacks)") == 0
assert s.count("private void persistSlot(int slot) {") == 1

start=s.index("private final class PersistentCraftingContainer extends TransientCraftingContainer")
section=s[start:]
old="""private void persistSlot(int slot) {
         TerminalInventoryBlockEntity persistent = this.backing();"""
new="""private void persistSlot(int slot) {
         // XSXLABS_CRAFT_RESULT_BATCH_PERSIST_V1
         // ResultSlot.onTake updates multiple slots, then commits the final grid.
         if (StorageTerminalMenu.this.batchingCraftMutation) return;
         TerminalInventoryBlockEntity persistent = this.backing();"""
assert section.count(old)==1
s=s[:start]+section.replace(old,new,1)

# Only call this from the onTake finally: successful and exceptional partial
# consumptions must both persist their final in-memory grid.
helper="""
   private void xsxPersistCraftGridAfterResultTake() {
      if (!(this.player instanceof ServerPlayer)) return;
      ServerLevel level = this.terminalServerLevel();
      if (level == null || !level.hasChunkAt(this.terminalPos)) return;
      if (!(level.getBlockEntity(this.terminalPos) instanceof TerminalInventoryBlockEntity persistent)) return;
      ItemStack[] items = new ItemStack[9];
      for (int i=0; i<9; ++i) items[i] = this.craftSlots.getItem(i);
      persistent.setCraftGrid(items);
   }

"""
anchor="private final class NetworkResultSlot extends ResultSlot"
assert s.count(anchor)==1
s=s.replace(anchor,helper+"   "+anchor,1)
start=s.index(anchor)
end=s.index("private final class PersistentCraftingContainer",start)
part=s[start:end]
old_finally="""} finally {
            StorageTerminalMenu.this.batchingCraftMutation = false;
         }"""
new_finally="""} finally {
            StorageTerminalMenu.this.batchingCraftMutation = false;
            StorageTerminalMenu.this.xsxPersistCraftGridAfterResultTake();
         }"""
assert part.count(old_finally)==1, "ResultSlot.onTake finally changed; refuse unsafe batching"
part=part.replace(old_finally,new_finally,1)
assert "StorageTerminalMenu.this.slotsChanged(StorageTerminalMenu.this.craftSlots);" in part
s=s[:start]+part+s[end:]
assert s.count(marker)==1 and s.count("xsxPersistCraftGridAfterResultTake();")==1
assert s.count("persistent.setCraftGrid(items);")==1
p.write_text(s,encoding="utf-8")
print("CRAFT_RESULT_BATCH_PERSIST_V1 PASS: no per-slot writes in onTake, exception-safe final-grid flush")