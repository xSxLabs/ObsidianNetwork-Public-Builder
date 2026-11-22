#!/usr/bin/env python3
"""B1715: original, bounded, static mechanical drill + no minimap claims title."""
import ast
import json
import os
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH="features/v178/apply-v178-b1715-miner-visuals.py"
SRC=(ROOT/PATH).read_text(encoding="utf8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf8")

class MechanicalMiningBuilder1715(unittest.TestCase):
    def test_source_and_order(self):
        ast.parse(SRC,filename=PATH)
        self.assertEqual(WF.count("python3 "+PATH),1)
        self.assertLess(WF.index("python3 features/v178/apply-v178-b1677-miner-style.py"),
                        WF.index("python3 "+PATH))
        self.assertLess(WF.index("python3 features/v178/apply-v178-b1700-atlas-and-tps-miner.py"),
                        WF.index("python3 "+PATH))
        self.assertIn("B1715_PART_BUDGET",SRC)
        self.assertIn("B1715_MINIMAP_TITLE_SOURCE_DRIFT",SRC)
        self.assertIn("head=\'\"CLAIMS \"+\'",SRC)
        self.assertNotIn("BlockEntityRenderer",SRC)
        self.assertNotIn("world.getChunk(",SRC)
        self.assertNotIn("texture.upload()",SRC)

    def test_model_and_visible_drill(self):
        for token in (
            "forward-narrowing stepped cutter",
            'box((7,6.5,0),(9,8.5,1),"blade")',
            'box((5.5,12.35,1.75),(10.5,13.65,2),"display")',
            'box((6,15.1,7),(10,16,11),"core")',
            'box((6,5,15.5),(10,10.5,16),"display")',
            'SIZE=64',
            '"warning","hydraulic"',
            '"ambientocclusion":True',
            'B1715_MECHANICAL_DIAMOND_DRILL_BUILDER_STATIC_',
        ):
            self.assertIn(token,SRC,token)

    def test_generated_render_only_resources(self):
        r=os.environ.get("V1_RESOURCE_ROOT")
        j=os.environ.get("V1_SOURCE_ROOT")
        if not r or not j:self.skipTest("Full CI generated resources only")
        assets=Path(r)/"assets/obsidiannetwork"
        model=json.loads((assets/"models/block/mining_builder.json").read_text())
        self.assertEqual(len(model["elements"]),1)
        self.assertLessEqual(len(model["elements"]),40)
        self.assertTrue(any(e["from"][2]==0 for e in model["elements"]))
        self.assertTrue(any(e["to"][1]==16 for e in model["elements"]))
        for element in model["elements"]:
            for a,b in zip(element["from"],element["to"]):
                self.assertGreaterEqual(a,0)
                self.assertLessEqual(b,16)
                self.assertLess(a,b)
        for key,loc in model["textures"].items():
            path=assets/"textures"/(loc.split(":")[1]+".png")
            self.assertTrue(path.is_file(),key)
            self.assertEqual(struct.unpack(">II",path.read_bytes()[16:24]),
                             (32,32) if key=="front" else (16,16))
        state=json.loads((assets/"blockstates/mining_builder.json").read_text())
        self.assertEqual(len(state["variants"]),4)
        java=(Path(j)/"dev/obsidiannetwork/client/V178ClaimsClient.java").read_text()
        self.assertNotIn('"CLAIMS "',java)
        self.assertNotIn('"CLAIMS M"',java)
        self.assertIn("showCoordinates",java)
        self.assertNotIn(':"CLAIMS M"',java)

if __name__=="__main__":
    unittest.main()
