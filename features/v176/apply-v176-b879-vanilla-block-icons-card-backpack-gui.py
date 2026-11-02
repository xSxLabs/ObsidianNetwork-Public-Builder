#!/usr/bin/env python3
"""B879: native Minecraft stone/obsidian cubes with tiny per-item corner badges,
Micro-MG matching the existing Power Armor upgrade CARD sprites, and 75%-size
virtual backpack listing icons with unscaled 64-bit quantity labels.
Stage after B878. Source-only: does not authorize build.
"""
from pathlib import Path
import os,json
from PIL import Image,ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

# ALL the other upgrade items use a complete framed 32x32 card texture.
# Earlier B863 incorrectly replaced that with a Nether Star background.
cards=A/"textures/item"
card=Image.open(cards/"power_card_speed.png").convert("RGBA")
assert card.size==(32,32),("B879_CARD_BASE_DRIFT",card.size)
# Recolor the existing frame's warm yellow pixel accent to Micro-MG cyan.
palette=card.load()
for y in range(32):
 for x in range(32):
  r,g,b,a=palette[x,y]
  if a>0 and r>=155 and g>=95 and b<=145 and r>g*0.90:
   palette[x,y]=(51,217,243,a)
d=ImageDraw.Draw(card)
# Clean ONLY the center of the old speed pictogram, preserving the frame.
d.rectangle((8,8,23,23),fill=(11,20,32,255))
# Compact glowing cyan rifle / right-arm barrel silhouette, actual 32px pixels.
cyan=(51,221,244,255)
dark=(13,72,110,255)
d.rectangle((10,14,22,16),fill=cyan)
d.rectangle((21,15,25,15),fill=(199,247,255,255))
d.rectangle((11,12,16,13),fill=dark)
d.rectangle((12,17,15,20),fill=cyan)
d.rectangle((16,17,20,18),fill=dark)
d.point((10,15),fill=(240,255,255,255))
card.save(cards/"power_card_micro_mg.png",optimize=True)
model=A/"models/item/power_card_micro_mg.json"
assert model.is_file()
model.write_text(json.dumps({"parent":"minecraft:item/generated",
 "textures":{"layer0":"obsidiannetwork:item/power_card_micro_mg"}},indent=2)+"\n")

# Model the SAME vanilla cobblestone/obsidian block in 3D. Badge is an
# independent transparent model overlay so it doesn't destroy stone detail.
# This keeps the Minecraft block look at GUI, in hand and on ground.
digits={
 "1":("010","110","010","010","111"),
 "2":("111","001","111","100","111"),
 "x":("000","101","010","101","000")
}
for item,texture,label in (
  ("compressed_cobblestone_1x","minecraft:block/cobblestone","1x"),
  ("compressed_cobblestone_3x","minecraft:block/cobblestone","2x"),
  ("compressed_obsidian_1x","minecraft:block/obsidian","1x")):
 model=A/"models/item"/(item+".json")
 old=json.loads(model.read_text(encoding="utf-8"))
 assert old["parent"]=="minecraft:block/cube_all",("B879_NOT_A_CUBE",item)
 model.write_text(json.dumps({"parent":"minecraft:block/cube_all",
   "textures":{"all":texture}},indent=2)+"\n",encoding="utf-8")
 # 16x16 transparent with a MINI 8x7-pixel upper-corner badge, not a giant
 # full-face 1x number or a second item count.
 badge=Image.new("RGBA",(16,16),(0,0,0,0))
 draw=ImageDraw.Draw(badge)
 draw.rectangle((0,0,8,6),fill=(10,12,18,224))
 for j,char in enumerate(label):
  for y,row in enumerate(digits[char]):
   for x,px in enumerate(row):
    if px=="1":draw.point((1+j*4+x,1+y),fill=(249,249,249,255))
 badge_path=cards/(item+"_badge_small.png")
 badge.save(badge_path,optimize=True)
 # Slim north+south+east+west flat overlay, exactly on outer surface;
 # no giant floating card attached to the block and no untextured black cube.
 badge_model=A/"models/item"/(item+"_badge_overlay.json")
 badge_model.write_text(json.dumps({
   "parent":"minecraft:block/block",
   "textures":{"badge":"obsidiannetwork:item/"+item+"_badge_small"},
   "elements":[
     {"from":[8,9,-0.02],"to":[16,16,0.02],
      "faces":{"north":{"texture":"#badge","uv":[0,0,16,16]}}},
     {"from":[8,9,15.98],"to":[16,16,16.02],
      "faces":{"south":{"texture":"#badge","uv":[0,0,16,16]}}},
     {"from":[15.98,9,8],"to":[16.02,16,16],
      "faces":{"east":{"texture":"#badge","uv":[0,0,16,16]}}},
     {"from":[-0.02,9,8],"to":[0.02,16,16],
      "faces":{"west":{"texture":"#badge","uv":[0,0,16,16]}}}
   ]},indent=2)+"\n",encoding="utf-8")
 client=A/"items"/(item+".json")
 assert client.is_file()
 client.write_text(json.dumps({"model":{
   "type":"minecraft:composite",
   "models":[
     {"type":"minecraft:model","model":"obsidiannetwork:item/"+item},
     {"type":"minecraft:model","model":"obsidiannetwork:item/"+item+"_badge_overlay"}
   ]}},indent=2)+"\n",encoding="utf-8")

# Draw the stored-list item slightly smaller than vanilla slots while leaving
# actual player inventory, magnet and all three cells at their normal scale.
# The quantity overlay in extractLabels stays fully sized and readable.
screen=J/"client/V176BackpackScreen.java"
s=screen.read_text(encoding="utf-8")
needle="public final class V176BackpackScreen extends ContainerScreen {"
assert s.count(needle)==1,("B879_BACKPACK_CLASS_DRIFT",s.count(needle))
injection="""public final class V176BackpackScreen extends ContainerScreen {
 @Override protected void renderSlotContents(
     net.minecraft.client.gui.GuiGraphicsExtractor g,
     net.minecraft.world.item.ItemStack stack,
     net.minecraft.world.inventory.Slot slot,
     String countText){
  if(slot.index>=4 && slot.index<49){
   // Scale only the 45 virtual listing slots around their center.
   // Vanilla inventory/modules do not shrink.
   float cx=slot.x+8.0F,cy=slot.y+8.0F;
   g.pose().pushMatrix();
   g.pose().translate(cx,cy);
   g.pose().scale(0.72F,0.72F);
   g.pose().translate(-cx,-cy);
   super.renderSlotContents(g,stack,slot,"");
   g.pose().popMatrix();
   return;
  }
  super.renderSlotContents(g,stack,slot,countText);
 }
"""
screen.write_text(s.replace(needle,injection,1),encoding="utf-8")
assert "scale(0.72F,0.72F)" in screen.read_text(encoding="utf-8")
print("B879_NATIVE_3D_STONE_CUBES_1X_2X_BADGES_UNIFORM_MICRO_MG_CARD_SMALL_BACKPACK_ICONS_READY")
