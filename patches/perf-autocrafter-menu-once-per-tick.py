#!/usr/bin/env python3
"""Reduce repeat server-side queries from an OPEN Autocrafter GUI.

Reconstructed AutocrafterMenu.ContainerData.get previously resolves accessory
topology on every status field read (3 times per menu broadcast) while preview
getItem rebuilds a complete autocrafting job view on every slot read.

Cache *only per open menu instance and current server game tick*; never globally
cache a world, player, NetworkRuntime, or source ItemStack. Independent status
fields compute lazily so initial autoChiseler() only reads the blockstate.
Preview remains read-only/unobtainable and returns a defensive ItemStack copy.
Production job scheduling, FE, reserved amounts and network topology untouched.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
path = root / "menu/AutocrafterMenu.java"
source = path.read_text(encoding="utf-8")

def replace_method(start_marker, end_marker, required, replacement):
    global source
    assert source.count(start_marker) == 1 and source.count(end_marker) == 1, (
        "autocrafter menu method boundary drift", start_marker, end_marker)
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    old = source[start:end]
    for anchor in required:
        assert old.count(anchor) == 1, ("autocrafter menu anchor drift", anchor, old.count(anchor))
    assert "XSXLABS_AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1" not in old
    source = source[:start] + replacement + source[end:]


replace_method(
    "private static ContainerData status(final Inventory inv, final BlockPos p) {",
    "private static SimpleContainer preview(final Inventory inv, final BlockPos p) {",
    (
        "NetworkRuntime var4 = WorldTopologyBridge.runtimeForAccessory(level, p);",
        "WorldTopologyBridge.autocraftingActiveJobs(level, var4)",
        "WorldTopologyBridge.autocraftingBlockedJobs(level, var4)",
        "var4 != null && var4.powered()",
        "level.getBlockState(p).is(dev.obsidiannetwork.ObsidianNetwork.AUTO_CHISELER.get())",
        "public int getCount()",
    ),
    """private static ContainerData status(final Inventory inv, final BlockPos p) {
      return (ContainerData)(!(inv.player.level() instanceof ServerLevel) ? new SimpleContainerData(4) : new ContainerData() {
         // XSXLABS_AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1: one runtime lookup per tick per GUI.
         private long cachedTick = Long.MIN_VALUE;
         private NetworkRuntime cachedRuntime;
         private int cachedActive = -1;
         private int cachedBlocked = -1;

         public int get(int i) {
            if (!(inv.player.level() instanceof ServerLevel level)) return 0;
            // The constructor queries this field to position the speed-upgrade slot.
            // Keep it independent of autocrafting/job scans at GUI open time.
            if (i == 3) return level.getBlockState(p).is(dev.obsidiannetwork.ObsidianNetwork.AUTO_CHISELER.get()) ? 1 : 0;
            if (i < 0 || i > 2) return 0;
            long tick = level.getGameTime();
            if (cachedTick != tick) {
               cachedRuntime = WorldTopologyBridge.runtimeForAccessory(level, p);
               cachedActive = -1;
               cachedBlocked = -1;
               cachedTick = tick;
            }
            return switch (i) {
               case 0 -> {
                  if (cachedActive < 0) cachedActive = cachedRuntime == null ? 0 :
                     WorldTopologyBridge.autocraftingActiveJobs(level, cachedRuntime);
                  yield cachedActive;
               }
               case 1 -> {
                  if (cachedBlocked < 0) cachedBlocked = cachedRuntime == null ? 0 :
                     WorldTopologyBridge.autocraftingBlockedJobs(level, cachedRuntime);
                  yield cachedBlocked;
               }
               case 2 -> cachedRuntime != null && cachedRuntime.powered() ? 1 : 0;
               default -> 0;
            };
         }

         public void set(int i, int v) {
         }

         public int getCount() {
            return 4;
         }
      });
   }

   """
)
replace_method(
    "private static SimpleContainer preview(final Inventory inv, final BlockPos p) {",
    "private static SimpleContainer upgrades(Inventory inv, BlockPos p) {",
    (
        "WorldTopologyBridge.runtimeForAccessory(level, p)",
        "WorldTopologyBridge.autocraftingService(level, runtime).jobViews(level)",
        "Identifier.tryParse(jobs.getFirst().output().itemId())",
        "new ItemStack(item)",
        "public ItemStack getItem(int slot)",
    ),
    """private static SimpleContainer preview(final Inventory inv, final BlockPos p) {
      return !(inv.player.level() instanceof ServerLevel) ? new SimpleContainer(1) : new SimpleContainer(1) {
         // Read-only slot: resolve the job view no more than once per server tick.
         private long cachedTick = Long.MIN_VALUE;
         private ItemStack cachedPreview = ItemStack.EMPTY;

         public ItemStack getItem(int slot) {
            if (slot != 0 || !(inv.player.level() instanceof ServerLevel level)) return ItemStack.EMPTY;
            long tick = level.getGameTime();
            if (cachedTick != tick) {
               ItemStack next = ItemStack.EMPTY;
               NetworkRuntime runtime = WorldTopologyBridge.runtimeForAccessory(level, p);
               if (runtime != null) {
                  List<MinecraftAutocraftingService.JobView> jobs =
                     WorldTopologyBridge.autocraftingService(level, runtime).jobViews(level);
                  if (!jobs.isEmpty()) {
                     Identifier id = Identifier.tryParse(jobs.getFirst().output().itemId());
                     if (id != null) {
                        Item item = (Item)BuiltInRegistries.ITEM.getValue(id);
                        if (item != null) next = new ItemStack(item);
                     }
                  }
               }
               cachedPreview = next;
               cachedTick = tick;
            }
            // Do not expose the mutable cached display stack to consumers.
            return cachedPreview.copy();
         }
      };
   }

   """
)
assert source.count("XSXLABS_AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1") == 1
assert "public boolean mayPickup(Player p)" in source and "return false;" in source
path.write_text(source, encoding="utf-8")
print("AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1 PASS")
