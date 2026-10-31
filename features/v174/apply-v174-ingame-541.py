#!/usr/bin/env python3
"""B541 test feedback: hotbar-left compact HUD; one-tick NutriPaste helmet;
bucket-safe Network Tank; remove H; distinctly assembled industrial designs.
No recurring multiblock scans or additional server work for the textures.
"""
import os,json,struct,zlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel; text=p.read_text(encoding="utf-8")
 assert text.count(old)==1,("B541_SOURCE_DRIFT",rel,text.count(old),old[:130])
 p.write_text(text.replace(old,new,1),encoding="utf-8")
# HUD: the left edge of the vanilla hotbar is screenCenter-91. Anchor both
# 80px meters 8px LEFT of that edge, on the final 2 hotbar-height rows.
# Never cover the center hotbar and never put them 60+px up into chat.
patch("client/PowerArmorBuild98Client.java",
 "int x=8; // B537_HUD_BOTTOM_LEFT_FE",
 """int x=Math.max(3,mc.getWindow().getGuiScaledWidth()/2-91-88);
   // B541_HUD_LEFT_OF_HOTBAR_FE, fixed 8px separation at normal GUI scale""")
patch("client/PowerArmorBuild98Client.java",
 "int y=mc.getWindow().getGuiScaledHeight()-61;",
 "int y=mc.getWindow().getGuiScaledHeight()-29; // B541_HOTBAR_BOTTOM")
patch("client/PowerArmorBuild98Client.java",
 "int pasteWidth=80,px=8; // B537_HUD_BOTTOM_LEFT_PASTE",
 """int pasteWidth=80,px=Math.max(3,mc.getWindow().getGuiScaledWidth()/2-91-88);
   // B541_HUD_LEFT_OF_HOTBAR_PASTE""")
patch("client/PowerArmorBuild98Client.java",
 "int py=mc.getWindow().getGuiScaledHeight()-85;",
 "int py=mc.getWindow().getGuiScaledHeight()-47; // B541_TIGHT_HUD_ROWS")
# Remove misleading label. The framed slot alone indicates placement.
patch("client/NetworkTankScreen.java",
 'g.text(font,"H",leftPos+10,topPos+17,0xff92ddd1,false);',
 '/* B541_NO_H_LABEL: slot is self explanatory; no extra letter */')

# One-tick helmet refill; nonempty slots only => no extra work for idle tanks.
# Eimer output uses Fluid.getBucket(), never creates a bucket for arbitrary fluids.
p=J/"blockentity/NetworkTankBlockEntity.java"
src=p.read_text(encoding="utf-8")
start=src.index(" // B533_NETWORK_TANK_HELMET_FILL:")
end=src.index(" @Override protected void saveAdditional",start)
new=r''' // B541_TANK_ONE_TICK_NUTRIPASTE_AND_BUCKETS: server only, no idle cost.
 public static void tick(net.minecraft.world.level.Level level,net.minecraft.core.BlockPos pos,
       net.minecraft.world.level.block.state.BlockState state,NetworkTankBlockEntity be){
  if(level.isClientSide())return;
  var stack=be.helmet.getItem(0);
  if(stack.isEmpty())return;
  // Never inject any other fluid into a Power Armor helmet.
  boolean powerHelmet=dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(stack,0)>0;
  if(powerHelmet){
   long room=dev.obsidiannetwork.nutrition.NutriPaste.HELMET_CAPACITY-
     dev.obsidiannetwork.nutrition.NutriPaste.stored(stack);
   if(room<=0L)return;
   var tankFluid=net.neoforged.neoforge.fluids.capability.IFluidHandler.of(be.tank);
   var held=tankFluid.getFluidInTank(0);
   if(held.isEmpty()||held.getFluid()!=dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get())return;
   // B541_FAST_HELMET: exact full remaining capacity in one tick when available.
   int offer=(int)Math.min(room,(long)held.getAmount());
   if(offer<=0)return;
   var taken=tankFluid.drain(offer,net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
   if(taken.isEmpty()||taken.getFluid()!=dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get())return;
   long inserted=dev.obsidiannetwork.nutrition.NutriPaste.add(stack,taken.getAmount());
   if(inserted<taken.getAmount()){
    tankFluid.fill(new net.neoforged.neoforge.fluids.FluidStack(
      dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get(),
      taken.getAmount()-(int)inserted),
      net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
   }
   if(inserted>0)be.helmet.setChanged();
   return;
  }
  // B541_BUCKET_ONLY: empty single vanilla bucket -> exact fluid-specific bucket.
  // Filled buckets never drain backwards, and unsupported fluids stay untouched.
  if(!stack.is(net.minecraft.world.item.Items.BUCKET)||stack.getCount()!=1)return;
  var tankFluid=net.neoforged.neoforge.fluids.capability.IFluidHandler.of(be.tank);
  var held=tankFluid.getFluidInTank(0);
  if(held.isEmpty()||held.getAmount()<1000)return;
  var result=held.getFluid().getBucket();
  if(result==net.minecraft.world.item.Items.AIR||result==net.minecraft.world.item.Items.BUCKET)return;
  var drawn=tankFluid.drain(1000,net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
  if(drawn.isEmpty()||drawn.getAmount()!=1000||drawn.getFluid()!=held.getFluid()){
   if(!drawn.isEmpty())tankFluid.fill(drawn,net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
   return;
  }
  be.helmet.setItem(0,new net.minecraft.world.item.ItemStack(result));
 }
'''
src=src[:start]+new+src[end:]
p.write_text(src,encoding="utf-8")
# The slot is intentionally a single input/output place for helmets or empty buckets.
patch("menu/NetworkTankMenu.java",
 'return dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(stack,0)>0;',
 '''return stack.is(net.minecraft.world.item.Items.BUCKET)
    || dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(stack,0)>0; // B541_TANK_HELMET_OR_EMPTY_BUCKET_ONLY''')
patch("menu/NetworkTankMenu.java",
 'else if(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(src,0)>0){',
 '''else if(src.is(net.minecraft.world.item.Items.BUCKET)
       ||dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(src,0)>0){''')
# Enable a real NutriPaste bucket. All other fluid types keep their normal bucket.
patch("nutrition/NutriPasteFluids.java",
 'new BaseFlowingFluid.Properties(TYPE,SOURCE,FLOWING);',
 '''new BaseFlowingFluid.Properties(TYPE,SOURCE,FLOWING)
          .bucket(()->dev.obsidiannetwork.ObsidianNetwork.NUTRIPASTE_BUCKET.get());''')
p=J/"ObsidianNetwork.java";s=p.read_text(encoding="utf-8")
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_FEEDING ='
assert s.count(anchor)==1,("B541_FLUID_BUCKET_REGISTRATION_ANCHOR",s.count(anchor))
s=s.replace(anchor,'''   // B541_REAL_NUTRIPASTE_BUCKET: allows exactly 1000mB bucket output.
   public static final DeferredItem<net.minecraft.world.item.BucketItem> NUTRIPASTE_BUCKET =
     ITEMS.registerItem("nutripaste_bucket", properties ->
       new net.minecraft.world.item.BucketItem(
         dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get(),
         properties.stacksTo(1)));
'''+anchor,1)
p.write_text(s,encoding="utf-8")
# The new bucket has an item model and translations; no missing-asset icon.
item_model=A/"items/nutripaste_bucket.json"
item_model.parent.mkdir(parents=True,exist_ok=True)
item_model.write_text(json.dumps({"model":{"type":"minecraft:model",
"model":"obsidiannetwork:item/nutripaste_bucket"}},indent=2)+"\n",encoding="utf-8")
item= A/"models/item/nutripaste_bucket.json"
item.write_text(json.dumps({"parent":"minecraft:item/generated","textures":{
 "layer0":"minecraft:item/bucket",
 "layer1":"obsidiannetwork:item/nutripaste_bucket_liquid"}},indent=2)+"\n",encoding="utf-8")
for name,label in (("en_us","NutriPaste Bucket"),("de_de","NutriPaste-Eimer")):
 p=A/("lang/"+name+".json")
 data=json.loads(p.read_text(encoding="utf-8"));data["item.obsidiannetwork.nutripaste_bucket"]=label
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
# Pixel art PNGs: one-time asset generation only; no server renderer/tick.
def png(file,w,h,pixels):
 path=A/"textures"/file
 path.parent.mkdir(parents=True,exist_ok=True)
 raw=bytearray()
 for y in range(h):
  raw.append(0)
  for x in range(w):raw.extend(pixels(x,y))
 def chunk(k,v):return len(v).to_bytes(4,'big')+k+v+(zlib.crc32(k+v)&0xffffffff).to_bytes(4,'big')
 path.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+
   chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b""))
 return path
def liquid(x,y):
 if y<3 or y>13 or x<3 or x>12:return (0,0,0,0)
 if x in (3,12) or y in (3,13):return (0,0,0,0)
 t=((x*13+y*19)%9)-4
 return (171+t,112+t,67+t,240)
png("item/nutripaste_bucket_liquid.png",16,16,liquid)
# B541 final reference: reactor is mostly white structural ceramic with narrow
# inset dark technical vents, small bolts, and exposed graphite ribs.
# Unlike B533, NO full-width twin vents across the whole casing face.
def rside(x,y):
 c=(239,244,249,255)
 if x in (0,31) or y in (0,31):c=(97,112,129,255)
 elif x in (1,30) or y in (1,30):c=(204,214,227,255)
 elif x in (2,29) or y in (2,29):c=(249,252,255,255)
 elif (x in (3,28) and 3<=y<=28):c=(178,192,207,255)
 # Inset mechanical vent above and below the central white ceramic panel.
 if 7<=x<=24 and ((5<=y<=9) or (23<=y<=27)):
  c=(70,83,98,255)
  if y in (6,8,24,26) and 8<=x<=23:c=(28,41,54,255)
  if x in (8,13,18,23):c=(143,161,171,255)
 if (x,y) in ((4,4),(27,4),(4,27),(27,27)):c=(62,79,95,255)
 if (x,y) in ((5,5),(26,5),(5,26),(26,26)):c=(145,158,167,255)
 if 12<=y<=20 and 5<=x<=26:
  c=(246,249,251,255)
  if x in (5,26):c=(195,204,214,255)
 return c
def rtop(x,y):
 c=(237,243,249,255)
 if x in (0,31) or y in (0,31):return (94,108,122,255)
 if x in (1,30) or y in (1,30):return (204,218,226,255)
 if x in (3,28) or y in (3,28):return (248,252,255,255)
 if 9<=x<=22 and 9<=y<=22:return (230,238,243,255)
 return c
# Powerbank pictured: WHITE shell, cyan NEON horizontal and vertical rails,
# dark metal joiners in the corners. Strong blue-white only when charged.
def bside(x,y,charged):
 c=(239,247,252,255)
 if x in (0,31) or y in (0,31):c=(35,52,70,255)
 elif x in (1,30) or y in (1,30):c=(82,105,122,255)
 elif x in (2,29) or y in (2,29):c=(226,236,245,255)
 # Steel corner joints occupy only corner nodes, not all walls.
 if (x<7 or x>24) and (y<7 or y>24):
  c=(52,66,84,255)
  if x in (3,27) or y in (3,27):c=(124,143,158,255)
  if (x,y) in ((5,5),(26,5),(5,26),(26,26)):
   c=(88,226,252,255) if charged else (77,132,148,255)
 # Proper luminous LED strips run seamlessly over the white housing.
 if (y in (7,8,23,24) and 7<=x<=24) or (x in (7,8,23,24) and 9<=y<=22):
  c=(81,230,250,255) if charged else (83,131,149,255)
  if charged and (y in (8,23) or x in (8,23)):c=(157,250,255,255)
 if 10<=x<=21 and 10<=y<=21:
  c=(250,252,255,255)
  if x in (10,21) or y in (10,21):c=(214,226,235,255)
 return c
def btop(x,y,charged):
 if x in (0,31) or y in (0,31):return (36,53,68,255)
 if x in (1,30) or y in (1,30):return (104,125,144,255)
 if x in (5,6,25,26) or y in (5,6,25,26):
  return (103,237,250,255) if charged else (85,139,161,255)
 return (245,250,255,255)
# Rendered asset references remain constant for all reactor 5-64 and
# powerbank 3x3x3..3x3x12. Separate 3D cube sides/top prevent top-plane grids.
png("block/reactor_casing_formed.png",32,32,rside)
png("block/reactor_casing_formed_top.png",32,32,rtop)
for charged in (False,True):
 suffix="_lit" if charged else ""
 png("block/powerbank_casing_formed"+suffix+".png",32,32,
     lambda x,y,on=charged:bside(x,y,on))
 png("block/powerbank_casing_formed"+suffix+"_top.png",32,32,
     lambda x,y,on=charged:btop(x,y,on))
for machine in ("reactor_casing","powerbank_casing","powerbank_casing_lit"):
 # Convert formed models from 'cube_all' to face-selective white industrial
 # panels. No BE model renderer and no per-frame world inspection.
 base=machine.removesuffix("_lit")+"_formed"
 lit=machine.endswith("_lit")
 sprite=base+("_lit" if lit else "")
 model=A/"models/block"/(sprite+".json")
 assert model.is_file(),("B541_FORMED_MODEL_MISSING",sprite)
 model.write_text(json.dumps({
  "parent":"minecraft:block/cube",
  "textures":{"particle":"obsidiannetwork:block/"+sprite,
    "down":"obsidiannetwork:block/"+sprite+"_top",
    "up":"obsidiannetwork:block/"+sprite+"_top",
    **{face:"obsidiannetwork:block/"+sprite for face in ("north","south","east","west")}}
 },indent=2)+"\n",encoding="utf-8")
# Highlight only newly assembled skins; preserve all eight F/A/L variants.
for block in ("reactor_casing","powerbank_casing"):
 states=json.loads((A/"blockstates"/(block+".json")).read_text())
 assert len(states["variants"])==8,("B541_EIGHT_STATE_REGRESSION",block)
print("B541_HUD_HOTBAR_SIDE_TANK_HELMET_BUCKET_INDUSTRIAL_FORMS_PASS")
