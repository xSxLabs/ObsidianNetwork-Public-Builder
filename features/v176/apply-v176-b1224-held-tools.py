#!/usr/bin/env python3
"""B1224: fix real handheld geometry, vanilla-sized centered hotbar icons and tool durability.

Runs AFTER native multitool and hammer model generation. Do not change textures,
mining rules, power armor, world rendering, or the 1.7.5 walk-in freeze.
"""
import copy
import itertools
import json
import math
import os
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
A = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"
MODELS = A / "models/item"

# ToolMaterial.applyToolProperties installs vanilla Netherite durability (2031).
# Applying the requested max damage BEFORE that call is not effective.
constructor = "super(ToolMaterial.NETHERITE.applyToolProperties(properties,BlockTags.MINEABLE_WITH_PICKAXE,8.0F,-3.0F,0.0F));"
for path, amount in (
    (J / "multitool/MultitoolItem.java", 6093),
    (J / "hammer/HammerItem.java", 12186),
):
    source = path.read_text(encoding="utf-8")
    assert source.count(constructor) == 1, ("B1224_DURABILITY_CONSTRUCTOR_CHANGED", str(path))
    fixed = constructor.replace("0.0F));", f"0.0F).durability({amount}));")
    path.write_text(source.replace(constructor, fixed, 1), encoding="utf-8")
    assert fixed in path.read_text(encoding="utf-8")

multitool_path = MODELS / "multitool.json"
hammer_path = MODELS / "hammer.json"
multitool = json.loads(multitool_path.read_text(encoding="utf-8"))
hammer = json.loads(hammer_path.read_text(encoding="utf-8"))
assert multitool.get("parent") == "minecraft:block/block", "B1224_NATIVE_MULTITOOL_MISSING"
assert len(multitool["elements"]) >= 2000, "B1224_MULTITOOL_MESH_CHANGED"
assert len(hammer["elements"]) == 110, "B1224_HAMMER_MESH_CHANGED"
assert hammer["display"]["thirdperson_righthand"]["rotation"] == [0, -90, 0]
assert multitool["display"]["thirdperson_righthand"]["rotation"] == [0, -90, 55]

# B1223 hammer's model was built around X=0/Z=0, whereas the hand render
# convention and original user BBModel both use an 8/8 center. That wrongly
# offsets the entire hammer from the fist *before* its display rotation.
# Move the exact existing geometry (no resampling and no UV/texture changes)
# so the grip's lower end starts at Y=0, like the held multitool.
for element in hammer["elements"]:
    for field in ("from", "to"):
        x, y, z = element[field]
        element[field] = [round(x + 8, 6), round(y + 2, 6), round(z + 8, 6)]

# Lower ONLY the multitool's first-person held pose; keep the correctly
# working third-person, inventory and armor gun rendering untouched.
for hand in ("firstperson_righthand", "firstperson_lefthand"):
    old = multitool["display"][hand]
    assert abs(old["translation"][1] - 1.9) < 0.0001, ("B1224_FP_ANCHOR_DRIFT", hand, old)
    old["translation"][1] = -0.5

# Both tools now share precisely the same genuine hand display transforms.
# Hammer proportions differ, but their lower grip points have been aligned.
for hand in ("firstperson_righthand", "firstperson_lefthand",
             "thirdperson_righthand", "thirdperson_lefthand"):
    hammer["display"][hand] = copy.deepcopy(multitool["display"][hand])

# Vanilla handheld items use [30,225,0] for the inventory view. Fit each
# real 3D silhouette into the central 13x13 pixels of a 16x16 hotbar slot
# (1.5 px padding on every side), rather than scaling about an off-center
# original Blockbench origin. No item icon may overflow its field.
def transformed_corners(model, angles):
    rx, ry, rz = (math.radians(a) for a in angles)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    for element in model["elements"]:
        lo, hi = element["from"], element["to"]
        for a, b, c in itertools.product((0, 1), repeat=3):
            x = (lo[0], hi[0])[a] - 8.0
            y = (lo[1], hi[1])[b] - 8.0
            z = (lo[2], hi[2])[c] - 8.0
            # Minecraft's XYZ display rotation, rightmost axis applied first.
            x, y = x * cz - y * sz, x * sz + y * cz
            x, z = x * cy + z * sy, -x * sy + z * cy
            y, z = y * cx - z * sx, y * sx + z * cx
            yield x, y

def centered_gui(model):
    angles = [30, 225, 0]
    pts = list(transformed_corners(model, angles))
    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    width, height = maxx - minx, maxy - miny
    assert 5 < width < 40 and 5 < height < 40, ("B1224_ICON_GEOMETRY", width, height)
    scale = round(min(0.625, 13.0 / max(width, height)), 6)
    tx = round(-(minx + maxx) * scale / 2.0, 6)
    ty = round(-(miny + maxy) * scale / 2.0, 6)
    assert max(width, height) * scale <= 13.001
    assert abs((maxx + minx) * scale / 2 + tx) < 0.0001
    assert abs((maxy + miny) * scale / 2 + ty) < 0.0001
    return {"rotation": angles, "translation": [tx, ty, 0],
            "scale": [scale, scale, scale]}

for name, path, model in (
    ("multitool", multitool_path, multitool),
    ("hammer", hammer_path, hammer),
):
    model["display"]["gui"] = centered_gui(model)
    path.write_text(json.dumps(model, separators=(",", ":"), ensure_ascii=False) + "\n",
                    encoding="utf-8")
    gui = model["display"]["gui"]
    print("B1224_CENTERED_HOTBAR", name, gui)

assert hammer["display"]["thirdperson_righthand"] == multitool["display"]["thirdperson_righthand"]
assert hammer["display"]["firstperson_righthand"] == multitool["display"]["firstperson_righthand"]
assert min(e["from"][2] for e in hammer["elements"]) > 5
print("B1224_HAMMER_HELD_LIKE_MULTITOOL_FP_LOWER_DURABILITY_6093_12186_PASS")
