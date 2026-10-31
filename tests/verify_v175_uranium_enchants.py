#!/usr/bin/env python3
"""Fail-closed v1.7.5 uranium harvest and Veinminer source/resource guard."""
import json
import os
import re
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
R = Path(os.environ["V1_RESOURCE_ROOT"])
src = (J / "ObsidianNetwork.java").read_text(encoding="utf-8")
ores = ("uranium_ore", "deepslate_uranium_ore")
ids = {"obsidiannetwork:" + x for x in ores}

def read(path):
    p = R / path
    assert p.is_file(), ("V175_MISSING_RESOURCE", str(path))
    return json.loads(p.read_text(encoding="utf-8"))

for symbol, name in (("URANIUM_ORE", ores[0]), ("DEEPSLATE_URANIUM_ORE", ores[1])):
    match = re.search(r"\b" + symbol + r"\s*=", src)
    assert match, ("V175_MISSING_REGISTRY", name)
    decl = src[match.start():src.index(";", match.start())]
    assert "BLOCKS.registerBlock" in decl and ('"' + name + '"') in decl, name
    assert decl.count(".requiresCorrectToolForDrops()") == 1, ("V175_MUST_REQUIRE_CORRECT_PICKAXE", name)
    assert ".strength(" in decl, ("V175_MINING_STRENGTH_LOST", name)

    loot = read("data/obsidiannetwork/loot_table/blocks/" + name + ".json")
    assert loot["type"] == "minecraft:block"
    assert len(loot["pools"]) == 1 and loot["pools"][0]["rolls"] == 1.0
    alt, = loot["pools"][0]["entries"]
    assert alt["type"] == "minecraft:alternatives"
    assert len(alt["children"]) == 2
    silk, raw = alt["children"]
    assert silk["type"] == "minecraft:item" and silk["name"] == "obsidiannetwork:" + name
    assert "functions" not in silk
    cond, = silk["conditions"]
    assert cond["condition"] == "minecraft:match_tool"
    enchant, = cond["predicate"]["predicates"]["minecraft:enchantments"]
    assert enchant == {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}, name
    assert raw["type"] == "minecraft:item" and raw["name"] == "obsidiannetwork:raw_uranium"
    assert raw["functions"] == [
        {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
        {"function": "minecraft:explosion_decay"}
    ], name
    assert "conditions" not in raw
    for folder in ("models/block", "blockstates"):
        read("assets/obsidiannetwork/" + folder + "/" + name + ".json")

for path in (
    "data/minecraft/tags/block/mineable/pickaxe.json",
    "data/minecraft/tags/block/needs_iron_tool.json",
    "data/c/tags/block/ores.json",
    "data/c/tags/block/ores/uranium.json",
):
    tags = read(path)["values"]
    assert ids.issubset(set(x for x in tags if isinstance(x, str))), ("V175_URANIUM_MISSING_TAG", path)
    assert all(tags.count(x) == 1 for x in ids), ("V175_URANIUM_DUPLICATE_TAG", path)

print("V175_URANIUM_ENCHANTED_HARVEST_VEINMINER_TWO_ORES_PASS")