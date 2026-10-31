#!/usr/bin/env python3
"""B533: unique formed reactor industrial panels, powered cyan bank edge bands, brown NutriPaste fluid."""
import json,math,os,struct,zlib
from pathlib import Path
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def png(name,w,h,pixel):
 path=A/"textures/block"/(name+".png")
 path.parent.mkdir(parents=True,exist_ok=True)
 raw=bytearray()
 for y in range(h):
  raw.append(0)
  for x in range(w):raw.extend(pixel(x,y))
 def chunk(t,v):
  return struct.pack(">I",len(v))+t+v+struct.pack(">I",zlib.crc32(t+v)&0xffffffff)
 path.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
   +chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b""))
 return path
# Characterful but performant 32px repeatable all-face textures; no per-tick mesh.
def reactor(x,y):
 # White ceramic casing, inset graphite vent grille, anti-alias-free steel borders.
 c=(229,235,240,255)
 if x in (0,31) or y in (0,31):c=(202,211,220,255)
 if x in (1,30) or y in (1,30):c=(247,250,251,255)
 if y in (3,4,27,28):c=(194,203,213,255)
 if 3<=x<=28 and (7<=y<=12 or 19<=y<=24):
  c=(173,184,195,255)
  if 4<=x<=27 and 8<=y<=11 or 4<=x<=27 and 20<=y<=23:
   c=(47,60,70,255)
   if y in (8,20):c=(96,109,117,255)
   if y in (11,23):c=(26,38,47,255)
   if 5<=x<=26 and x%4==0:c=(119,133,139,255)
 if x in (2,29) and y in (2,29):c=(84,103,115,255)
 if 13<=y<=18 and 4<=x<=27:c=(238,243,246,255)
 if 13<=y<=18 and x in (6,25):c=(145,159,170,255)
 return c
png("reactor_casing_formed",32,32,reactor)
# Powerbank casing: white structure, dark edge cap + cyan illuminated cable.
def powerbank(x,y,charged):
 c=(229,237,246,255)
 if x in (0,31) or y in (0,31):c=(51,68,83,255)
 if x in (1,30) or y in (1,30):c=(120,143,159,255)
 if x in (2,29) or y in (2,29):c=(245,249,252,255)
 if y in (5,6,25,26):
  c=(46,67,83,255) if x>1 and x<30 else (25,36,50,255)
  if charged and 3<=x<=28:c=(50,218,245,255) if y in (5,25) else (112,248,253,255)
  if not charged and 3<=x<=28:c=(71,111,125,255)
 if x in (4,5,26,27):
  if charged and 7<=y<=24:c=(68,193,219,255)
  elif 7<=y<=24:c=(79,101,116,255)
 if 7<=x<=24 and 9<=y<=22:c=(235,242,248,255)
 # Bold articulated bracket plates at all four corner joints.
 if ((x<7 or x>24) and (y<9 or y>22)):
  c=(47,62,77,255)
  if x in (2,29) or y in (2,29):c=(92,111,129,255)
  if x in (4,27) and y in (4,27):c=(151,167,174,255)
 return c
png("powerbank_casing_formed",32,32,lambda x,y:powerbank(x,y,False))
png("powerbank_casing_formed_lit",32,32,lambda x,y:powerbank(x,y,True))
# Keep the formed glass crystal clear: do not paste opaque casing details on it.
for name in ("reactor_glass","powerbank_glass"):
 path=A/"textures/block"/(name+"_formed.png")
 assert path.is_file(),("B533_GLASS_MISSING",name)
# Each formed tile refers to its own model. When bank LIT=true, use
# a distinct joined powered texture, without changing any registry IDs.
blockstates=A/"blockstates/powerbank_casing.json"
d=json.loads(blockstates.read_text())
assert len(d["variants"])==8,("B533_MODEL_STATE_COUNT",d["variants"])
for active in ("false","true"):
 key=f"formed=true,active={active},lit=true"
 assert d["variants"][key]["model"]=="obsidiannetwork:block/powerbank_casing_formed"
 d["variants"][key]["model"]="obsidiannetwork:block/powerbank_casing_formed_lit"
blockstates.write_text(json.dumps(d,indent=2)+"\n")
model=A/"models/block/powerbank_casing_formed_lit.json"
model.write_text(json.dumps({"parent":"minecraft:block/cube_all",
 "textures":{"all":"obsidiannetwork:block/powerbank_casing_formed_lit"}},indent=2)+"\n")
# Actual viscosity/paste tones, independent from tank tint and UI colors.
# 16x16 still, 32x32 flowing with fine creamy layered ribbons.
def still(x,y):
 wave=int(6*math.sin(x*.61+y*.47))
 grain=((x*37+y*53+x*y*13)%13)-6
 k=max(-18,min(16,wave+grain))
 if (x+y*2)%11==0:k+=17
 return (max(0,min(255,158+k)),max(0,min(255,113+k)),max(0,min(255,73+k//2)),255)
def flowing(x,y):
 v=int(9*math.sin((x+y*.58)*.32)+8*math.cos((y-x*.31)*.29))
 noise=((x*23+y*41)%17)-8
 a=v+noise
 return (max(0,min(255,152+a)),max(0,min(255,106+a)),max(0,min(255,63+a//2)),255)
png("nutripaste_still",16,16,still)
png("nutripaste_flowing",32,32,flowing)
# Modern NeoForge 26.1 FluidModel registry. Required for any modded tank,
# pipes and fluid-displays to use actual sprites instead of purple/black.
p=J/"nutrition/client/NutriPasteFluidModels.java"
assert not p.exists(),"B533_FLUID_REGISTRATION_COLLISION"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''package dev.obsidiannetwork.nutrition.client;
import dev.obsidiannetwork.nutrition.NutriPasteFluids;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.resources.model.Material;
import net.minecraft.resources.Identifier;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterFluidModelsEvent;
/** B533_BROWN_NUTRIPASTE_FLUID: model for native fluid tank renderers. */
@EventBusSubscriber(modid="obsidiannetwork", bus=EventBusSubscriber.Bus.MOD, value=Dist.CLIENT)
public final class NutriPasteFluidModels {
 private NutriPasteFluidModels(){}
 @SubscribeEvent public static void register(RegisterFluidModelsEvent event){
  event.register(new FluidModel.Unbaked(
      new Material(Identifier.fromNamespaceAndPath("obsidiannetwork","block/nutripaste_still")),
      new Material(Identifier.fromNamespaceAndPath("obsidiannetwork","block/nutripaste_flowing")),
      null,null),
      NutriPasteFluids.SOURCE,NutriPasteFluids.FLOWING);
 }
}
''')
print("B533_INDUSTRIAL_REACTOR_CYAN_BANK_AND_BROWN_FLUID_MODELS_PASS")
