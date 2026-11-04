#!/usr/bin/env python3
"""No tinted glass in any ObsidianNetwork crafting input, without damaging outputs."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"features/v176/replace-tinted-glass-crafting-recipes.py"
SPEC=importlib.util.spec_from_file_location("xsx_crafting_glass",SCRIPT)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class NormalGlassRecipes(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.recipes=self.root/"data/obsidiannetwork/recipe"
  self.recipes.mkdir(parents=True)
 def recipe(self,name,payload):
  p=self.recipes/(name+".json")
  p.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
  return p
 def test_replaces_shaped_and_shapeless_inputs_and_preserves_results(self):
  shaped=self.recipe("reactor_glass",{
   "type":"minecraft:crafting_shaped",
   "pattern":["GG","GG"],
   "key":{"G":"minecraft:tinted_glass"},
   "result":{"id":"minecraft:tinted_glass","count":1}
  })
  shapeless=self.recipe("other",{
   "type":"minecraft:crafting_shapeless",
   "ingredients":[{"item":"tinted_glass"},["minecraft:tinted_glass","minecraft:amethyst_shard"]],
   "result":{"id":"obsidiannetwork:other","count":1}
  })
  with self.assertRaises(AssertionError):
   MOD.process(self.root,apply=False)
  self.assertEqual(MOD.process(self.root,apply=True),(2,3))
  self.assertEqual(MOD.process(self.root,apply=True),(0,0))
  MOD.process(self.root,apply=False)
  a=json.loads(shaped.read_text())
  b=json.loads(shapeless.read_text())
  self.assertEqual(a["key"]["G"],"minecraft:glass")
  self.assertEqual(a["result"]["id"],"minecraft:tinted_glass")
  self.assertEqual(b["ingredients"][0]["item"],"minecraft:glass")
  self.assertEqual(b["ingredients"][1][0],"minecraft:glass")
  self.assertEqual(b["ingredients"][1][1],"minecraft:amethyst_shard")
 def test_does_not_mutate_furnace_recipes_or_other_mods(self):
  furnace=self.recipe("smelt",{"type":"minecraft:smelting",
                   "ingredient":"minecraft:tinted_glass",
                   "result":{"id":"minecraft:stone"}})
  foreign=self.root/"data/othermod/recipe/special.json"
  foreign.parent.mkdir(parents=True)
  foreign.write_text('{"type":"minecraft:crafting_shaped","key":{"G":"minecraft:tinted_glass"}}\n')
  old1,old2=furnace.read_bytes(),foreign.read_bytes()
  self.recipe("valid",{"type":"minecraft:crafting_shapeless",
                       "ingredients":["minecraft:glass"],
                       "result":{"id":"obsidiannetwork:valid"}})
  self.assertEqual(MOD.process(self.root,apply=True),(0,0))
  self.assertEqual(furnace.read_bytes(),old1)
  self.assertEqual(foreign.read_bytes(),old2)
 def test_recipe_plural_supported(self):
  p=self.root/"data/obsidiannetwork/recipes/machines/glass.json"
  p.parent.mkdir(parents=True)
  p.write_text('{"type":"minecraft:crafting_shapeless","ingredients":["minecraft:tinted_glass"],"result":{"id":"obsidiannetwork:test"}}\n')
  self.assertEqual(MOD.process(self.root,apply=True),(1,1))
  self.assertIn('"minecraft:glass"',p.read_text())
 def test_fail_closed_if_no_recipes(self):
  with self.assertRaisesRegex(RuntimeError,"No ObsidianNetwork recipes"):
   MOD.process(self.root,apply=False)
 def test_fail_closed_on_corrupt_json(self):
  p=self.recipes/"bad.json"
  p.write_text('{not json')
  with self.assertRaises(json.JSONDecodeError):
   MOD.process(self.root,apply=True)

if __name__=="__main__":
 unittest.main()
