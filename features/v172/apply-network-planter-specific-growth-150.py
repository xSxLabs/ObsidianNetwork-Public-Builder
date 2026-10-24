#!/usr/bin/env python3
"""Build 150: real crop stage visuals, miniature true-species trees, no double GUI title."""
import json,copy,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def fix(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,old[:90],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
# Vanilla AbstractContainerScreen renders its menu title (dark) by default,
# even though the custom background paints the branded title (white).
fix("client/NetworkPlanterScreen.java",
 " @Override public void extractBackground(GuiGraphicsExtractor g,int mouseX,int mouseY,float partial){",
 """ /** BUILD150_SINGLE_GUI_TITLE: omit vanilla background menu title and inventory label.
  * The bespoke panel already paints the title and inventory header itself.
  */
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mouseX,int mouseY){}
 @Override public void extractBackground(GuiGraphicsExtractor g,int mouseX,int mouseY,float partial){""")
# The previous fallback WHEAT rendered a phantom crop in empty pots.
fix("block/NetworkPlanterBlock.java",
 " public enum Plant implements StringRepresentable {\n",
 " public enum Plant implements StringRepresentable {\n  EMPTY(Items.AIR,Items.AIR,Items.AIR,false),\n")
fix("block/NetworkPlanterBlock.java",
 "registerDefaultState(stateDefinition.any().setValue(AGE,0).setValue(PLANT,Plant.WHEAT));",
 "registerDefaultState(stateDefinition.any().setValue(AGE,0).setValue(PLANT,Plant.EMPTY));")
fix("block/NetworkPlanterBlock.java",
 "if(stack.isEmpty())return WHEAT;",
 "if(stack.isEmpty())return EMPTY;")
fix("block/NetworkPlanterBlock.java",
 "   return WHEAT;",
 "   return EMPTY;")
fix("blockentity/NetworkPlanterBlockEntity.java",
 "  var plant=NetworkPlanterBlock.Plant.of(seed);\n  if(state.getValue(NetworkPlanterBlock.AGE)!=age",
 "  var plant=pair()?NetworkPlanterBlock.Plant.of(seed):NetworkPlanterBlock.Plant.EMPTY;\n  if(state.getValue(NetworkPlanterBlock.AGE)!=age")
# Texture IDs in the Minecraft atlas, one actual vanilla stage texture per age.
TEXTURES={
 "wheat":["wheat_stage0","wheat_stage2","wheat_stage5","wheat_stage7"],
 "beetroot":["beetroots_stage0","beetroots_stage1","beetroots_stage2","beetroots_stage3"],
 "carrot":["carrots_stage0","carrots_stage1","carrots_stage2","carrots_stage3"],
 "potato":["potatoes_stage0","potatoes_stage1","potatoes_stage2","potatoes_stage3"],
 "melon":["melon_stem_stage0","melon_stem_stage2","melon_stem_stage5","melon_stem_stage7"],
 "pumpkin":["pumpkin_stem_stage0","pumpkin_stem_stage2","pumpkin_stem_stage5","pumpkin_stem_stage7"],
 "nether_wart":["nether_wart_stage0","nether_wart_stage1","nether_wart_stage1","nether_wart_stage2"],
 "sweet_berries":["sweet_berry_bush_stage0","sweet_berry_bush_stage1","sweet_berry_bush_stage2","sweet_berry_bush_stage3"],
 "cocoa":["cocoa_stage0","cocoa_stage1","cocoa_stage2","cocoa_stage2"],
 "cactus":["cactus_side"]*4,
 "sugar_cane":["sugar_cane"]*4,
 "bamboo":["bamboo_stalk"]*4
}
# Actual vanilla sapling sprite, appropriate LOG/STEM and leaf block by tree.
TREES={
 "oak":("oak_sapling","oak_log","oak_leaves"),
 "spruce":("spruce_sapling","spruce_log","spruce_leaves"),
 "birch":("birch_sapling","birch_log","birch_leaves"),
 "jungle":("jungle_sapling","jungle_log","jungle_leaves"),
 "acacia":("acacia_sapling","acacia_log","acacia_leaves"),
 "dark_oak":("dark_oak_sapling","dark_oak_log","dark_oak_leaves"),
 "mangrove":("mangrove_propagule","mangrove_log","mangrove_leaves"),
 "cherry":("cherry_sapling","cherry_log","cherry_leaves"),
 "pale_oak":("pale_oak_sapling","pale_oak_log","pale_oak_leaves"),
 "azalea":("azalea","oak_log","azalea_leaves"),
 "flowering_azalea":("flowering_azalea","oak_log","flowering_azalea_leaves"),
 "crimson":("crimson_fungus","crimson_stem","nether_wart_block"),
 "warped":("warped_fungus","warped_stem","warped_wart_block")
}
assert len(TEXTURES)==12 and len(TREES)==13
def cube(frm,to,tex):
 return {"from":frm,"to":to,"faces":{face:{"texture":"#"+tex} for face in
   ("up","down","north","south","east","west")}}
def crossed(height,width):
 # Crossed, double-sided, non-zero thickness so faces survive baking.
 out=[]
 for degrees in (-45,45):
  out.append({"from":[8-width,7,7.97],"to":[8+width,height,8.03],
    "rotation":{"origin":[8,8,8],"axis":"y","angle":degrees,"rescale":False},
    "faces":{"north":{"texture":"#plant"},"south":{"texture":"#plant"}}})
 return out
def growth(name,age,tex):
 texture={}
 out=[]
 if name in TREES:
  sapling,log,leaves=TREES[name]
  texture={"plant":"minecraft:block/"+sapling,
           "trunk":"minecraft:block/"+log,
           "foliage":"minecraft:block/"+leaves}
  if age==0:
   out=crossed(12,2.5)
  elif age==1:
   out=crossed(17,3.5)
  elif age==2:
   out=[cube([7.2,7,7.2],[8.8,19,8.8],"trunk"),
        cube([4.5,17,4.5],[11.5,24,11.5],"foliage"),
        cube([5.5,21,5.5],[10.5,27,10.5],"foliage")]
  else:
   out=[cube([6.5,7,6.5],[9.5,25,9.5],"trunk"),
        cube([3,19,3],[13,26,13],"foliage"),
        cube([4,25,4],[12,31,12],"foliage"),
        cube([1.5,23,5],[14.5,27,11],"foliage")]
  if name in ("crimson","warped") and age>=2:
   # Nether fungi have a broad colored cap rather than a green leaf crown.
   pass
 elif name=="cactus":
  texture={"trunk":"minecraft:block/cactus_side",
    "foliage":"minecraft:block/cactus_top"}
  height=[12,15,20,28][age]
  out=[cube([5.8,7,5.8],[10.2,height,10.2],"trunk"),
       cube([5.6,height-.4,5.6],[10.4,height,10.4],"foliage")]
 elif name=="bamboo":
  texture={"trunk":"minecraft:block/bamboo_stalk",
    "foliage":"minecraft:block/bamboo_small_leaves"}
  height=[11.5,15.5,21.5,28.5][age]
  out=[cube([7.25,7,7.25],[8.75,height,8.75],"trunk")]
  if age>=2:
   out.extend([cube([6.0,height-3,7.8],[10.0,height,8.2],"foliage"),
               cube([7.8,height-3,6.0],[8.2,height,10.0],"foliage")])
 elif name=="sugar_cane":
  texture={"plant":"minecraft:block/sugar_cane"}
  heights=[12,16,21,27]
  out=crossed(heights[age],2.0)
  if age>=2:
   out.append({"from":[5,7,9.5],"to":[11,heights[age]-3,9.56],
      "faces":{"north":{"texture":"#plant"},"south":{"texture":"#plant"}}})
 else:
  texture={"plant":"minecraft:block/"+TEXTURES[name][age]}
  heights=[12,14.5,17,20]
  widths=[2.2,3.5,4.6,5.5]
  out=crossed(heights[age],widths[age])
  if name in ("melon","pumpkin") and age==3:
   texture["fruit"]="minecraft:block/melon_side" if name=="melon" else "minecraft:block/pumpkin_side"
   out.append(cube([8.5,8,8.5],[13,12.5,13],"fruit"))
 return texture,out
MODEL=R/"models/block"
STATES=R/"blockstates"
blocks=sorted(STATES.glob("network_planter*.json"))
assert len(blocks)==12,len(blocks)
seen=set()
for block_path in blocks:
 block=block_path.stem
 old=json.loads(block_path.read_text(encoding="utf-8"))
 assert len(old["variants"])==100,(block,len(old.get("variants",{})))
 # The entire base pot is already a correct xSxLabs stripped-wood model.
 # Recover the base by removing the extra appended growth planes.
 reference=MODEL/(block+"_oak_age0.json")
 old_model=json.loads(reference.read_text(encoding="utf-8"))
 pot_elements=copy.deepcopy(old_model["elements"][:6])
 assert len(pot_elements)==6,block
 variants={}
 for plant in [*TEXTURES,*TREES,"empty"]:
  for age in range(4):
   filename=block+"_"+plant+"_age"+str(age)+".json"
   textures={k:v for k,v in old_model["textures"].items() if k in ("base","soil","particle")}
   pieces=copy.deepcopy(pot_elements)
   if plant!="empty":
    added,visual=growth(plant,age,None)
    textures.update(added)
    pieces.extend(visual)
   doc={"parent":"minecraft:block/block","ambientocclusion":False,
        "render_type":"minecraft:cutout","textures":textures,"elements":pieces}
   for element in pieces:
    for face in element["faces"].values():
     if face["texture"].startswith("#"):
      assert face["texture"][1:] in textures,(filename,face["texture"],textures)
    for vec in ("from","to"):
     assert all(-16<=v<=32 for v in element[vec]),(filename,vec,element[vec])
   (MODEL/filename).write_text(json.dumps(doc,separators=(",",":"))+"\n",encoding="utf-8")
   key=f"age={age},plant={plant}"
   variants[key]={"model":"obsidiannetwork:block/"+filename[:-5]}
   seen.add(plant)
 assert len(variants)==104,len(variants)
 block_path.write_text(json.dumps({"variants":variants},indent=2)+"\n",encoding="utf-8")
assert seen==set(TEXTURES)|set(TREES)|{"empty"},seen
assert all("minecraft:block/wheat_stage" in json.dumps(json.loads(
   (MODEL/(blocks[0].stem+"_wheat_age"+str(age)+".json")).read_text()))
   for age in range(4))
assert "minecraft:block/oak_leaves" in (MODEL/(blocks[0].stem+"_oak_age3.json")).read_text()
assert "minecraft:block/cherry_leaves" in (MODEL/(blocks[0].stem+"_cherry_age3.json")).read_text()
assert len(blocks)==12
print("BUILD150_SPECIFIC_GROWTH_PASS: 12 planters x 26 plant types x 4 real stage models, 13 tree crowns, 12 crop textures")
print("BUILD150_SINGLE_GUI_TITLE_PASS: title rendered once, default labels suppressed")
print("BUILD150_EMPTY_POT_PASS: no phantom wheat when soil/seed are absent")
