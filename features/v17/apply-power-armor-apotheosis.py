#!/usr/bin/env python3
"""Power Armor MK1/MK2 -> Apotheosis 26.1 loot-category data map, optional compat.

Source: Apotheosis schema/loot/LootCategory.md (26.1). Reforging and Gem systems
select the supported armor slot from apotheosis:loot_category_overrides.
No Java linkage or hard dependency; existing ItemStack components are unchanged.
"""
import json
import os
from pathlib import Path

PARTS = ("helmet", "chestplate", "leggings", "boots")
CATEGORY_OVERRIDES = {
    f"obsidiannetwork:power_armor_{prefix}{part}": f"apotheosis:{part}"
    for prefix in ("", "mk2_")
    for part in PARTS
}

assert len(CATEGORY_OVERRIDES) == 8
assert set(CATEGORY_OVERRIDES.values()) == {f"apotheosis:{part}" for part in PARTS}

root = Path(os.environ["V1_RESOURCE_ROOT"])
target = root / "data/apotheosis/data_maps/item/loot_category_overrides.json"
if target.exists():
    obj = json.loads(target.read_text(encoding="utf-8"))
    assert isinstance(obj, dict) and isinstance(obj.get("values"), dict), (
        "Do not overwrite unrelated existing Apotheosis category data maps"
    )
else:
    obj = {"values": {}}
for item, category in CATEGORY_OVERRIDES.items():
    prior = obj["values"].get(item)
    assert prior in (None, category), f"Conflicting Apotheosis category: {item}"
    obj["values"][item] = category
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("CLEAN_V17_APOTHEOSIS_COMPAT PASS: 8 armor IDs, data-only optional Gem/reforging categories")
