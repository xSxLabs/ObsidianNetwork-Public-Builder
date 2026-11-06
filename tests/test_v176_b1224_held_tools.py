"""B1224 real generated asset/Java regression tests (no Minecraft client required)."""
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "features/v176/apply-v176-b1224-held-tools.py"
GEOMETRY = ROOT / "features/v176/hammer-geometry.json"
WORKFLOW = ROOT / ".github/workflows/networkstorage-v1.7-clean.yml"
CTOR = "super(ToolMaterial.NETHERITE.applyToolProperties(properties,BlockTags.MINEABLE_WITH_PICKAXE,8.0F,-3.0F,0.0F));"


class HeldToolsB1224(unittest.TestCase):
    def test_pipeline_guards(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python3 features/v176/apply-v176-b1224-held-tools.py", workflow)
        self.assertIn("test_v176_b1224_held_tools.py", workflow)
        self.assertLess(workflow.index("python3 features/v176/apply-v176-hammer-model.py"),
                        workflow.index("python3 features/v176/apply-v176-b1224-held-tools.py"))
        self.assertIn("_EXPLICIT_BUILD_", workflow)

    def test_generated_java_and_item_transforms(self):
        geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
        self.assertEqual(len(geometry["elements"]), 110)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            java = base / "java/dev/obsidiannetwork"
            assets = base / "resources/assets/obsidiannetwork"
            for classname, slug in (("MultitoolItem", "multitool"), ("HammerItem", "hammer")):
                p = java / slug / (classname + ".java")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("class " + classname + "{void init(){" + CTOR + "}}", encoding="utf-8")
            modelroot = assets / "models/item"
            modelroot.mkdir(parents=True, exist_ok=True)
            mt_disp = {
                "thirdperson_righthand": {"rotation": [0, -90, 55],
                                          "translation": [0, 3, 1], "scale": [.67] * 3},
                "thirdperson_lefthand": {"rotation": [0, 90, -55],
                                         "translation": [0, 3, 1], "scale": [.67] * 3},
                "firstperson_righthand": {"rotation": [0, -88, 10],
                                          "translation": [1.9, 1.9, 1.3], "scale": [.78] * 3},
                "firstperson_lefthand": {"rotation": [0, 88, -10],
                                         "translation": [-1.9, 1.9, 1.3], "scale": [.78] * 3},
                "gui": {"rotation": [28, -35, -8], "translation": [0, 0, 0],
                        "scale": [.56] * 3},
            }
            # A bounding-volume native multitool fixture; require all 2000
            # reconstructed pieces as in the production resource.
            element = {"from": [-.17, .26, 6.43], "to": [16.9, 24.95, 9.575],
                       "faces": {"north": {"texture": "#palette"}}}
            mt_original = {"parent": "minecraft:block/block",
                           "textures": {"palette": "obsidiannetwork:item/void_reaver_hd"},
                           "elements": [copy.deepcopy(element) for _ in range(2000)],
                           "display": mt_disp}
            hammer_original = {"textures": {"0": "obsidiannetwork:item/hammer"},
                               "elements": copy.deepcopy(geometry["elements"]),
                               "display": copy.deepcopy(geometry["display"])}
            (modelroot / "multitool.json").write_text(json.dumps(mt_original), encoding="utf-8")
            (modelroot / "hammer.json").write_text(json.dumps(hammer_original), encoding="utf-8")
            env = {**os.environ, "V1_SOURCE_ROOT": str(base / "java"),
                   "V1_RESOURCE_ROOT": str(base / "resources")}
            proc = subprocess.run([sys.executable, str(PATCH)], env=env,
                                  capture_output=True, text=True, check=True)
            self.assertIn("B1224_HAMMER_HELD_LIKE_MULTITOOL_FP_LOWER_DURABILITY_6093_12186_PASS",
                          proc.stdout)
            multitool = json.loads((modelroot / "multitool.json").read_text())
            hammer = json.loads((modelroot / "hammer.json").read_text())
            for slug, classname, amount in (("multitool", "MultitoolItem", 6093),
                                             ("hammer", "HammerItem", 12186)):
                s = (java / slug / (classname + ".java")).read_text()
                self.assertIn(f"0.0F).durability({amount}));", s)
                self.assertNotIn(CTOR, s)
            self.assertEqual(multitool["elements"], mt_original["elements"])
            self.assertEqual(len(hammer["elements"]), 110)
            for old, new in zip(hammer_original["elements"], hammer["elements"]):
                self.assertEqual(old["faces"], new["faces"])
                for key in ("from", "to"):
                    self.assertEqual([round(x + shift, 6)
                                      for x, shift in zip(old[key], (8, 2, 8))], new[key])
            self.assertEqual(min(e["from"][1] for e in hammer["elements"]), 0)
            for hand in ("thirdperson_righthand", "thirdperson_lefthand",
                         "firstperson_righthand", "firstperson_lefthand"):
                self.assertEqual(hammer["display"][hand], multitool["display"][hand])
            for hand in ("firstperson_righthand", "firstperson_lefthand"):
                self.assertEqual(multitool["display"][hand]["translation"][1], -0.5)
            for name, model in (("hammer", hammer), ("multitool", multitool)):
                gui = model["display"]["gui"]
                self.assertEqual(gui["rotation"], [30, 225, 0], name)
                self.assertTrue(0 < gui["scale"][0] <= .625, name)
                self.assertEqual(gui["scale"], [gui["scale"][0]] * 3)
                self.assertLess(abs(gui["translation"][0]), 5, name)
                self.assertLess(abs(gui["translation"][1]), 5, name)
                self.assertEqual(gui["translation"][2], 0)


if __name__ == "__main__":
    unittest.main()
