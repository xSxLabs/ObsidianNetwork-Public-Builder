#!/usr/bin/env python3
"""B1226: make BOTH native Netherite tools enchantable like a real pickaxe.

Use Minecraft's data-driven item tags, not a vanilla-only enchantment whitelist.
Compatible modded enchantments that target #minecraft:pickaxes or derived
enchantable/mining/mining_loot/durability tags can apply in Survival.
Multitool also advertises its existing axe/shovel compatibility.
"""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
for name,durability in (("multitool",6093),("hammer",12186)):
 path=J/name/(name.capitalize()+"Item.java")
 old=f"0.0F).durability({durability}));"
 src=path.read_text(encoding="utf-8")
 assert src.count(old)==1,("B1226_TOOL_CONSTRUCTOR_DRIFT",name,src.count(old))
 # Vanilla tool enchantability = 15. Keep the B1224 durability override
 # AFTER ToolMaterial.applyToolProperties; do not reset the mining tool or XP.
 src=src.replace(old,f"0.0F).durability({durability}).enchantable(15));",1)
 path.write_text(src,encoding="utf-8")
 assert ".enchantable(15)" in src

tags={
 "pickaxes":["obsidiannetwork:multitool","obsidiannetwork:hammer"],
 "axes":["obsidiannetwork:multitool"],
 "shovels":["obsidiannetwork:multitool"],
}
# Merge without replacing vanilla / another mod's entries; 26.1.2 resolves
# enchantments through the #minecraft:pickaxes item tag (and its derived tags).
for key,ids in tags.items():
 path=R/"data/minecraft/tags/item"/f"{key}.json"
 path.parent.mkdir(parents=True,exist_ok=True)
 data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"replace":False,"values":[]}
 assert isinstance(data.get("values"),list),("B1226_TAG_FORMAT",str(path))
 data["replace"]=False
 for name in ids:
  if name not in data["values"]:data["values"].append(name)
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

for slug in ("multitool","hammer"):
 jsonpath=R/"data/minecraft/tags/item/pickaxes.json"
 assert "obsidiannetwork:"+slug in json.loads(jsonpath.read_text())["values"]
print("B1226_SURVIVAL_ENCHANT_TABLE_ANVIL_VANILLA_AND_MODDED_PICKAXE_TAGS_PASS")
