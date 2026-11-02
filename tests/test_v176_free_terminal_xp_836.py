"""Pure-source regression checks for XP-free v1.7.6 special terminals."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "features/v176/apply-v176-free-terminal-xp-836.py"
spec = spec_from_file_location("v176_free_terminal_xp", SCRIPT)
patch = module_from_spec(spec)
spec.loader.exec_module(patch)

DECONSTRUCTION = """
public int get() {
    Optional<DeconstructionTerminalMenu.Plan> q = DeconstructionTerminalMenu.this.serverPlan(inv.player);
    DeconstructionTerminalMenu.this.syncPreview(q);
    return q.<Integer>map(p -> p.cost).orElse(0);
}
public boolean clickMenuButton(Player player, int id) {
    DeconstructionTerminalMenu.Plan p = pOpt.get();
    if (!sp.getAbilities().instabuild && sp.experienceLevel < p.cost) {
        XSX_LOG.warn("[xSxDiag] click rejected: xp need={} have={}", p.cost, sp.experienceLevel);
        return false;
    } else {
        ArrayList<ItemStack> pending = new ArrayList<>();
        input.shrink(p.consume);
        if (!sp.getAbilities().instabuild) {
            sp.giveExperienceLevels(-p.cost);
        }
        this.machine.setItem(0, input);
    }
}
public int xpCost() {
    return this.cost;
}
"""

DISENCHANTING = """
private int serverCost(Player p) {
    List<Entry<Holder<Enchantment>, Integer>> e = this.entries();
    if (e.isEmpty()) {
        return 0;
    } else {
        int i = Math.max(0, Math.min(this.selected, e.size() - 1));
        int lvl = e.get(i).getValue();
        return Math.max(1, Math.min(5, (lvl + 1) / 2));
    }
}
public boolean clickMenuButton(Player p, int id) {
    int xp = this.serverCost(p);
    if (!sp.getAbilities().instabuild && sp.experienceLevel < xp) {
        return false;
    } else {
        if (rt.storage().extract(plain.key(), 1L) != 1L) return false;
        this.machine.setItem(1, out);
        if (!sp.getAbilities().instabuild) {
            sp.giveExperienceLevels(-xp);
        }
    }
}
"""


class FreeSpecialTerminalXpTests(unittest.TestCase):
    def test_deconstruction_price_gui_and_server_are_zero(self):
        result = patch.patch_deconstruction(DECONSTRUCTION)
        self.assertIn("return 0;", result)
        self.assertIn("public int xpCost() {\n    return 0;", result)
        self.assertNotIn("sp.experienceLevel <", result)
        self.assertNotIn("giveExperienceLevels(", result)
        self.assertIn("this.syncPreview(q)", result)
        self.assertIn("input.shrink(p.consume)", result)

    def test_disenchanting_price_gui_and_server_are_zero(self):
        result = patch.patch_disenchanting(DISENCHANTING)
        self.assertIn("int lvl = e.get(i).getValue();\n        return 0;", result)
        self.assertNotIn("sp.experienceLevel <", result)
        self.assertNotIn("giveExperienceLevels(", result)
        self.assertIn("rt.storage().extract(plain.key(), 1L)", result)
        self.assertIn("this.machine.setItem(1, out)", result)

    def test_fails_closed_if_source_changes(self):
        with self.assertRaisesRegex(AssertionError, "expected 1 source match"):
            patch.patch_deconstruction(DECONSTRUCTION.replace("p.cost", "p.unknown", 1))
        with self.assertRaisesRegex(AssertionError, "expected 1 source match"):
            patch.patch_disenchanting(DISENCHANTING.replace("-xp", "-2"))


if __name__ == "__main__":
    unittest.main()
