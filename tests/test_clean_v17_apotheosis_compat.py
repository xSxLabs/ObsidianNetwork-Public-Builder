#!/usr/bin/env python3
"""Apotheosis optional 26.1 integration: eight real suit items, no hard dependency."""
import ast
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"features/v17/apply-power-armor-apotheosis.py"
WORKFLOW=Path(__file__).resolve().parents[1]/".github/workflows/networkstorage-v1.7-clean.yml"

class ApotheosisArmorCompat(unittest.TestCase):
 def test_generator_syntax_and_position(self):
  ast.parse(SCRIPT.read_text(encoding="utf-8"))
  wf=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("python3 features/v17/apply-power-armor-apotheosis.py",wf)
  self.assertLess(wf.index("python3 features/v17/apply-power-armor-freestanding.py"),
                  wf.index("python3 features/v17/apply-power-armor-apotheosis.py"))
 def test_eight_powerarmor_ids_and_preserved_apotheosis_defaults(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   j=root/"java/dev/obsidiannetwork"
   j.mkdir(parents=True)
   reg="\n".join(f'ITEMS.registerItem("power_armor_{tier}{piece}"'
    for tier in ("","mk2_") for piece in ("helmet","chestplate","leggings","boots"))
   (j/"ObsidianNetwork.java").write_text(reg,encoding="utf-8")
   with patch.dict(os.environ,{"V1_SOURCE_ROOT":str(root/"java"),
                               "V1_RESOURCE_ROOT":str(root/"resources")}):
    runpy.run_path(str(SCRIPT),run_name="__main__")
   p=root/"resources/data/apotheosis/data_maps/item/loot_category_overrides.json"
   values=json.loads(p.read_text(encoding="utf-8"))["values"]
   self.assertEqual(len(values),10)
   for tier in ("","mk2_"):
    for piece in ("helmet","chestplate","leggings","boots"):
     self.assertEqual(values[f"obsidiannetwork:power_armor_{tier}{piece}"],"apotheosis:"+piece)
   self.assertEqual(values["minecraft:iron_sword"],"apotheosis:melee_weapon")
   self.assertEqual(values["minecraft:shulker_shell"],"apotheosis:none")
   with patch.dict(os.environ,{"V1_SOURCE_ROOT":str(root/"java"),
                               "V1_RESOURCE_ROOT":str(root/"resources")}):
    with self.assertRaises(AssertionError):
     runpy.run_path(str(SCRIPT),run_name="__main__")

if __name__=="__main__":
 unittest.main()
