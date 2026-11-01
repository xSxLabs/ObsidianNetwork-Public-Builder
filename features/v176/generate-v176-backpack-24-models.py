#!/usr/bin/env python3
"""Create 24 original, armor-palette-matched Backpack 3D models and textures.

Reads the actual MK1..MK24 GeckoLib suit texture atlases from reconstructed
resources; never copies Sophisticated Backpacks assets. Safe to rerun only
after clean resource reconstruction. Does NOT register items or blocks.
"""
import json
import os
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"
TEX = ROOT / "textures"
BLOCKS = ROOT / "models/block"
ITEMS = ROOT / "models/item"
DEFINITIONS = ROOT / "items"
for folder in (BLOCKS, ITEMS, DEFINITIONS, TEX / "block"):
    folder.mkdir(parents=True, exist_ok=True)

def swatch(armor):
    rgba = armor.convert("RGBA")
    # Keep opaque, saturated armor materials, not empty/transparent UV space.
    candidates = []
    for r, g, b, a in rgba.getdata():
        if a < 220:
            continue
        if max(r, g, b) < 26:
            continue
        candidates.append((r // 20 * 20, g // 20 * 20, b // 20 * 20))
    if not candidates:
        raise AssertionError("suit atlas has no visible palette")
    common = [p for p, _ in Counter(candidates).most_common(40)]
    body = max(common, key=lambda p: (p[0] + p[1] + p[2]) / 3)
    accent = max(common, key=lambda p: max(p) - min(p))
    muted = tuple(max(8, int(v * .48)) for v in body)
    light = tuple(min(255, int(v * 1.23 + 18)) for v in accent)
    return body, accent, muted, light

def faces(texture, uv):
    return {side: {"texture": texture, "uv": uv} for side in
        ("north", "south", "east", "west", "up", "down")}

def element(start, end, tex, uv):
    return {"from": start, "to": end, "faces": faces(tex, uv)}

# Distinct segments: body, armored rim, straps, light/emissive inset.
model = {
    "parent": "minecraft:block/block",
    "textures": {
        "particle": "#body",
        "body": "#body",
        "accent": "#accent",
        "dark": "#dark",
        "glow": "#glow"
    },
    "elements": [
        element([4, 2, 5.5], [12, 13.5, 10.5], "#body", [0, 0, 8, 12]),
        element([3.5, 10.5, 5], [12.5, 14, 11], "#accent", [8, 0, 16, 6]),
        element([4.4, 1.5, 5], [11.6, 3], "#dark", [0, 8, 8, 12]) if False else
        element([4.4, 1.5, 5], [11.6, 3, 11], "#dark", [0, 8, 8, 12]),
        element([3.6, 3.5, 5.1], [4.5, 12.5, 11.1], "#accent", [8, 0, 11, 11]),
        element([11.5, 3.5, 5.1], [12.4, 12.5, 11.1], "#accent", [8, 0, 11, 11]),
        element([6.0, 6.1, 4.4], [10.0, 9.2, 5.5], "#glow", [8, 8, 12, 12]),
        element([5, 13.5, 7.2], [11, 14.5, 10.5], "#dark", [0, 8, 8, 12]),
        # Two visible rear shoulder straps, and a side buckle.
        element([4.4, 2, 10.5], [5.5, 13, 11.6], "#dark", [0, 8, 8, 12]),
        element([10.5, 2, 10.5], [11.6, 13, 11.6], "#dark", [0, 8, 8, 12]),
        element([12.4, 7.1, 7.0], [13.0, 9.1, 10.3], "#glow", [8, 8, 12, 12])
    ],
    "display": {
        "gui": {"rotation": [22, 35, 0], "translation": [0, -0.5, 0], "scale": [0.9, 0.9, 0.9]},
        "ground": {"translation": [0, 2.5, 0], "scale": [0.6, 0.6, 0.6]},
        "thirdperson_righthand": {"rotation": [65, 40, 0], "scale": [0.55, 0.55, 0.55]},
        "firstperson_righthand": {"rotation": [0, -35, 0], "scale": [0.7, 0.7, 0.7]}
    }
}
assert len(model["elements"]) == 10
for tier in range(1, 25):
    slug = "network_backpack_mk" + str(tier)
    suit = TEX / "entity" / ("power_armor_visual_mk" + str(tier) + ".png")
    assert suit.is_file(), ("MISSING_REAL_SUIT_ATLAS", tier)
    with Image.open(suit) as image:
        colors = swatch(image)
    atlas = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
    pixels = atlas.load()
    body, accent, muted, light = colors
    for y in range(16):
        for x in range(16):
            chosen = body if x < 8 and y < 8 else accent if x >= 8 and y < 8 else muted if x < 8 else light
            shaded = tuple(min(255, max(0, v + (2 if (x+y) % 5 else -10))) for v in chosen)
            pixels[x, y] = (*shaded, 255)
    atlas.save(TEX / "block" / (slug + ".png"))
    full = json.loads(json.dumps(model))
    for name in ("body", "accent", "dark", "glow"):
        full["textures"][name] = "obsidiannetwork:block/" + slug
    # The 16x16 image contains independent quad swatches for every material.
    (BLOCKS / (slug + ".json")).write_text(json.dumps(full, indent=2) + "\n", encoding="utf-8")
    (ITEMS / (slug + ".json")).write_text(json.dumps(
        {"parent": "obsidiannetwork:block/" + slug}, indent=2) + "\n", encoding="utf-8")
    (DEFINITIONS / (slug + ".json")).write_text(json.dumps(
        {"model": {"type": "minecraft:model", "model": "obsidiannetwork:item/" + slug}},
        indent=2) + "\n", encoding="utf-8")
print("V176_BACKPACK_24_ORIGINAL_COLOR_MATCHED_MODELS PASS")
