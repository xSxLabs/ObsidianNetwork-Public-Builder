#!/usr/bin/env python3
"""v1.7.6: register installable FE Micro-MG armor module.
Runs after B662 and recipe generators. Combat/Actionswheel integration is separate.
"""
import json, os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

def inject(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_MODULE_ANCHOR_DRIFT",rel,s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

inject("ObsidianNetwork.java",
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_ENERGY_SHIELD =',
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_MICRO_MG =\n'
 '      ITEMS.registerItem("power_card_micro_mg",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"micro_mg"));\n'
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_ENERGY_SHIELD =')
inject("ObsidianNetwork.java",
 '            output.accept((ItemLike)POWER_CARD_ENERGY_SHIELD.get());',
 '            output.accept((ItemLike)POWER_CARD_ENERGY_SHIELD.get());\n'
 '            output.accept((ItemLike)POWER_CARD_MICRO_MG.get());')
inject("powerarmor/PowerArmorCards.java",
 '   default -> null;',
 '   case "micro_mg" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_MICRO_MG.get();\n'
 '   default -> null;')

def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 assert not path.exists(),("V176_EXISTING_RESOURCE",str(path))
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

root=R/"assets/obsidiannetwork"
write(root/"models/item/power_card_micro_mg.json",
 {"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/crossbow"}})
write(root/"items/power_card_micro_mg.json",
 {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_micro_mg"}})
write(R/"data/obsidiannetwork/recipe/power_card_micro_mg.json",
 {"type":"minecraft:crafting_shaped","pattern":["CEC","EUE","CEC"],
  "key":{"C":"minecraft:copper_block","E":"minecraft:redstone_block",
         "U":"obsidiannetwork:power_armor_upgrade"},
  "result":{"id":"obsidiannetwork:power_card_micro_mg","count":1}})
for lang,name in (("de_de","Power-Ruestung Mikro-MG-Modul"),
                  ("en_us","Power Armor Micro-MG Module")):
 path=root/"lang"/(lang+".json")
 data=json.loads(path.read_text(encoding="utf-8"))
 key="item.obsidiannetwork.power_card_micro_mg"
 assert key not in data
 data[key]=name
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("V176_MICRO_MG_REGISTERED_AND_STATION_INSTALLABLE PASS")