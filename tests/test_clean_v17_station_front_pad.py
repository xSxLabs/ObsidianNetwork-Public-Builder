#!/usr/bin/env python3
"""Regression guards for v1.7 Armor Station: ONLY exact facing red pad."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = (ROOT / "features/v17/apply-power-armor-bundle-93.py").read_text(encoding="utf-8")


class StationFrontPad(unittest.TestCase):
    def test_patch_python_syntax(self):
        ast.parse(PATCH)

    def test_only_one_block_ahead_is_visible_to_station(self):
        tree = ast.parse(PATCH)
        finder = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "finder_new"
                for target in node.targets
            ):
                finder = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(finder)
        self.assertIn("station.relative(state.getValue(ArmorStationBlock.FACING))", finder)
        self.assertIn("new AABB(pad)", finder)
        self.assertIn("e.blockPosition().equals(pad)", finder)
        self.assertIn("e->mine(e,player)&&full(e)", finder)
        self.assertIn("suits.size()==1", finder)
        self.assertNotIn("inflate(3.0D)", finder)

    def test_auto_dock_only_from_front_pad(self):
        self.assertIn("if(!candidate.equals(origin))continue;", PATCH)
        self.assertNotIn("'if(station.distSqr(origin)>4.0D)continue;'", PATCH)

    def test_station_gui_guidance(self):
        self.assertIn("on the red pad one block in front", PATCH)

if __name__ == "__main__":
    unittest.main()
