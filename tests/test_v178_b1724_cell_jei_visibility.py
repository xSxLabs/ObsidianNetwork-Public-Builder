#!/usr/bin/env python3
"""B1724 2M and 4M Storage Cell JEI discoverability regression."""
import ast
import json
import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT="features/v178/apply-v178-b1724-4m-cell-jei-visibility.py"
SOURCE=(ROOT/SCRIPT).read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class CellJei1724(unittest.TestCase):
 def test_source_and_correct_post_recipe_order(self):
  ast.parse(SOURCE,filename=SCRIPT)
  self.assertEqual(WF.count("python3 "+SCRIPT),1)
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1711-4m-storage-cell-balance.py"),
                  WF.index("python3 "+SCRIPT))
  self.assertLess(WF.index("python3 "+SCRIPT),
                  WF.index("python3 features/v175/apply-v175-recipe-collisions-659.py work/src/main/resources",
                           WF.index("python3 "+SCRIPT)))
  for token in (
    "output.accept((ItemLike)STORAGE_CELL_2M.get());",
    "output.accept((ItemLike)STORAGE_CELL_4M.get());",
    "storage_cell_4m.json","minecraft:netherite_block",
    "minecraft:nether_star","minecraft:crafting_shaped",
    "B1724_2M_4M_STORAGE_CELLS_VISIBLE_CREATIVE_JEI_ENTRY_PASS"):
   self.assertIn(token,SOURCE,token)
  self.assertNotIn("removeIngredientsAtRuntime",SOURCE)

 def test_generated_item_models_lang_and_crafting(self):
  java=os.environ.get("V1_SOURCE_ROOT")
  resources=os.environ.get("V1_RESOURCE_ROOT")
  if not java or not resources:self.skipTest("Full generated build only")
  main=(Path(java)/"dev/obsidiannetwork/ObsidianNetwork.java").read_text()
  root=Path(resources)
  for name in ("2m","4m"):
   cap=name.upper()
   self.assertEqual(main.count(
     f"output.accept((ItemLike)STORAGE_CELL_{cap}.get());"),1)
   descriptor=root/f"assets/obsidiannetwork/items/storage_cell_{name}.json"
   self.assertEqual(json.loads(descriptor.read_text())["model"]["model"],
                    f"obsidiannetwork:item/storage_cell_{name}")
   self.assertTrue((root/f"assets/obsidiannetwork/models/item/storage_cell_{name}.json").is_file())
   data=json.loads((root/f"data/obsidiannetwork/recipe/storage_cell_{name}.json").read_text())
   self.assertEqual(data["result"]["id"],f"obsidiannetwork:storage_cell_{name}")
  four=json.loads((root/"data/obsidiannetwork/recipe/storage_cell_4m.json").read_text())
  self.assertEqual(four["pattern"],["NCN","CSC","NCN"])
  self.assertEqual(four["key"]["C"],"obsidiannetwork:storage_cell_1m")
  for language in ("de_de","en_us"):
   doc=json.loads((root/f"assets/obsidiannetwork/lang/{language}.json").read_text())
   self.assertTrue(doc["item.obsidiannetwork.storage_cell_4m"])

if __name__=="__main__":unittest.main()
