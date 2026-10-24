#!/usr/bin/env python3
"""Build151: fix Network Planter runtime Missing Texture sprites for MC 26.1.2.

Build150 used model-file names (melon_stem_stage0 etc.) as sprites; those
textures do not exist. Vanilla uses one melon_stem and one pumpkin_stem
texture at every growth stage. Azaleas likewise use *_azalea_plant sprites.
26.1 automatically selects the correct render pass per sprite; drop the
legacy forced render_type from our generated models.
"""
import json
import os
from pathlib import Path

root = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"
models = root / "models/block"
states = root / "blockstates"
blocks = sorted(states.glob("network_planter*.json"))
assert len(blocks) == 12, ("wood variants", len(blocks))

# These are actual vanilla sprite IDs, not block-model or blockstate names.
bad_to_good = {
    **{"minecraft:block/melon_stem_stage" + str(n): "minecraft:block/melon_stem"
       for n in (0, 2, 5, 7)},
    **{"minecraft:block/pumpkin_stem_stage" + str(n): "minecraft:block/pumpkin_stem"
       for n in (0, 2, 5, 7)},
    "minecraft:block/azalea": "minecraft:block/azalea_plant",
    "minecraft:block/flowering_azalea": "minecraft:block/flowering_azalea_plant",
}
# Explicit 26.1.2 block atlas sprites used by the generated planter models.
# This catches invalid sprite references even when a face variable is defined.
known = set("""
    dirt melon_side pumpkin_side melon_stem pumpkin_stem
    wheat_stage0 wheat_stage2 wheat_stage5 wheat_stage7
    beetroots_stage0 beetroots_stage1 beetroots_stage2 beetroots_stage3
    carrots_stage0 carrots_stage1 carrots_stage2 carrots_stage3
    potatoes_stage0 potatoes_stage1 potatoes_stage2 potatoes_stage3
    nether_wart_stage0 nether_wart_stage1 nether_wart_stage2
    sweet_berry_bush_stage0 sweet_berry_bush_stage1
    sweet_berry_bush_stage2 sweet_berry_bush_stage3
    cocoa_stage0 cocoa_stage1 cocoa_stage2 cactus_side cactus_top
    sugar_cane bamboo_stalk bamboo_small_leaves
    oak_sapling oak_log oak_leaves spruce_sapling spruce_log spruce_leaves
    birch_sapling birch_log birch_leaves jungle_sapling jungle_log jungle_leaves
    acacia_sapling acacia_log acacia_leaves
    dark_oak_sapling dark_oak_log dark_oak_leaves
    mangrove_propagule mangrove_log mangrove_leaves
    cherry_sapling cherry_log cherry_leaves
    pale_oak_sapling pale_oak_log pale_oak_leaves
    azalea_plant azalea_leaves flowering_azalea_plant flowering_azalea_leaves
    crimson_fungus crimson_stem nether_wart_block
    warped_fungus warped_stem warped_wart_block
    stripped_oak_log stripped_spruce_log stripped_birch_log
    stripped_jungle_log stripped_acacia_log stripped_dark_oak_log
    stripped_mangrove_log stripped_cherry_log stripped_pale_oak_log
    stripped_bamboo_block stripped_crimson_stem stripped_warped_stem
""".split())

total = 0
repaired = {}
for block in blocks:
    variants = json.loads(block.read_text(encoding="utf-8"))["variants"]
    assert len(variants) == 104, (block.name, len(variants))
    for key, assignment in variants.items():
        filename = assignment["model"].split(":", 1)[1]
        assert filename.startswith("block/"), (key, filename)
        target = models / (filename.removeprefix("block/") + ".json")
        assert target.is_file(), (block.name, key, str(target))
        obj = json.loads(target.read_text(encoding="utf-8"))
        textures = obj["textures"]
        assert len(obj["elements"]) >= 6, (target.name, "missing pot")
        for name, value in list(textures.items()):
            if value in bad_to_good:
                textures[name] = bad_to_good[value]
                repaired[value] = repaired.get(value, 0) + 1
            value = textures[name]
            assert isinstance(value, str), (target.name, name, value)
            if value.startswith("minecraft:block/"):
                assert value[16:] in known, (target.name, name, value)
        # MC 26.1+ assigns the solid/cutout/translucent pass automatically
        # based on the sprite, so older forced 'render_type' is unnecessary.
        obj.pop("render_type", None)
        for piece in obj["elements"]:
            for face in piece["faces"].values():
                tex = face["texture"]
                assert tex.startswith("#"), (target.name, tex)
                assert tex[1:] in textures, (target.name, tex)
            for coord in ("from", "to"):
                assert all(-16 <= n <= 32 for n in piece[coord]), (target.name, coord)
        plant = key.split("plant=", 1)[1]
        if plant in ("melon", "pumpkin"):
            assert textures["plant"] == "minecraft:block/" + plant + "_stem", target.name
        elif plant in ("azalea", "flowering_azalea"):
            if "plant" in textures:
                assert textures["plant"] == "minecraft:block/" + plant + "_plant", target.name
            else:
                # Later tree stages display actual foliage rather than sapling planes.
                assert textures["foliage"] == "minecraft:block/" + plant + "_leaves", target.name
        target.write_text(json.dumps(obj, separators=(",", ":")) + "\n", encoding="utf-8")
        total += 1

assert total == 12 * 26 * 4, total
assert sum(repaired.values()) == 12 * 4 * 4, repaired
for old in bad_to_good:
    if old in repaired:
        assert repaired[old] == 12 * (4 if old in
            ("minecraft:block/azalea", "minecraft:block/flowering_azalea") else 1), (old, repaired[old])
assert repaired.get("minecraft:block/azalea") == 48
assert repaired.get("minecraft:block/flowering_azalea") == 48
print("BUILD151_PLANTER_TEXTURE_PASS: validated", total,
      "models across 12 woods/26 species/4 ages; repaired", sum(repaired.values()),
      "bad sprite references; removed legacy forced render_type")
