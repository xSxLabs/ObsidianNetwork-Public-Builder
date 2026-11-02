"""Fail-closed static wiring checks; real NeoForge compile and GameTests remain required."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features" / "v176"

class BackpackPipeline809(unittest.TestCase):
    def source(self, filename):
        return (FEATURES / filename).read_text(encoding="utf-8")

    def test_real_cell_and_curios_modules_installed(self):
        installer = self.source("install-v176-feature-rules.py")
        for name in ("V176BackpackCells.java", "V176BackpackEquipped.java",
                     "V176BackpackCuriosCompat.java", "V176BackpackMagnetEvents.java"):
            self.assertIn(name, installer)

    def test_cable_installed_after_backpack_block_and_cell_modules(self):
        workflow = (ROOT / ".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
        script_names = ("install-v176-feature-rules.py",
                        "apply-v176-backpack-world-placement.py",
                        "apply-v176-backpack-cables.py")
        offsets = [workflow.index("python3 features/v176/" + name) for name in script_names]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(workflow.count("python3 features/v176/apply-v176-backpack-cables.py"), 1)

    def test_all_equipped_item_writes_reject_stale_sources(self):
        equipped = self.source("java/V176BackpackEquipped.java")
        curios = self.source("java/V176BackpackCuriosCompat.java")
        for owner in ("CHEST", "MAIN_HAND", "OFF_HAND"):
            self.assertIn("case " + owner, equipped)
        self.assertGreaterEqual(equipped.count("ItemStack.matches("), 3)
        self.assertIn("ItemStack.matches(", curios)
        self.assertIn('cls.getMethod("save",ServerPlayer.class,int.class,ItemStack.class,ItemStack.class)', equipped)

    def test_cable_handler_entry_order_is_stable(self):
        cells = self.source("java/V176BackpackCells.java")
        self.assertIn("sorted.sort(java.util.Comparator", cells)
        self.assertIn("java.util.Arrays.compareUnsigned", cells)
        self.assertNotIn("return List.copyOf(data.values());", cells)

    def test_magnet_refreshes_source_after_each_write(self):
        magnet = self.source("java/V176BackpackMagnetEvents.java")
        self.assertLess(magnet.index("location.persist(player,updated);"),
                        magnet.index("location=V176BackpackEquipped.active(player);"))

if __name__ == "__main__":
    unittest.main()
