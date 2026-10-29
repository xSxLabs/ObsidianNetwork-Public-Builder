#!/usr/bin/env python3
"""v1.7.4: real uranium ore -> raw uranium -> ingot -> tag-compatible fuel rod.

Reconstruction-safe additive change to the green v1.7.3 source tree.
This does NOT pretend that a reactor or fuel consumption has been implemented.
"""
import json
import os
import struct
import zlib
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
R = Path(os.environ["V1_RESOURCE_ROOT"])
MAIN = J / "ObsidianNetwork.java"

def replace_one(path, old, new):
    s = path.read_text(encoding="utf-8")
    assert s.count(old) == 1, ("V174_URANIUM_SOURCE_DRIFT", str(path), old[:80], s.count(old))
    path.write_text(s.replace(old, new, 1), encoding="utf-8")

def emit(rel, obj):
    p = R / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists(), ("V174_URANIUM_RESOURCE_COLLISION", rel)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def append_tag(rel, item):
    p = R / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    tag = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"replace": False, "values": []}
    values = tag.setdefault("values", [])
    assert item not in values, ("V174_TAG_ALREADY_ADDED", rel)
    values.append(item)
    p.write_text(json.dumps(tag, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Keep existing registry names stable: do not modify v1.7.3 items.
anchor = '   public static final DeferredItem<dev.obsidiannetwork.item.NetworkElytraItem> NETWORK_ELYTRA = ITEMS.registerItem('
registrations = """    // V174_URANIUM_FUEL_CHAIN: ore / raw material / ingot / reactor fuel rod.
    public static final DeferredBlock<net.minecraft.world.level.block.Block> URANIUM_ORE =
        BLOCKS.registerBlock("uranium_ore", net.minecraft.world.level.block.Block::new,
            p -> p.mapColor(MapColor.STONE).strength(3.0F,3.0F).requiresCorrectToolForDrops());
    public static final DeferredItem<BlockItem> URANIUM_ORE_ITEM =
        ITEMS.registerSimpleBlockItem("uranium_ore", URANIUM_ORE);
    public static final DeferredItem<net.minecraft.world.item.Item> RAW_URANIUM =
        ITEMS.registerItem("raw_uranium", net.minecraft.world.item.Item::new);
    public static final DeferredItem<net.minecraft.world.item.Item> URANIUM_INGOT =
        ITEMS.registerItem("uranium_ingot", net.minecraft.world.item.Item::new);
    public static final DeferredItem<net.minecraft.world.item.Item> URANIUM_ROD =
        ITEMS.registerItem("uranium_rod", net.minecraft.world.item.Item::new);
"""
replace_one(MAIN, anchor, registrations + "\n" + anchor)
creative = '            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());'
addition = "\n".join("            output.accept((ItemLike)%s.get());" % field
                     for field in ("URANIUM_ORE_ITEM", "RAW_URANIUM", "URANIUM_INGOT", "URANIUM_ROD"))
replace_one(MAIN, creative, creative + "\n" + addition)

# Built with standard Python, without image libraries or copied assets.
def png(rel, color_at):
    p = R / "assets/obsidiannetwork/textures" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists(), str(p)
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t+data)&0xffffffff)
    scanlines = b"".join(b"\0" + b"".join(bytes(color_at(x,y)) for x in range(16)) for y in range(16))
    header = struct.pack(">IIBBBBB",16,16,8,6,0,0,0)
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(scanlines,9)) + chunk(b"IEND",b""))

def ore_color(x, y):
    stone = [(95,94,100,255),(91,92,95,255),(112,110,110,255),(79,82,84,255)]
    green = [(44,100,41,255),(74,143,53,255),(126,184,66,255),(181,216,86,255)]
    vein = ((x*7+y*11)%17 in (1,2,3,7)) or (abs(x-y-1)<=1 and x in (4,5,6,9,10))
    return (green if vein else stone)[(x*3+y*5)%4]
def raw_color(x,y):
    shape = abs(x-7.5)*0.82+abs(y-8)*0.9 < 7.0 and y>=3
    if not shape: return (0,0,0,0)
    shades = [(47,93,40,255),(72,120,42,255),(120,167,59,255),(151,199,76,255)]
    return shades[(x*3+y*7)%len(shades)]
def ingot_color(x,y):
    on = 3<=y<=12 and (5 <= x <= 10 if y<6 else 3<=x<=12)
    if not on: return (0,0,0,0)
    if y<7: return (177,214,95,255)
    if x in (3,12) or y==12: return (38,90,48,255)
    return (96+(x%3)*14,159+(y%3)*11,66,255)
def rod_color(x,y):
    if not (6<=x<=9 and 1<=y<=14): return (0,0,0,0)
    if y in (1,14): return (48,70,49,255)
    return ((47,103,48,255) if x==6 else (179,223,96,255) if x==8 else (112,171,64,255))
png("block/uranium_ore.png",ore_color)
png("item/raw_uranium.png",raw_color)
png("item/uranium_ingot.png",ingot_color)
png("item/uranium_rod.png",rod_color)

emit("assets/obsidiannetwork/blockstates/uranium_ore.json",
     {"variants":{"":{"model":"obsidiannetwork:block/uranium_ore"}}})
emit("assets/obsidiannetwork/models/block/uranium_ore.json",
     {"parent":"minecraft:block/cube_all","textures":{"all":"obsidiannetwork:block/uranium_ore"}})
emit("assets/obsidiannetwork/items/uranium_ore.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:block/uranium_ore"}})
for name in ("raw_uranium", "uranium_ingot", "uranium_rod"):
    emit(f"assets/obsidiannetwork/models/item/{name}.json",
         {"parent":"minecraft:item/generated","textures":{"layer0":f"obsidiannetwork:item/{name}"}})
    emit(f"assets/obsidiannetwork/items/{name}.json",
         {"model":{"type":"minecraft:model","model":f"obsidiannetwork:item/{name}"}})

emit("data/obsidiannetwork/loot_table/blocks/uranium_ore.json",{
    "type":"minecraft:block","pools":[{"rolls":1,"entries":[
      {"type":"minecraft:item","name":"obsidiannetwork:raw_uranium"}]}]})
append_tag("data/minecraft/tags/block/mineable/pickaxe.json","obsidiannetwork:uranium_ore")
append_tag("data/minecraft/tags/block/needs_iron_tool.json","obsidiannetwork:uranium_ore")
append_tag("data/c/tags/item/ingots/uranium.json","obsidiannetwork:uranium_ingot")
append_tag("data/c/tags/item/raw_materials/uranium.json","obsidiannetwork:raw_uranium")

for style, ticks in (("smelting",200),("blasting",100)):
    emit(f"data/obsidiannetwork/recipe/uranium_ingot_from_{style}.json",{
       "type":"minecraft:"+style,"category":"misc","ingredient":"obsidiannetwork:raw_uranium",
       "result":"obsidiannetwork:uranium_ingot","experience":0.7,"cookingtime":ticks})
emit("data/obsidiannetwork/recipe/uranium_rod.json",{
    "type":"minecraft:crafting_shaped","category":"misc",
    "pattern":["U","U"],"key":{"U":"#c:ingots/uranium"},
    "result":{"id":"obsidiannetwork:uranium_rod","count":1}})
emit("data/obsidiannetwork/worldgen/configured_feature/ore_uranium.json",{
    "type":"minecraft:ore","config":{
       "size":7,"discard_chance_on_air_exposure":0.0,
       "targets":[
         {"target":{"predicate_type":"minecraft:tag_match",
                    "tag":"minecraft:stone_ore_replaceables"},
          "state":{"Name":"obsidiannetwork:uranium_ore"}},
         {"target":{"predicate_type":"minecraft:tag_match",
                    "tag":"minecraft:deepslate_ore_replaceables"},
          "state":{"Name":"obsidiannetwork:uranium_ore"}}]}})
emit("data/obsidiannetwork/worldgen/placed_feature/ore_uranium.json",{
    "feature":"obsidiannetwork:ore_uranium",
    "placement":[{"type":"minecraft:count","count":6},
                 {"type":"minecraft:in_square"},
                 {"type":"minecraft:height_range",
                  "height":{"type":"minecraft:uniform",
                            "min_inclusive":{"absolute":-48},"max_inclusive":{"absolute":48}}},
                 {"type":"minecraft:biome"}]})
emit("data/obsidiannetwork/neoforge/biome_modifier/add_uranium_ore.json",{
    "type":"neoforge:add_features","biomes":"#minecraft:is_overworld",
    "features":"obsidiannetwork:ore_uranium","step":"underground_ores"})

labels = {
 "en_us": {"block.obsidiannetwork.uranium_ore":"Uranium Ore",
           "item.obsidiannetwork.raw_uranium":"Raw Uranium",
           "item.obsidiannetwork.uranium_ingot":"Uranium Ingot",
           "item.obsidiannetwork.uranium_rod":"Uranium Fuel Rod"},
 "de_de": {"block.obsidiannetwork.uranium_ore":"Uranerz",
           "item.obsidiannetwork.raw_uranium":"Rohuran",
           "item.obsidiannetwork.uranium_ingot":"Uranbarren",
           "item.obsidiannetwork.uranium_rod":"Uran-Brennstab"}}
for language, additions in labels.items():
    p = R / f"assets/obsidiannetwork/lang/{language}.json"
    translations = json.loads(p.read_text(encoding="utf-8"))
    assert not any(k in translations for k in additions), ("V174_LANGUAGE_COLLISION",language)
    translations.update(additions)
    p.write_text(json.dumps(translations,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("V174_URANIUM_FUEL_CHAIN_PASS: ore, raw, smelt+blast, common-tag 2-ingot rod, textures, worldgen")
