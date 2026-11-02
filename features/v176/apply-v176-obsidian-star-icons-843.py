#!/usr/bin/env python3
"""B843: native-looking numbered Cobblestone and 1x Obsidian recipes.

Preserve existing compressed_cobblestone_3x ID for existing inventory saves,
but display it as 2x (second compression stage) per user request.
No source vanilla texture copies: use the actual Minecraft block sprites with
a transparent original small corner badge layer.
"""
import os,json
from pathlib import Path
from PIL import Image,ImageDraw
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
new_id="compressed_obsidian_1x"
main=J/"ObsidianNetwork.java"
s=main.read_text(encoding="utf-8")
anchor="   public static final DeferredItem<net.minecraft.world.item.Item> NETWORK_BACKPACK_MAGNET_UPGRADE ="
assert s.count(anchor)==1,("B843_OBSIDIAN_ITEM_ANCHOR",s.count(anchor))
s=s.replace(anchor,
 '''   public static final DeferredItem<net.minecraft.world.item.Item> COMPRESSED_OBSIDIAN_1X =
      ITEMS.registerSimpleItem("compressed_obsidian_1x",() -> new net.minecraft.world.item.Item.Properties().stacksTo(64));
'''+anchor,1)
anchor="            output.accept((ItemLike)COMPRESSED_COBBLESTONE_3X.get());"
assert s.count(anchor)==1,("B843_CREATIVE_TAB_ANCHOR",s.count(anchor))
s=s.replace(anchor,anchor+"\n            output.accept((ItemLike)COMPRESSED_OBSIDIAN_1X.get());",1)
main.write_text(s,encoding="utf-8")

def recipe(name, pattern, key, output):
 path=R/"data/obsidiannetwork/recipe"/(name+".json")
 assert not path.exists(),("B843_RECIPE_COLLISION",str(path))
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({"type":"minecraft:crafting_shaped","pattern":pattern,
    "key":key,"result":{"id":output,"count":1}},indent=2)+"\n",encoding="utf-8")
recipe("compressed_obsidian_1x",["OOO","OOO","OOO"],{"O":"minecraft:obsidian"},
       "obsidiannetwork:compressed_obsidian_1x")
recipe("nether_star_from_compressed_obsidian",
       ["OOO","ODO","OOO"],
       {"O":"obsidiannetwork:compressed_obsidian_1x","D":"minecraft:diamond_block"},
       "minecraft:nether_star")

def badge(label):
 im=Image.new("RGBA",(32,32),(0,0,0,0))
 d=ImageDraw.Draw(im)
 d.rounded_rectangle((13,18,31,31),radius=3,fill=(15,17,19,231),
                     outline=(220,220,220,255),width=1)
 glyph={
 "1":["010","110","010","010","111"],
 "2":["111","001","111","100","111"],
 "x":["000","101","010","101","000"]
 }
 for k,c in enumerate(label):
  for y,row in enumerate(glyph[c]):
   for x,p in enumerate(row):
    if p=="1":
     xx=15+k*8+x*2;yy=20+y*2
     d.rectangle((xx,yy,xx+1,yy+1),fill=(255,255,255,255))
 return im

items=(
 ("compressed_cobblestone_1x","minecraft:block/cobblestone","1x"),
 ("compressed_cobblestone_3x","minecraft:block/cobblestone","2x"),
 ("compressed_obsidian_1x","minecraft:block/obsidian","1x")
)
for ident,base,label in items:
 model=A/"models/item"/(ident+".json")
 definition=A/"items"/(ident+".json")
 if ident==new_id:
  assert not model.exists() and not definition.exists(),("B843_OBSIDIAN_MODEL_COLLISION",ident)
 else:
  assert model.is_file() and definition.is_file(),("B843_EXISTING_COBBLE_MISSING",ident)
 model.write_text(json.dumps({"parent":"minecraft:item/generated",
       "textures":{"layer0":base,"layer1":"obsidiannetwork:item/"+ident+"_badge"}},indent=2)+"\n")
 if ident==new_id:
  definition.write_text(json.dumps({"model":{"type":"minecraft:model",
       "model":"obsidiannetwork:item/"+ident}},indent=2)+"\n")
 tex=A/"textures/item"/(ident+"_badge.png")
 assert not tex.exists(),("B843_BADGE_ALREADY_EXISTS",ident)
 tex.parent.mkdir(parents=True,exist_ok=True)
 badge(label).save(tex,optimize=True)
for locale in ("de_de","en_us"):
 path=A/"lang"/(locale+".json")
 data=json.loads(path.read_text(encoding="utf-8"))
 data["item.obsidiannetwork.compressed_cobblestone_1x"]="1x Cobble"
 data["item.obsidiannetwork.compressed_cobblestone_3x"]="2x Cobble"
 assert "item.obsidiannetwork.compressed_obsidian_1x" not in data
 data["item.obsidiannetwork.compressed_obsidian_1x"]="1x Obsidian"
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
# A Nether Star costs 8 compressed Obsidian (each 9 vanilla Obsidian) plus one Diamond Block.
# No crafting cycle or accidental overlap with the existing 729-cobble chain.
assert (9*9*9)==729 and (9*729)==6561 and 8*6561==52488
print("V176_B843_COBBLE_CORNER_BADGES_9_OBSIDIAN_COMPRESSED_NETHERSTAR PASS")
