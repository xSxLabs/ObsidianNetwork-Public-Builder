#!/usr/bin/env python3
"""Fail closed on unsafe full-height suit model geometry and animation wiring."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "features/v17/apply-power-armor-animation.py").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")


class ArmorAnimationModelTests(unittest.TestCase):
    def test_stage_order_and_valid_source(self):
        parsed = ast.parse(SCRIPT)
        self.assertTrue(parsed.body)
        self.assertIn("python3 features/v17/apply-power-armor-animation.py", WORKFLOW)
        self.assertLess(WORKFLOW.index("apply-power-armor-cards.py"), WORKFLOW.index("apply-power-armor-animation.py"))
        self.assertIn("ArmorStationBlockEntity::serverTick", SCRIPT)
        self.assertIn("getStateForPlacement(", SCRIPT)
        self.assertIn("STAND_SHAPE", SCRIPT)
        self.assertIn("context.getClickedPos().above()", SCRIPT)
        self.assertIn("level.removeBlock(pos,false)", SCRIPT)
        self.assertIn("animationTicks=20", SCRIPT)
        self.assertIn("out.putInt(\"power_armor_anim\"", SCRIPT)
        self.assertIn("in.getIntOr(\"power_armor_anim\"", SCRIPT)

    def test_all_eight_blockmodels_stay_within_valid_bounds(self):
        # Compile ONLY these two pure model generators. Never execute the patch script.
        module = ast.parse(SCRIPT)
        nodes = [node for node in module.body if isinstance(node, ast.FunctionDef)
                 and node.name in ("cuboid", "model")]
        self.assertEqual(len(nodes), 2)
        scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]),
                     "<v17-armor-models>", "exec"), scope)
        model = scope["model"]
        snapshots = {}
        for filled in (False, True):
            for frame in range(4):
                data = model(filled, frame)
                cubes = data["elements"]
                self.assertGreater(len(cubes), 0)
                snapshots[(filled, frame)] = cubes
                for cube in cubes:
                    self.assertEqual(len(cube["from"]), 3)
                    self.assertEqual(len(cube["to"]), 3)
                    for lo, hi in zip(cube["from"], cube["to"]):
                        self.assertGreaterEqual(lo, -16)
                        self.assertLessEqual(hi, 32)
                        self.assertLess(lo, hi)
        self.assertEqual(snapshots[(False, 0)], snapshots[(False, 3)])
        self.assertNotEqual(snapshots[(True, 0)], snapshots[(True, 3)])

    def test_exit_and_station_contents_stay_persisted(self):
        self.assertIn("stand.startClose()", SCRIPT)
        self.assertIn("station.startOpen()", SCRIPT)
        self.assertIn("out.store(\"armor_suit\"", SCRIPT)
        self.assertIn("if(station.isAnimating())return InteractionResult.FAIL;", SCRIPT)
        self.assertIn("if(be.opening&&empty)",SCRIPT)
        self.assertIn("level.getBlockEntity(pos)==be",SCRIPT)


if __name__ == "__main__":
    unittest.main()
