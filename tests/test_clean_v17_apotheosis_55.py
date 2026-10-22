#!/usr/bin/env python3
"""Build 55 Apotheosis 26.1 8-item category map integration."""
import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "features/v17/apply-power-armor-apotheosis.py"
WF = (ROOT / ".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class Apotheosis55(unittest.TestCase):
    def test_generator_valid_and_workflow_order(self):
        ast.parse(SCRIPT.read_text(encoding="utf-8"))
        self.assertIn("python3 features/v17/apply-power-armor-apotheosis.py", WF)
        self.assertLess(WF.index("python3 features/v17/apply-power-armor-freestanding.py"),
                        WF.index("python3 features/v17/apply-power-armor-apotheosis.py"))
        self.assertIn("data/apotheosis/data_maps/item/loot_category_overrides.json", SCRIPT.read_text(encoding="utf-8"))

    def test_exact_eight_suit_items_with_correct_slots_and_idempotency(self):
        with tempfile.TemporaryDirectory() as name:
            env = dict(os.environ, V1_RESOURCE_ROOT=name)
            path = Path(name) / "data/apotheosis/data_maps/item/loot_category_overrides.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"values":{"minecraft:iron_sword":"apotheosis:melee_weapon"}}),encoding="utf-8")
            for attempt in range(2):
                result = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                                        capture_output=True, text=True, check=True)
                self.assertIn("COMPAT PASS",result.stdout)
                actual = json.loads(path.read_text(encoding="utf-8"))["values"]
                self.assertEqual(actual["minecraft:iron_sword"],"apotheosis:melee_weapon")
                for tier in ("", "mk2_"):
                    for part in ("helmet","chestplate","leggings","boots"):
                        self.assertEqual(actual[f"obsidiannetwork:power_armor_{tier}{part}"],
                                         f"apotheosis:{part}")
                self.assertEqual(len(actual),9)

if __name__ == "__main__":
    unittest.main()
