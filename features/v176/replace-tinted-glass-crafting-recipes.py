#!/usr/bin/env python3
"""Replace tinted glass INPUTS in every generated ObsidianNetwork crafting recipe.

Apply as the last resource transformation, after all recipe generators/collision
fixes. Never change recipe outputs, non-crafting recipes, other mod namespaces,
inventory code, or existing Cell Terminal/Power Armor mechanics.
"""
import argparse
import json
from pathlib import Path

OLD = {"minecraft:tinted_glass", "tinted_glass"}
NEW = "minecraft:glass"
RECIPE_DIRECTORIES = ("recipe", "recipes")
OUTPUT_FIELDS = {"result", "output"}


def is_crafting(recipe):
    if not isinstance(recipe, dict):
        raise ValueError("Recipe root must be a JSON object")
    kind = recipe.get("type")
    return isinstance(kind, str) and "crafting" in kind.split(":")[-1]


def change_inputs(node):
    """Transform only exact item IDs, recursively excluding all output values."""
    if isinstance(node, str):
        return (NEW, 1) if node in OLD else (node, 0)
    if isinstance(node, list):
        total = 0
        out = []
        for value in node:
            replacement, n = change_inputs(value)
            out.append(replacement)
            total += n
        return out, total
    if isinstance(node, dict):
        out = {}
        total = 0
        for key, value in node.items():
            if key in OUTPUT_FIELDS:
                out[key] = value
            else:
                out[key], n = change_inputs(value)
                total += n
        return out, total
    return node, 0


def recipe_paths(resources):
    data = resources / "data" / "obsidiannetwork"
    found = []
    for directory in RECIPE_DIRECTORIES:
        root = data / directory
        if root.is_dir():
            found.extend(p for p in root.rglob("*.json") if p.is_file())
    return sorted(set(found))


def process(resources, apply=False):
    resources = Path(resources)
    if not resources.is_dir():
        raise FileNotFoundError(f"Resources not found: {resources}")
    paths = recipe_paths(resources)
    if not paths:
        raise RuntimeError("No ObsidianNetwork recipes found; refusing false-green verification")
    seen = 0
    changed_files = 0
    changed_ingredients = 0
    remaining = []
    for file in paths:
        recipe = json.loads(file.read_text(encoding="utf-8"))
        if not is_crafting(recipe):
            continue
        seen += 1
        amended, replacements = change_inputs(recipe)
        if replacements:
            if not apply:
                remaining.append(str(file))
            else:
                file.write_text(
                    json.dumps(amended, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8"
                )
                changed_files += 1
                changed_ingredients += replacements
        # Always verify actual JSON after modifications and only count inputs.
        current = json.loads(file.read_text(encoding="utf-8"))
        _, outstanding = change_inputs(current)
        if apply and outstanding:
            raise AssertionError(f"Crafting recipe still uses tinted glass: {file}")
    if not apply and remaining:
        raise AssertionError(
            f"{len(remaining)} ObsidianNetwork crafting recipes still use tinted glass:\n"
            + "\n".join(remaining)
        )
    if seen == 0:
        raise RuntimeError("No crafting recipes discovered; cannot verify glass replacement")
    print(
        f"OBSIDIAN_NETWORK_CRAFTING_GLASS_VERIFIED recipes={seen} "
        f"modified_files={changed_files} replaced_ingredients={changed_ingredients} "
        f"mode={'apply' if apply else 'verify'}"
    )
    return changed_files, changed_ingredients


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("resources", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    process(args.resources, apply=args.apply)
