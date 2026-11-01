#!/usr/bin/env python3
"""Register 24 equivalent color-variant backpack items plus magnet upgrade.

Dedicated item behavior, GUI, storage backend, placeable world BE and cable
handlers are wired in the later backpack runtime step. This script alone does
NOT make the complete feature usable and must not trigger a release build.
"""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
main=J/"ObsidianNetwork.java"
src=main.read_text(encoding="utf-8")
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_MICRO_MG ='
assert src.count(anchor)==1,("BPK_REGISTRY_ANCHOR_DRIFT",src.count(anchor))
register=[]
for i in range(1,25):
 name=f"network_backpack_mk{i}"
 field=f"NETWORK_BACKPACK_MK{i}"
 register.extend([
  f"   public static final DeferredItem<dev.obsidiannetwork.backpack.NetworkBackpackItem> {field} =",
  f'      ITEMS.registerItem("{name}",p -> new dev.obsidiannetwork.backpack.NetworkBackpackItem(',
  '          p.stacksTo(1).component(net.minecraft.core.component.DataComponents.EQUIPPABLE,',
  '          net.minecraft.world.item.equipment.Equippable.builder(net.minecraft.world.entity.EquipmentSlot.CHEST).build()),'+str(i)+'));'
 ])
register.extend([
 "   public static final DeferredItem<net.minecraft.world.item.Item> NETWORK_BACKPACK_MAGNET_UPGRADE =",
 '      ITEMS.registerSimpleItem("network_backpack_magnet_upgrade",new net.minecraft.world.item.Item.Properties().stacksTo(1));'
])
src=src.replace(anchor,"\n".join(register)+"\n"+anchor,1)
creative='            output.accept((ItemLike)POWER_CARD_MICRO_MG.get());'
assert src.count(creative)==1,("BPK_CREATIVE_ANCHOR_DRIFT",src.count(creative))
entries="\n".join(f"            output.accept((ItemLike)NETWORK_BACKPACK_MK{i}.get());" for i in range(1,25))
src=src.replace(creative,creative+"\n"+entries+"\n"+
            "            output.accept((ItemLike)NETWORK_BACKPACK_MAGNET_UPGRADE.get());",1)
main.write_text(src,encoding="utf-8")

item=J/"backpack/NetworkBackpackItem.java"
item.parent.mkdir(parents=True,exist_ok=True)
assert not item.exists(),("BACKPACK_ALREADY_DEFINED",item)
item.write_text('''package dev.obsidiannetwork.backpack;

import net.minecraft.world.item.Item;

/** All 24 MK color variants have identical storage/upgrade mechanics. */
public final class NetworkBackpackItem extends Item {
 private final int visualTier;
 public NetworkBackpackItem(Properties properties,int visualTier){
  super(properties);
  if(visualTier<1||visualTier>24)throw new IllegalArgumentException("color tier");
  this.visualTier=visualTier;
 }
 public int visualTier(){return visualTier;}
}
''',encoding="utf-8")

dyes=("white","orange","magenta","light_blue","yellow","lime","pink","gray",
      "light_gray","cyan","purple","blue","brown","green","red","black")
recipe_dir=R/"data/obsidiannetwork/recipe"
recipe_dir.mkdir(parents=True,exist_ok=True)
seen=set()
for i in range(1,25):
 a=dyes[(i-1)%16]
 b=dyes[(i-1)//16]
 pair=(a,b)
 assert pair not in seen,pair
 seen.add(pair)
 name=f"network_backpack_mk{i}"
 path=recipe_dir/(name+".json")
 assert not path.exists(),("BACKPACK_RECIPE_COLLISION",name)
 recipe={
  "type":"minecraft:crafting_shaped",
  "pattern":["ICI","BDB","IEI"],
  "key":{"I":"minecraft:iron_ingot","C":"minecraft:"+a+"_dye",
         "D":"minecraft:chest","E":"minecraft:"+b+"_dye",
         "B":"minecraft:obsidian"},
  "result":{"id":"obsidiannetwork:"+name,"count":1}}
 path.write_text(json.dumps(recipe,indent=2)+"\n",encoding="utf-8")
m=recipe_dir/"network_backpack_magnet_upgrade.json"
assert not m.exists()
m.write_text(json.dumps({
 "type":"minecraft:crafting_shaped","pattern":["IRI","RCR","IRI"],
 "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone_block",
        "C":"minecraft:compass"},
 "result":{"id":"obsidiannetwork:network_backpack_magnet_upgrade","count":1}
},indent=2)+"\n",encoding="utf-8")

for lang in ("de_de","en_us"):
 path=R/f"assets/obsidiannetwork/lang/{lang}.json"
 data=json.loads(path.read_text(encoding="utf-8"))
 for tier in range(1,25):
  key=f"item.obsidiannetwork.network_backpack_mk{tier}"
  assert key not in data,key
  data[key]=f"Network Backpack MK{tier}" if lang=="en_us" else f"Network-Rucksack MK{tier}"
 key="item.obsidiannetwork.network_backpack_magnet_upgrade"
 assert key not in data,key
 data[key]="Network Backpack Magnet Upgrade" if lang=="en_us" else "Network-Rucksack Magnet-Upgrade"
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

assets=R/"assets/obsidiannetwork"
(assets/"models/item").mkdir(parents=True,exist_ok=True)
(assets/"items").mkdir(parents=True,exist_ok=True)
magmodel=assets/"models/item/network_backpack_magnet_upgrade.json"
magdef=assets/"items/network_backpack_magnet_upgrade.json"
for p in (magmodel,magdef):
 assert not p.exists(),p
magmodel.write_text(json.dumps({"parent":"minecraft:item/generated",
 "textures":{"layer0":"minecraft:item/compass"}},indent=2)+"\n",encoding="utf-8")
magdef.write_text(json.dumps({"model":{"type":"minecraft:model",
 "model":"obsidiannetwork:item/network_backpack_magnet_upgrade"}},indent=2)+"\n",encoding="utf-8")

tag=R/"data/curios/tags/item/back.json"
tag.parent.mkdir(parents=True,exist_ok=True)
if tag.is_file():
 existing=json.loads(tag.read_text(encoding="utf-8"))
else:existing={"replace":False,"values":[]}
for tier in range(1,25):
 id=f"obsidiannetwork:network_backpack_mk{tier}"
 if id not in existing["values"]:existing["values"].append(id)
tag.write_text(json.dumps(existing,indent=2)+"\n",encoding="utf-8")
print("V176_BACKPACK_24_ITEMS_CURIOS_BACK_MAGNET_AND_UNIQUE_RECIPES_REGISTERED")
