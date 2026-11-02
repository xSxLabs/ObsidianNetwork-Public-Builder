"""Static integration tests for 729-Cobblestone vanilla Obsidian recipe."""
import ast
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Cobble815(unittest.TestCase):
    def test_three_stages_one_output(self):
        src=(ROOT/"features/v176/apply-v176-cobble-obsidian-815.py").read_text("utf-8")
        tree=ast.parse(src)
        # Recipe tuple contains tier variable names, so literal_eval cannot
        # evaluate it. Verify concrete values and sequence as exact source text.
        self.assertIn('(first,"minecraft:cobblestone","obsidiannetwork:"+first)',src)
        self.assertIn('(third,"obsidiannetwork:"+first,"obsidiannetwork:"+third)',src)
        self.assertIn('("obsidian_from_compressed_cobblestone","obsidiannetwork:"+third,"minecraft:obsidian")',src)
        self.assertIn('first="compressed_cobblestone_1x"',src)
        self.assertIn('third="compressed_cobblestone_3x"',src)
        self.assertIn('"count":1',src)
        self.assertIn('"CCC","CCC","CCC"',src)
        self.assertEqual(9**3,729)
    def test_pipeline_orders_recipe_after_item_registration_and_audits(self):
        workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
        register=workflow.index("python3 features/v176/apply-v176-backpack-registry.py")
        recipe=workflow.index("python3 features/v176/apply-v176-cobble-obsidian-815.py")
        audit=workflow.index("python3 features/v175/apply-v175-recipe-collisions-659.py work/src/main/resources --apply",recipe)
        self.assertLess(register,recipe)
        self.assertLess(recipe,audit)
if __name__=="__main__":
    unittest.main()
