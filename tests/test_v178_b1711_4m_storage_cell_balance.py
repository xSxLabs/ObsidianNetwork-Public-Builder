#!/usr/bin/env python3
"""B1711: resource-only 4M Storage Cell pricing, idempotence and isolation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v178/apply-v178-b1711-4m-storage-cell-balance.py"
SPEC=importlib.util.spec_from_file_location("b1711_4m_storage",PATCH)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class FourMillionCellBalance(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.folder=self.root/"data/obsidiannetwork/recipe"
        self.folder.mkdir(parents=True)
    def recipe(self,name,result,ingredients=None):
        path=self.folder/(name+".json")
        payload={"type":"minecraft:crafting_shaped",
                 "pattern":["ABA","CDC","ABA"],
                 "key":ingredients or {"A":"minecraft:iron_ingot",
                      "B":"minecraft:diamond","C":"minecraft:glass",
                      "D":"minecraft:redstone"},
                 "result":{"id":"obsidiannetwork:"+result,"count":1},
                 "category":"misc"}
        path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
        return path
    def test_hard_4m_recipe_is_staged_and_only_target_changes(self):
        one=self.recipe("storage_cell_1m","storage_cell_1m")
        four=self.recipe("storage_cell_4m","storage_cell_4m")
        other=self.recipe("storage_cell_64k","storage_cell_64k")
        before={p:p.read_bytes() for p in (one,other)}
        expected_result=json.loads(four.read_text())["result"]
        self.assertEqual(MOD.apply(self.root),four)
        new=json.loads(four.read_text())
        self.assertEqual(new["result"],expected_result)
        self.assertEqual(new["category"],"misc")
        self.assertEqual(new["pattern"],["NCN","CSC","NCN"])
        self.assertEqual(new["key"],{
          "N":"minecraft:netherite_block",
          "C":"obsidiannetwork:storage_cell_1m",
          "S":"minecraft:nether_star"})
        self.assertEqual([p.read_bytes() for p in (one,other)],
                         [before[p] for p in (one,other)])
        after=four.read_bytes()
        MOD.apply(self.root)
        self.assertEqual(after,four.read_bytes())
    def test_alias_capacity_4096k_and_shapeless_original(self):
        self.recipe("storage_cell_1024k","storage_cell_1024k")
        four=self.recipe("storage_cell_4096k","storage_cell_4096k")
        before=json.loads(four.read_text())
        before["type"]="minecraft:crafting_shapeless"
        before["ingredients"]=["minecraft:diamond"]*4
        before.pop("pattern")
        before.pop("key")
        four.write_text(json.dumps(before),encoding="utf-8")
        MOD.apply(self.root)
        new=json.loads(four.read_text())
        self.assertEqual(new["type"],"minecraft:crafting_shaped")
        self.assertEqual(new["key"]["C"],
                         "obsidiannetwork:storage_cell_1024k")
        self.assertNotIn("ingredients",new)
    def test_missing_target_fails_closed(self):
        self.recipe("storage_cell_1m","storage_cell_1m")
        with self.assertRaisesRegex(ValueError,"B1711_CELL_TIER"):
            MOD.apply(self.root)
    def test_missing_1m_fails_closed_without_modifying_4m(self):
        four=self.recipe("storage_cell_4m","storage_cell_4m")
        before=four.read_bytes()
        with self.assertRaisesRegex(ValueError,"B1711_1M_FAMILY"):
            MOD.apply(self.root)
        self.assertEqual(before,four.read_bytes())
    def test_no_foreign_or_energy_cells_affected(self):
        self.recipe("storage_cell_1m","storage_cell_1m")
        four=self.recipe("storage_cell_4m","storage_cell_4m")
        energy=self.recipe("energy_cell_4m","energy_cell_4m")
        before=energy.read_bytes()
        MOD.apply(self.root)
        self.assertEqual(energy.read_bytes(),before)
        self.assertIn("netherite_block",four.read_text())
    def test_workflow_orders_final_recipe_audit_after_balance(self):
        workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
        patch="python3 features/v178/apply-v178-b1711-4m-storage-cell-balance.py work/src/main/resources"
        self.assertEqual(workflow.count(patch),1)
        position=workflow.index(patch)
        glass=workflow.index("python3 features/v176/resolve-normal-glass-recipe-conflicts.py work/src/main/resources",position-1000)
        audit=workflow.index("python3 features/v175/apply-v175-recipe-collisions-659.py work/src/main/resources",position)
        self.assertLess(glass,position)
        self.assertLess(position,audit)

if __name__=="__main__":
    unittest.main()
