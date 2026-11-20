#!/usr/bin/env python3
"""B1724: restore 2M/4M Storage Cell creative + JEI ingredient discovery.

In the final 1.7.8 baseline the items were registered and crafting recipes
packaged, but BUILD268 never added them to the actual creative inventory tab.
JEI's item ingredient discovery therefore omits these two registered items.
Keep every item identity, capacity, persisted component and recipe unchanged.
"""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
MAIN=J/"ObsidianNetwork.java"
original=MAIN.read_text(encoding="utf-8")
for tier in ("2M","4M"):
    assert f"STORAGE_CELL_{tier} = ITEMS.registerItem(" in original,(
        "B1724_CELL_REGISTRATION_MISSING",tier)
assert "output.accept((ItemLike)STORAGE_CELL_1M.get());" in original
assert "output.accept((ItemLike)STORAGE_CELL_512K.get());" in original
# Existing 1M output is inside the native creative tab population callback.
# Do not add a secondary JEI plugin, item, or category (duplicate entries).
old="            output.accept((ItemLike)STORAGE_CELL_1M.get());"
new='''            output.accept((ItemLike)STORAGE_CELL_1M.get());
            output.accept((ItemLike)STORAGE_CELL_2M.get());
            output.accept((ItemLike)STORAGE_CELL_4M.get());'''
assert original.count(old)==1,("B1724_CREATIVE_TAB_ANCHOR_DRIFT",original.count(old))
for tier in ("2M","4M"):
    assert f"output.accept((ItemLike)STORAGE_CELL_{tier}.get());" not in original,(
        "B1724_DUPLICATE_CELL_CREATIVE",tier)
updated=original.replace(old,new,1)
MAIN.write_text(updated,encoding="utf-8")
for tier in ("2M","4M"):
    assert updated.count(f"output.accept((ItemLike)STORAGE_CELL_{tier}.get());")==1

# The item model definition was optional in earlier builds but required by
# modern Minecraft's item-model loader. Never overwrite existing model art.
for tier in ("2m","4m"):
    model=R/f"assets/obsidiannetwork/models/item/storage_cell_{tier}.json"
    assert model.is_file(),("B1724_CELL_ITEM_MODEL_MISSING",tier)
    definition=R/f"assets/obsidiannetwork/items/storage_cell_{tier}.json"
    if not definition.exists():
        definition.parent.mkdir(parents=True,exist_ok=True)
        definition.write_text(json.dumps({
            "model":{"type":"minecraft:model",
                     "model":f"obsidiannetwork:item/storage_cell_{tier}"} },
            indent=2)+"\n",encoding="utf-8")
    data=json.loads(definition.read_text(encoding="utf-8"))
    assert data["model"]["model"]==f"obsidiannetwork:item/storage_cell_{tier}",(
        "B1724_ITEM_DESCRIPTOR_MISMATCH",tier)

for lang,label2,label4 in (
  ("de_de","2M-Speicherzelle","4M-Speicherzelle"),
  ("en_us","2M Storage Cell","4M Storage Cell")
):
    file=R/f"assets/obsidiannetwork/lang/{lang}.json"
    content=json.loads(file.read_text(encoding="utf-8"))
    # Preserve any existing (possibly richer) translations.
    content.setdefault("item.obsidiannetwork.storage_cell_2m",label2)
    content.setdefault("item.obsidiannetwork.storage_cell_4m",label4)
    file.write_text(json.dumps(content,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

# Native recipe registration is server-sided and JEI queries the same
# RecipeManager. Verify its exact post-B1711 shape and that its output is
# the registered item; unlike a JSON existence test, this detects accidental
# ordering regressions from a later recipe-repair overlay.
data=R/"data/obsidiannetwork/recipe"
four=json.loads((data/"storage_cell_4m.json").read_text(encoding="utf-8"))
assert four["type"]=="minecraft:crafting_shaped"
assert four["result"]["id"]=="obsidiannetwork:storage_cell_4m"
assert four["pattern"]==["NCN","CSC","NCN"]
assert four["key"]=={
    "N":"minecraft:netherite_block",
    "C":"obsidiannetwork:storage_cell_1m",
    "S":"minecraft:nether_star"
},("B1724_4M_RECIPE_DRIFT",four.get("key"))
two=json.loads((data/"storage_cell_2m.json").read_text(encoding="utf-8"))
assert two["result"]["id"]=="obsidiannetwork:storage_cell_2m"
assert "STORAGE_CELL_4M = ITEMS.registerItem(" in updated
assert "STORAGE_CELL_2M = ITEMS.registerItem(" in updated
print("B1724_2M_4M_STORAGE_CELLS_VISIBLE_CREATIVE_JEI_ENTRY_PASS",
      "2M=registered+listed+recipe+item_model",
      "4M=registered+listed+endgame_recipe+item_model")
