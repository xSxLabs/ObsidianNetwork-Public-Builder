#!/usr/bin/env python3
"""v1.7.4 CI data/registry acceptance gate for uranium fuel foundation."""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
mod=(J/"ObsidianNetwork.java").read_text(encoding="utf-8")
for field, name in [
    ("URANIUM_ORE","uranium_ore"), ("RAW_URANIUM","raw_uranium"),
    ("URANIUM_INGOT","uranium_ingot"), ("URANIUM_ROD","uranium_rod")
]:
    assert mod.count('registerBlock("'+name+'"') == 1 if name=="uranium_ore" else mod.count('ITEMS.registerItem("'+name+'"') == 1, name
    assert field in mod
for survivor in ("NETWORK_PLANTER_ITEM", "NETWORK_BLUEPRINT", "NETWORK_PRINTER_ITEM",
                 "NETWORK_SCHEMATIC_QUILL", "NETWORK_HOLOGRAM_TERMINAL_ITEM"):
    assert survivor in mod, ("REGISTRY_ID_LOST",survivor)
def read(path):
    p=R/path
    assert p.is_file(), path
    return json.loads(p.read_text(encoding="utf-8"))
for name in ("raw_uranium","uranium_ingot","uranium_rod"):
    assert read(f"assets/obsidiannetwork/items/{name}.json")["model"]["type"]=="minecraft:model"
    assert (R/f"assets/obsidiannetwork/textures/item/{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
assert (R/"assets/obsidiannetwork/textures/block/uranium_ore.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
assert read("data/obsidiannetwork/loot_table/blocks/uranium_ore.json")["pools"][0]["entries"][0]["name"]=="obsidiannetwork:raw_uranium"
for rel, entry in (
    ("data/minecraft/tags/block/mineable/pickaxe.json","obsidiannetwork:uranium_ore"),
    ("data/minecraft/tags/block/needs_iron_tool.json","obsidiannetwork:uranium_ore"),
    ("data/c/tags/item/ingots/uranium.json","obsidiannetwork:uranium_ingot"),
    ("data/c/tags/item/raw_materials/uranium.json","obsidiannetwork:raw_uranium")):
    assert entry in read(rel)["values"], rel
rod=read("data/obsidiannetwork/recipe/uranium_rod.json")
assert rod["type"]=="minecraft:crafting_shaped"
assert rod["pattern"]==["U","U"], "exactly two ingots vertically, 1 rod"
assert rod["key"]["U"]=="#c:ingots/uranium", "use shared tag rather than only native ingot"
assert rod["result"]=={"id":"obsidiannetwork:uranium_rod","count":1}
for style, ticks in (("smelting",200),("blasting",100)):
    recipe=read(f"data/obsidiannetwork/recipe/uranium_ingot_from_{style}.json")
    assert recipe["ingredient"]=="obsidiannetwork:raw_uranium"
    assert recipe["result"]=="obsidiannetwork:uranium_ingot"
    assert recipe["cookingtime"]==ticks
placed=read("data/obsidiannetwork/worldgen/placed_feature/ore_uranium.json")
assert placed["feature"]=="obsidiannetwork:ore_uranium"
assert read("data/obsidiannetwork/neoforge/biome_modifier/add_uranium_ore.json")["step"]=="underground_ores"
for language in ("de_de","en_us"):
    langs=read(f"assets/obsidiannetwork/lang/{language}.json")
    for name in ("uranium_ore","raw_uranium","uranium_ingot","uranium_rod"):
        key=("block" if name=="uranium_ore" else "item")+f".obsidiannetwork.{name}"
        assert langs.get(key), (language,key)
print("V174_URANIUM_FUEL_CHAIN_CI_PASS: registry, recipes, models, PNGs, tags, worldgen and 1.7.3 preservation")
