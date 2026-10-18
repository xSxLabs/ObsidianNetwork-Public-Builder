#!/usr/bin/env python3
"""User-requested quick mining for the two craftable/drop-enabled wireless points.

Apply after wireless runtime registration. Do not change the item IDs, loot
tables or recipe outputs. A 0.6 hardness block mines by hand and normal
non-explosive mining drops the registered block item.
"""
from pathlib import Path
import json
import os

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/ObsidianNetwork.java"
src=java.read_text(encoding="utf-8")
for slug in ("network_transmitter","network_receiver"):
    original=(f'"{slug}", props -> new dev.obsidiannetwork.block.WirelessNetworkBlock(')
    assert src.count(original)==1,f"registration missing/duplicated: {slug}"
    begin=src.index(original)
    end=src.index(");",begin)+2
    fragment=src[begin:end]
    old="props.mapColor(MapColor.COLOR_GRAY).strength(1.33F,12.0F).noOcclusion()"
    assert fragment.count(old)==1, f"unexpected mining properties: {slug}"
    src=src[:begin]+fragment.replace(old,
         "props.mapColor(MapColor.COLOR_GRAY).strength(0.6F,6.0F).noOcclusion()")+src[end:]
java.write_text(src,encoding="utf-8")

data=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
for slug in ("network_transmitter","network_receiver"):
    recipe=json.loads((data/"recipe"/f"{slug}.json").read_text())
    assert recipe["type"]=="minecraft:crafting_shaped"
    assert recipe["result"]=={"id":"obsidiannetwork:"+slug,"count":1}
    assert "obsidiannetwork:wireless_antenna" in recipe["key"].values()
    loot=json.loads((data/"loot_table/blocks"/f"{slug}.json").read_text())
    assert loot["type"]=="minecraft:block"
    assert any(entry.get("name")=="obsidiannetwork:"+slug
               for pool in loot["pools"] for entry in pool["entries"])
    assert (data.parent.parent/"assets/obsidiannetwork/models/item"/f"{slug}.json").is_file()
print("WIRELESS_QUICK_MINE_CRAFT_DROP_V2 PASS both nodes: hardness 0.6, survival recipes, self-drop, item models")
