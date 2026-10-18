#!/usr/bin/env python3
"""Fail-closed Autocrafter GUI menu optimisation synthetic regression."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / "patches/perf-autocrafter-menu-once-per-tick.py"

STATUS = """private static ContainerData status(final Inventory inv, final BlockPos p) {
      return (ContainerData)(!(inv.player.level() instanceof ServerLevel) ? new SimpleContainerData(4) : new ContainerData() {
         public int get(int i) {
            if (!(inv.player.level() instanceof ServerLevel level)) {
               return 0;
            } else {
               NetworkRuntime var4 = WorldTopologyBridge.runtimeForAccessory(level, p);
               return switch (i) {
                  case 0 -> var4 == null ? 0 : WorldTopologyBridge.autocraftingActiveJobs(level, var4);
                  case 1 -> var4 == null ? 0 : WorldTopologyBridge.autocraftingBlockedJobs(level, var4);
                  case 2 -> var4 != null && var4.powered() ? 1 : 0;
                  case 3 -> level.getBlockState(p).is(dev.obsidiannetwork.ObsidianNetwork.AUTO_CHISELER.get()) ? 1 : 0;
                  default -> 0;
               };
            }
         }
         public void set(int i, int v) {}
         public int getCount() {return 4;}
      });
   }

   """
PREVIEW = """private static SimpleContainer preview(final Inventory inv, final BlockPos p) {
      return !(inv.player.level() instanceof ServerLevel) ? new SimpleContainer(1) : new SimpleContainer(1) {
         public ItemStack getItem(int slot) {
            if (slot == 0 && inv.player.level() instanceof ServerLevel level) {
               NetworkRuntime runtime = WorldTopologyBridge.runtimeForAccessory(level, p);
               if (runtime == null) {
                  return ItemStack.EMPTY;
               } else {
                  List<MinecraftAutocraftingService.JobView> jobs = WorldTopologyBridge.autocraftingService(level, runtime).jobViews(level);
                  if (jobs.isEmpty()) {
                     return ItemStack.EMPTY;
                  } else {
                     Identifier id = Identifier.tryParse(jobs.getFirst().output().itemId());
                     if (id == null) {
                        return ItemStack.EMPTY;
                     } else {
                        Item item = (Item)BuiltInRegistries.ITEM.getValue(id);
                        return item == null ? ItemStack.EMPTY : new ItemStack(item);
                     }
                  }
               }
            } else {
               return ItemStack.EMPTY;
            }
         }
      };
   }

   """
TAIL = """private static SimpleContainer upgrades(Inventory inv, BlockPos p) {
      return new SimpleContainer(1);
   }
   public boolean mayPickup(Player p) {
      return false;
   }
"""


class AutocrafterMenuCacheTest(unittest.TestCase):
    def test_patch_parses_and_scoped(self):
        source = PATCH.read_text()
        ast.parse(source)
        self.assertNotIn("setChunkForced(", source)
        self.assertNotIn("WirelessEnergyRuntime", source)
        self.assertNotIn("NetworkControllerMenu", source)

    def test_lazy_per_tick_status_and_readonly_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            java = root / "dev/obsidiannetwork/menu/AutocrafterMenu.java"
            java.parent.mkdir(parents=True)
            java.write_text("class FakeMenu {\n" + STATUS + PREVIEW + TAIL + "\n}")
            env = {**os.environ, "V1_SOURCE_ROOT": str(root)}
            run = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            actual = java.read_text()
            self.assertEqual(actual.count("XSXLABS_AUTOCRAFTER_MENU_TICK_QUERY_CACHE_V1"), 1)
            status = actual.split("private static ContainerData status(",1)[1].split("private static SimpleContainer preview(",1)[0]
            preview = actual.split("private static SimpleContainer preview(",1)[1].split("private static SimpleContainer upgrades(",1)[0]
            self.assertEqual(status.count("WorldTopologyBridge.runtimeForAccessory(level, p)"), 1)
            self.assertIn("if (i == 3) return level.getBlockState(p)", status)
            self.assertIn("if (cachedTick != tick)", status)
            self.assertIn("cachedActive = -1;", status)
            self.assertIn("cachedBlocked = -1;", status)
            self.assertIn("WorldTopologyBridge.autocraftingActiveJobs(level, cachedRuntime)", status)
            self.assertIn("WorldTopologyBridge.autocraftingBlockedJobs(level, cachedRuntime)", status)
            self.assertEqual(preview.count("WorldTopologyBridge.autocraftingService(level, runtime).jobViews(level)"), 1)
            self.assertIn("if (cachedTick != tick)", preview)
            self.assertIn("return cachedPreview.copy();", preview)
            self.assertIn("public boolean mayPickup(Player p)", actual)
            self.assertIn("return false;", actual)
            rerun = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True)
            self.assertNotEqual(rerun.returncode, 0, "duplicate application must fail closed")

    def test_source_drift_fails_without_rewriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            java = root / "dev/obsidiannetwork/menu/AutocrafterMenu.java"
            java.parent.mkdir(parents=True)
            original = "class FakeMenu {\n" + STATUS.replace(
                "WorldTopologyBridge.autocraftingActiveJobs(level, var4)",
                "changedJobCount(level, var4)") + PREVIEW + TAIL + "\n}"
            java.write_text(original)
            env = {**os.environ, "V1_SOURCE_ROOT": str(root)}
            run = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(original, java.read_text())


if __name__ == "__main__":
    unittest.main()
