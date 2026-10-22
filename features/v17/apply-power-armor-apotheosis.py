#!/usr/bin/env python3
"""Optional Apotheosis v26.1 data-map integration for all MK1/MK2 Power Armor."""
import json
import os
from pathlib import Path

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/ObsidianNetwork.java"
resources=Path(os.environ["V1_RESOURCE_ROOT"])
text=java.read_text(encoding="utf-8")

# Fail closed if an item registry ID changes. These are REAL suit items;
# upgrade disks and the armor station must not inherit affix categories.
values={
    "minecraft:iron_sword":"apotheosis:melee_weapon",
    "minecraft:shulker_shell":"apotheosis:none"
}
for tier in ("","mk2_"):
    for piece in ("helmet","chestplate","leggings","boots"):
        key=f"power_armor_{tier}{piece}"
        assert f'ITEMS.registerItem("{key}"' in text, f"Missing v1.7 armor item {key}"
        values[f"obsidiannetwork:{key}"]=f"apotheosis:{piece}"

# Apotheosis 26.1 uses its item data map to resolve both the Reforging Table
# input category and its Gem Socketing/affix bonuses. No Java API dependency.
# Preserve Apotheosis's two bundled vanilla overrides in case this datapack
# takes precedence over the mod's packaged JSON resource.
target=resources/"data/apotheosis/data_maps/item/loot_category_overrides.json"
assert not target.exists(), "Unexpected existing Apotheosis loot-category override: do not overwrite"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps({"values":values},indent=2,sort_keys=True)+"\n",encoding="utf-8")
assert len(values)==10
print("CLEAN_V17_APOTHEOSIS_DATA_MAP PASS: eight Power Armor category overrides; optional integration")
