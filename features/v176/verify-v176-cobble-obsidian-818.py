#!/usr/bin/env python3
"""Fail-closed: B659 may repair other recipes but must NOT change these 3."""
import json, os
from pathlib import Path
R=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork/recipe"
chain=[
 ("compressed_cobblestone_1x","minecraft:cobblestone","obsidiannetwork:compressed_cobblestone_1x"),
 ("compressed_cobblestone_3x","obsidiannetwork:compressed_cobblestone_1x","obsidiannetwork:compressed_cobblestone_3x"),
 ("obsidian_from_compressed_cobblestone","obsidiannetwork:compressed_cobblestone_3x","minecraft:obsidian")
]
for name,ingredient,result in chain:
 p=R/(name+".json")
 assert p.is_file(),("B818_RECIPE_MISSING",str(p))
 obj=json.loads(p.read_text(encoding="utf-8"))
 assert obj.get("type")=="minecraft:crafting_shaped",("B818_NOT_SHAPED",name)
 assert obj.get("pattern")==["CCC","CCC","CCC"],("B818_RECIPE_PATTERN_CHANGED",name)
 assert obj.get("key")=={"C":ingredient},("B818_RECIPE_COST_CHANGED",name)
 assert obj.get("result")=={"id":result,"count":1},("B818_RECIPE_OUTPUT_CHANGED",name)
print("V176_B818_EXACT_729_COBBLE_OBSIDIAN_CHAIN_NO_COLLISION_REWRITE PASS")
