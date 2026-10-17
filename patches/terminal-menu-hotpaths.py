#!/usr/bin/env python3
"""Optimize reconstructed terminal work, without changing transfer transactions.

Run after all upstream v1.6 feature/performance patches and before compilation.
Stable vanilla recipe matching is cached for an exact grid + recipe-map identity;
custom/special recipes and all result assembly still run on every change.
"""
from pathlib import Path
import os

root = Path(os.environ.get('V1_SOURCE_ROOT', 'work/src/main/java')) / 'dev/obsidiannetwork'
menu_path = root / 'menu/StorageTerminalMenu.java'
handler_path = root / 'network/ServerTerminalPayloadHandler.java'
s = menu_path.read_text()
h = handler_path.read_text()
marker = 'TERMINAL_MENU_HOTPATHS_V1'
assert marker not in s, 'terminal patch must be applied exactly once'
anchor = '   private boolean manualResultPredictionArmed;'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '''
   // TERMINAL_MENU_HOTPATHS_V1: count-only changes never alter an ItemKey's visual payload.
   private final java.util.HashSet<ItemKey> terminalVisualKeys = new java.util.HashSet<>();
   private long lastFluidSnapshotTick = Long.MIN_VALUE;
   private Object cachedCraftRecipeMap;
   private long cachedCraftRecipeTick = Long.MIN_VALUE;
   private ItemStack[] cachedCraftRecipeGrid;
   private java.util.List<RecipeHolder<CraftingRecipe>> cachedCraftRecipeCandidates;

   public boolean terminalVisualKeyKnown(ItemKey key) { return this.terminalVisualKeys.contains(key); }
   public void terminalVisualKeySent(ItemKey key) { this.terminalVisualKeys.add(key); }
   public void terminalVisualKeyRemoved(ItemKey key) { this.terminalVisualKeys.remove(key); }

   public boolean shouldSendFluidSnapshot(long tick, boolean force) {
      if (!force && this.lastFluidSnapshotTick == tick) return false;
      this.lastFluidSnapshotTick = tick;
      return true;
   }

   private java.util.List<RecipeHolder<CraftingRecipe>> craftRecipeCandidates(ServerLevel level, CraftingInput input) {
      Object recipeMap = level.recipeAccess().recipeMap();
      boolean same = this.cachedCraftRecipeMap == recipeMap && this.cachedCraftRecipeGrid != null &&
          this.cachedCraftRecipeTick == level.getGameTime();
      for (int slot = 0; same && slot < 9; slot++) {
         same = ItemStack.matches(this.cachedCraftRecipeGrid[slot], this.craftSlots.getItem(slot));
      }
      if (same) return this.cachedCraftRecipeCandidates;
      java.util.ArrayList<RecipeHolder<CraftingRecipe>> candidates = new java.util.ArrayList<>();
      for (RecipeHolder<CraftingRecipe> holder : level.recipeAccess().recipeMap().byType(RecipeType.CRAFTING)) {
         CraftingRecipe recipe = holder.value();
         // These exact vanilla implementations depend only on the crafting input.
         // Keep every dynamic/custom/special implementation in its original order.
         boolean stable = (recipe.getClass() == ShapedRecipe.class ||
             recipe.getClass() == net.minecraft.world.item.crafting.ShapelessRecipe.class) &&
             recipe.placementInfo().ingredients().stream().noneMatch(Ingredient::isCustom);
         if (!stable || recipe.matches(input, level)) candidates.add(holder);
      }
      ItemStack[] grid = new ItemStack[9];
      for (int slot = 0; slot < 9; slot++) grid[slot] = this.craftSlots.getItem(slot).copy();
      this.cachedCraftRecipeGrid = grid;
      this.cachedCraftRecipeMap = recipeMap;
      this.cachedCraftRecipeTick = level.getGameTime();
      this.cachedCraftRecipeCandidates = java.util.List.copyOf(candidates);
      return this.cachedCraftRecipeCandidates;
   }
''', 1)
loop = 'for (RecipeHolder<CraftingRecipe> holder : level.recipeAccess().recipeMap().byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {'
assert s.count(loop) == 1, 'final matchingCraftRecipes source anchor changed'
s = s.replace(loop, 'for (RecipeHolder<CraftingRecipe> holder : this.craftRecipeCandidates(level, input)) {', 1)

# A shift-craft click recomputes the authoritative result per craft; publish the
# final slot state once at the outer boundary rather than every intermediate grid.
# The output/input mutations, ResultSlot callbacks and recipe checks are unchanged.
anchor = '   private boolean manualResultPredictionArmed;'
s = s.replace(anchor, anchor + '\n   private int terminalBroadcastBatchDepth;', 1)
anchor = '   public void slotsChanged(Container container) {'
assert s.count(anchor) == 1
s = s.replace(anchor, '''   @Override
   public void broadcastChanges() {
      if (this.terminalBroadcastBatchDepth == 0) super.broadcastChanges();
   }

''' + anchor, 1)
start = s.index('         if (clickType == net.minecraft.world.inventory.ContainerInput.QUICK_MOVE) {')
end = s.index('         if (clickType == net.minecraft.world.inventory.ContainerInput.PICKUP && button == 0)', start)
block = s[start:end]
anchor = '            if (!player.level().isClientSide()) {'
assert block.count(anchor) == 1
block = block.replace(anchor, anchor + '\n               this.terminalBroadcastBatchDepth++;\n               try {', 1)
anchor = '               this.broadcastChanges();\n            }\n            return;'
assert block.count(anchor) == 1, 'shift craft outer sync boundary changed'
block = block.replace(anchor, '''               } finally {
                  this.terminalBroadcastBatchDepth--;
                  this.broadcastChanges();
               }
            }
            return;''', 1)
s = s[:start] + block + s[end:]
# Moving only part of a multi-item recipe output must not consume the recipe.
# Unlike vanilla crafting tables, this terminal rebuilds its passive result slot
# immediately and cannot leave the untransferred output there for later pickup.
anchor = '               if (!this.moveItemStackTo(source, 10, this.slots.size(), true)) {'
assert s.count(anchor) == 1
s = s.replace(anchor, '''               if (source.getCount() > 1 && !this.canMoveWholeCraftResult(source)) return ItemStack.EMPTY;
''' + anchor, 1)
anchor = '   public ItemStack quickMoveStack(Player player, int index) {'
assert s.count(anchor) == 1
s = s.replace(anchor, '''   private boolean canMoveWholeCraftResult(ItemStack result) {
      int remaining = result.getCount();
      for (int index = PLAYER_START; index < this.slots.size(); index++) {
         Slot slot = this.slots.get(index);
         if (!slot.mayPlace(result)) continue;
         ItemStack existing = slot.getItem();
         if (!existing.isEmpty() && !ItemStack.isSameItemSameComponents(existing, result)) continue;
         int limit = Math.min(result.getMaxStackSize(), slot.getMaxStackSize(result));
         remaining -= Math.max(0, limit - existing.getCount());
         if (remaining <= 0) return true;
      }
      return false;
   }

''' + anchor, 1)

# Avoid graph-wide fluid discovery for each item in the same rapid-deposit burst.
# Resync always forces a snapshot, including screen resize/reinitialization.
needle = 'net.neoforged.neoforge.network.PacketDistributor.sendToPlayer(player,new FluidTerminalSnapshotPayload(menu.terminalId(),menu.sessionId(),dev.obsidiannetwork.core.NetworkFluidTerminalAccess.snapshot(level,menu.terminalPos())));'
assert h.count(needle) == 1, 'fluid snapshot dispatch anchor changed'
h = h.replace(needle, 'sendFluidSnapshot(player,menu,level,frame.message() instanceof TerminalProtocol.ResyncRequest);', 1)
extract = 'if(frame.message() instanceof TerminalProtocol.TransferRequest fr && fr.amount()==-1000L){if(runtime!=null&&runtime.powered())dev.obsidiannetwork.core.NetworkFluidTerminalAccess.extractBucket(level,menu.terminalPos(),runtime,player,fr.key(),fr.insert());return;}'
assert h.count(extract) == 1
h = h.replace(extract, 'if(frame.message() instanceof TerminalProtocol.TransferRequest fr && fr.amount()==-1000L){if(runtime!=null&&runtime.powered()){dev.obsidiannetwork.core.NetworkFluidTerminalAccess.extractBucket(level,menu.terminalPos(),runtime,player,fr.key(),fr.insert());sendFluidSnapshot(player,menu,level,true);}return;}', 1)
insert = 'dev.obsidiannetwork.core.NetworkFluidTerminalAccess.insertFilledBucket(level,menu.terminalPos(),runtime,player,sr.slot(),sr.amount())){return;}'
assert h.count(insert) == 1
h = h.replace(insert, 'dev.obsidiannetwork.core.NetworkFluidTerminalAccess.insertFilledBucket(level,menu.terminalPos(),runtime,player,sr.slot(),sr.amount())){sendFluidSnapshot(player,menu,level,true);return;}', 1)
anchor = '   private static void sendActiveJobs('
assert h.count(anchor) == 1
h = h.replace(anchor, '''   private static void sendFluidSnapshot(ServerPlayer player, StorageTerminalMenu menu, ServerLevel level, boolean force) {
      if (menu.shouldSendFluidSnapshot(level.getGameTime(), force)) {
         ''' + needle + '''
      }
   }

''' + anchor, 1)

# Preserve full bootstrap/resync metadata; suppress immutable metadata already
# sent to this menu only when draining count deltas.
anchor = '      MinecraftItemStackCodec codec = new MinecraftItemStackCodec(level.registryAccess());\n      ArrayList<TerminalProtocol.DurabilityEntry> rows = new ArrayList<>();'
assert h.count(anchor) == 1
h = h.replace(anchor, '''      sendDurability(player, terminalId, sessionId, nonce, level, runtime, keys, false);
   }

   private static void sendDurability(
      ServerPlayer player, long terminalId, long sessionId, long nonce, ServerLevel level, NetworkRuntime runtime, Collection<ItemKey> keys, boolean changedOnly
   ) {
      StorageTerminalMenu boundMenu = player.containerMenu instanceof StorageTerminalMenu menu &&
          menu.terminalId() == terminalId && menu.sessionId() == sessionId ? menu : null;
''' + anchor, 1)
anchor = '      for (ItemKey key : keys) {\n         byte[] payload = runtime.descriptors().payload(key).orElse(null);'
assert h.count(anchor) == 1
h = h.replace(anchor, '''      for (ItemKey key : new java.util.LinkedHashSet<>(keys)) {
         if (changedOnly && boundMenu != null && boundMenu.terminalVisualKeyKnown(key)) continue;
         byte[] payload = runtime.descriptors().payload(key).orElse(null);''', 1)
anchor = '         PacketDistributor.sendToPlayer(player, TerminalWirePayload.of(frame), new CustomPacketPayload[0]);\n      }\n   }\n\n   public static void pushCraftables'
assert h.count(anchor) == 1, 'metadata packet boundary changed'
h = h.replace(anchor, '''         PacketDistributor.sendToPlayer(player, TerminalWirePayload.of(frame), new CustomPacketPayload[0]);
         if (boundMenu != null) for (TerminalProtocol.DurabilityEntry row : part) boundMenu.terminalVisualKeySent(row.key());
      }
   }

   public static void pushCraftables''', 1)
needle = 'sendDurability(viewer, viewerFlow.terminalId(), viewerFlow.sessionId(), nonce, level, runtime, changedKeys);'
assert h.count(needle) == 1
h = h.replace(needle, 'sendDurability(viewer, viewerFlow.terminalId(), viewerFlow.sessionId(), nonce, level, runtime, changedKeys, true);', 1)
anchor = '''                        for (IndexDelta d : batch.deltas()) {
                           changedKeys.add(d.key());'''
assert h.count(anchor) == 1
h = h.replace(anchor, '''                        for (IndexDelta d : batch.deltas()) {
                           if (d.amountAfter() == 0L) menu.terminalVisualKeyRemoved(d.key());
                           changedKeys.add(d.key());''', 1)
assert s.count('this.craftRecipeCandidates(level, input)') == 1
assert 'recipe.matches(input, level)' in s
assert 'recipe.assemble(input)' in s
menu_path.write_text(s)
handler_path.write_text(h)
print('TERMINAL_MENU_HOTPATHS_V1 PASS vanilla_candidate_cache=true dynamic_recipes_live=true batched_shift_sync=true fluid_snapshot_per_tick=true immutable_visual_metadata=true')
