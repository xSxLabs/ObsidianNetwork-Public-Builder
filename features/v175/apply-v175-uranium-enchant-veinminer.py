#!/usr/bin/env python3
"""v1.7.5: native Fortune, Silk Touch, and pickaxe-only Veinminer support
for ordinary and deepslate uranium ores. Apply after the B617 source patches.
No ore IDs, mining hardness, worldgen, recipes, or energy logic are changed.
"""
import json
import os
import re
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
R = Path(os.environ["V1_RESOURCE_ROOT"])
MAIN = J / "ObsidianNetwork.java"
NAMES = ("uranium_ore", "deepslate_uranium_ore")
IDS = tuple("obsidiannetwork:" + name for name in NAMES)
RAW = "obsidiannetwork:raw_uranium"

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def tag(rel, values):
    path = R / rel
    obj = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"replace": False, "values": []}
    assert isinstance(obj, dict) and isinstance(obj.get("values"), list), ("V175_TAG_INVALID", rel)
    obj.setdefault("replace", False)
    for val in values:
        if val not in obj["values"]:
            obj["values"].append(val)
    write(path, obj)

source = MAIN.read_text(encoding="utf-8")
for symbol, name in (("URANIUM_ORE", NAMES[0]), ("DEEPSLATE_URANIUM_ORE", NAMES[1])):
    matches = list(re.finditer(r"\b" + symbol + r"\s*=", source))
    assert len(matches) == 1, ("V175_ORE_REGISTRY_DRIFT", symbol, len(matches))
    start = matches[0].start()
    end = source.find(";", start)
    assert start < end < start + 1500, ("V175_REGISTRATION_RANGE", symbol)
    definition = source[start:end+1]
    assert "BLOCKS.registerBlock" in definition and ('"' + name + '"') in definition, ("V175_BLOCK_ID_DRIFT", symbol)
    # Explicitly prevent ordinary blocks without the correct pickaxe from
    # dropping anything, including through Silk Touch; respects tool tier tags.
    if ".requiresCorrectToolForDrops()" not in definition:
        strength = re.search(r"\.strength\([^()]+\)", definition)
        assert strength, ("V175_MISSING_TOOL_STRENGTH_ANCHOR", name)
        definition = definition[:strength.end()] + ".requiresCorrectToolForDrops()" + definition[strength.end():]
        source = source[:start] + definition + source[end+1:]
    assert definition.count(".requiresCorrectToolForDrops()") == 1, ("V175_TOOL_FLAG_DUPLICATE", name)
    for part in ("models/block", "blockstates"):
        assert (R / "assets/obsidiannetwork" / part / (name + ".json")).is_file(), ("V175_MISSING_MODEL", name)

if source != MAIN.read_text(encoding="utf-8"):
    MAIN.write_text(source, encoding="utf-8")

# Same loot behavior as vanilla iron/deepslate iron: one raw uranium (Fortune
# multiplies via vanilla ore_drops), Silk Touch returns the exact ore block.
for name, item in zip(NAMES, IDS):
    data = {
        "type": "minecraft:block",
        "random_sequence": "obsidiannetwork:blocks/" + name,
        "pools": [{
            "rolls": 1.0,
            "bonus_rolls": 0.0,
            "entries": [{
                "type": "minecraft:alternatives",
                "children": [
                    {
                        "type": "minecraft:item",
                        "name": item,
                        "conditions": [{
                            "condition": "minecraft:match_tool",
                            "predicate": {
                                "predicates": {"minecraft:enchantments": [{
                                    "enchantments": "minecraft:silk_touch",
                                    "levels": {"min": 1}
                                }]}
                            }
                        }]
                    },
                    {
                        "type": "minecraft:item",
                        "name": RAW,
                        "functions": [
                            {
                                "function": "minecraft:apply_bonus",
                                "enchantment": "minecraft:fortune",
                                "formula": "minecraft:ore_drops"
                            },
                            {"function": "minecraft:explosion_decay"}
                        ]
                    }
                ]
            }]
        }]
    }
    path = R / "data/obsidiannetwork/loot_table/blocks" / (name + ".json")
    assert path.is_file(), ("V175_EXPECT_EXISTING_ORE_LOOT", name)
    old = json.loads(path.read_text(encoding="utf-8"))
    assert old.get("type") == "minecraft:block", ("V175_LOOT_TYPE_DRIFT", name)
    write(path, data)

# Both vanilla mining checks are required for correct-tier pickaxes; Veinminer
# 2.x recognizes the existing #c:ores block group with #minecraft:pickaxes.
tag("data/minecraft/tags/block/mineable/pickaxe.json", IDS)
tag("data/minecraft/tags/block/needs_iron_tool.json", IDS)
tag("data/c/tags/block/ores.json", IDS)
tag("data/c/tags/block/ores/uranium.json", IDS)
print("V175_URANIUM_PICKAXE_FORTUNE_SILK_VEINMINER_PASS")