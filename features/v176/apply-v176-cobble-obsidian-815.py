#!/usr/bin/env python3
"""v1.7.6: 9^3 normal Cobblestone -> one vanilla Obsidian.

9 cobblestone -> 1 compressed_cobblestone_1x ("1x Cobble")
9 1x Cobble -> 1 compressed_cobblestone_3x ("3x Cobble")
9 3x Cobble -> 1 vanilla obsidian. All recipe outputs count=1.
"""
import json, os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
first="compressed_cobblestone_1x"
third="compressed_cobblestone_3x"
recipes=(
 (first,"minecraft:cobblestone","obsidiannetwork:"+first),
 (third,"obsidiannetwork:"+first,"obsidiannetwork:"+third),
 ("obsidian_from_compressed_cobblestone","obsidiannetwork:"+third,"minecraft:obsidian")
)
assert 9*9*9==729

main=J/"ObsidianNetwork.java"
src=main.read_text(encoding="utf-8")
anchor="   public static final DeferredItem<net.minecraft.world.item.Item> NETWORK_BACKPACK_MAGNET_UPGRADE ="
assert src.count(anchor)==1,("B815_ITEM_ANCHOR_DRIFT",src.count(anchor))
insert="\n".join(
 '   public static final DeferredItem<net.minecraft.world.item.Item> '+field+' =\n'
 '      ITEMS.registerSimpleItem("'+ident+'",new net.minecraft.world.item.Item.Properties().stacksTo(64));'
 for field,ident in (("COMPRESSED_COBBLESTONE_1X",first),("COMPRESSED_COBBLESTONE_3X",third)))
src=src.replace(anchor,insert+"\n"+anchor,1)
anchor="            output.accept((ItemLike)NETWORK_BACKPACK_MAGNET_UPGRADE.get());"
assert src.count(anchor)==1,("B815_TAB_ANCHOR_DRIFT",src.count(anchor))
src=src.replace(anchor,anchor+
 "\n            output.accept((ItemLike)COMPRESSED_COBBLESTONE_1X.get());"+
 "\n            output.accept((ItemLike)COMPRESSED_COBBLESTONE_3X.get());",1)
main.write_text(src,encoding="utf-8")

root=R/"data/obsidiannetwork/recipe"
for name,ingredient,result in recipes:
 path=root/(name+".json")
 assert not path.exists(),("B815_RECIPE_ALREADY_EXISTS",str(path))
 data={"type":"minecraft:crafting_shaped","pattern":["CCC","CCC","CCC"],
       "key":{"C":ingredient},"result":{"id":result,"count":1}}
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
for name,texture in ((first,"minecraft:block/cobblestone"),
                     (third,"minecraft:block/cobbled_deepslate")):
 model=R/"assets/obsidiannetwork/models/item"/(name+".json")
 definition=R/"assets/obsidiannetwork/items"/(name+".json")
 for path in (model,definition):
  path.parent.mkdir(parents=True,exist_ok=True)
  assert not path.exists(),("B815_MODEL_ALREADY_EXISTS",str(path))
 model.write_text(json.dumps({"parent":"minecraft:item/generated",
     "textures":{"layer0":texture}},indent=2)+"\n",encoding="utf-8")
 definition.write_text(json.dumps({"model":{"type":"minecraft:model",
     "model":"obsidiannetwork:item/"+name}},indent=2)+"\n",encoding="utf-8")
for locale in ("de_de","en_us"):
 path=R/"assets/obsidiannetwork/lang"/(locale+".json")
 values=json.loads(path.read_text(encoding="utf-8"))
 for name,label in ((first,"1x Cobble"),(third,"3x Cobble")):
  key="item.obsidiannetwork."+name
  assert key not in values,("B815_LANG_ALREADY_DEFINED",key)
  values[key]=label
 path.write_text(json.dumps(values,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V176_B815_729_COBBLESTONE_PER_1_OBSIDIAN_3_UNIQUE_RECIPES PASS")
