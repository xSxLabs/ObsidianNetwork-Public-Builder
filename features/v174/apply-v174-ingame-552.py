#!/usr/bin/env python3
"""B552 in-game fixes: 50% HUD text, real energy input collar, joined white multiblock skins.

Client presentation and one renderer-only model registration. No FE/t logic,
solar scheduling, server-side cable traversal, or reactor/powerbank tick changes.
Applied AFTER B541 visuals, B533 collar material fix and all older v174 gates.
"""
import json, os, struct, zlib
from collections import Counter
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def replace(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B552_JAVA_SOURCE_DRIFT",rel,old[:90],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# B552 HUD: halve the *actual glyphs* using 26.1 GuiGraphicsExtractor's
# Matrix3x2fStack, not just the backing bar. Leave the FE percentage/math
# and paste tank calculations entirely unchanged. Both labels remain on
# the left of the hotbar, much closer to the bottom of the screen.
hud="client/PowerArmorBuild98Client.java"
replace(hud,"int y=mc.getWindow().getGuiScaledHeight()-29; // B541_HOTBAR_BOTTOM",
        "int y=mc.getWindow().getGuiScaledHeight()-14; // B552_HUD_FE_LOWER")
replace(hud,"int py=mc.getWindow().getGuiScaledHeight()-47; // B541_TIGHT_HUD_ROWS",
        "int py=mc.getWindow().getGuiScaledHeight()-28; // B552_HUD_PASTE_LOWER")
replace(hud,"final int width=80;","final int width=60; // B552_HUD_SMALL_FE_BAR")
replace(hud,"int pasteWidth=80,px=Math.max(3,mc.getWindow().getGuiScaledWidth()/2-91-88);",
        "int pasteWidth=60,px=Math.max(3,mc.getWindow().getGuiScaledWidth()/2-91-88);")
replace(hud,'g.text(mc.font,"ARMOR FE",x+2,y-1,col);',
'''// B552_HALF_SIZE_FE_TEXT: correct Matrix3x2fStack API for MC 26.1.
   g.pose().pushMatrix();
   g.pose().translate(x+2f,y-1f);
   g.pose().scale(.5f,.5f);
   g.text(mc.font,"ARMOR FE",0,0,col);
   g.pose().popMatrix();''')
replace(hud,'g.text(mc.font,percent,x+width-percentWidth-1,y-1,col);',
'''g.pose().pushMatrix();
   g.pose().translate(x+width-percentWidth*.5f-1f,y-1f);
   g.pose().scale(.5f,.5f);
   g.text(mc.font,percent,0,0,col);
   g.pose().popMatrix();''')
replace(hud,'g.text(mc.font,pasteLabel,px,py,pasteColor);',
'''// B552_HALF_SIZE_PASTE_TEXT: halve glyph size without scaling percent.
   g.pose().pushMatrix();
   g.pose().translate((float)px,(float)py);
   g.pose().scale(.5f,.5f);
   g.text(mc.font,pasteLabel,0,0,pasteColor);
   g.pose().popMatrix();''')

# B552 collar: B533 used be.getBlockState() to get the correct cable color,
# but the ENERGY CABLE MODEL IS NOT A FULL CUBE. Scaling a thin cable mesh
# again makes the supposed input bulge disappear. Resolve a dedicated solid
# full-cube render-only blockstate, textured in the actual energy cable palette.
registry="ObsidianNetwork.java"
reg_marker="    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock."
registry_source=(J/registry).read_text(encoding="utf-8")
assert registry_source.count(reg_marker)==1,"B552_COLLAR_REGISTRY_ANCHOR"
assert "XSX_ENERGY_INPUT_COLLAR" not in registry_source
registration='''    // B552_RENDER_ONLY_ENERGY_INPUT_COLLAR: one simple state, no item, no ticker.
    // The real energy cable retains exactly its old number of BlockStates.
    public static final DeferredBlock<net.minecraft.world.level.block.Block> XSX_ENERGY_INPUT_COLLAR =
        BLOCKS.registerBlock("xsx_energy_input_collar",
            net.minecraft.world.level.block.Block::new,
            p -> p.mapColor(MapColor.METAL).strength(0.1F).noLootTable());
'''
(J/registry).write_text(registry_source.replace(reg_marker,registration+reg_marker,1),encoding="utf-8")

renderer="client/EnergyCableInputRenderer.java"
replace(renderer,
 "resolver.update(out.cap,be.getBlockState(),DISPLAY); // B533_ACTUAL_ENERGY_CABLE_CAP_TEXTURE",
 """resolver.update(out.cap,dev.obsidiannetwork.ObsidianNetwork.XSX_ENERGY_INPUT_COLLAR.get().defaultBlockState(),DISPLAY); // B552_SOLID_CABLE_COLORED_INPUT_COLLAR B533_ACTUAL_ENERGY_CABLE_CAP_TEXTURE""")
# 10/16 across, 3/16 protrusion on every face: same visible thick
# socket semantics as item cables. Input data and fade/facade behavior stay.
for old,new in (
 ("6/16f,0,6/16f,4/16f,2/16f,4/16f","3/16f,0,3/16f,10/16f,3/16f,10/16f"),
 ("6/16f,14/16f,6/16f,4/16f,2/16f,4/16f","3/16f,13/16f,3/16f,10/16f,3/16f,10/16f"),
 ("6/16f,6/16f,0,4/16f,4/16f,2/16f","3/16f,3/16f,0,10/16f,10/16f,3/16f"),
 ("6/16f,6/16f,14/16f,4/16f,4/16f,2/16f","3/16f,3/16f,13/16f,10/16f,10/16f,3/16f"),
 ("0,6/16f,6/16f,2/16f,4/16f,4/16f","0,3/16f,3/16f,3/16f,10/16f,10/16f"),
 ("14/16f,6/16f,6/16f,2/16f,4/16f,4/16f","13/16f,3/16f,3/16f,3/16f,10/16f,10/16f")
):
 replace(renderer,old,new)

# Find the ACTUAL cable texture already in the reconstructed resources.
# Prefer the cable model's own texture entries, without assuming a named
# path, and reject missing assets rather than ship a checkerboard socket.
texture_names=[]
model_dir=A/"models/block"
for file in sorted(model_dir.glob("*energy*cable*.json")):
 model=json.loads(file.read_text(encoding="utf-8"))
 for value in model.get("textures",{}).values():
  if isinstance(value,str) and value.startswith("obsidiannetwork:block/"):
   texture_names.append(value.split(":",1)[1].removeprefix("block/"))
for file in sorted((A/"textures/block").glob("*energy*cable*.png")):
 texture_names.append(file.stem)
for file in sorted((A/"textures/block").glob("*cable*energy*.png")):
 texture_names.append(file.stem)
choices=[]
for name in dict.fromkeys(texture_names):
 file=A/"textures/block"/(name+".png")
 if file.is_file():
  score=(10 if "energy_cable" in name else 0)+(4 if any(k in name for k in ("side","core","body")) else 0)
  score-=8 if any(k in name for k in ("input","output","overlay","facade")) else 0
  choices.append((score,name,file))
assert choices,("B552_NO_REAL_ENERGY_CABLE_PALETTE",texture_names[:20])
_,source_name,source_png=max(choices,key=lambda x:(x[0],-len(x[1])))
from PIL import Image
im=Image.open(source_png).convert("RGBA")
pallet=[(r,g,b) for r,g,b,a in im.getdata() if a>=110]
assert pallet,("B552_EMPTY_ENERGY_CABLE_TEXTURE",source_name)
# Dominant visible color keeps the socket consistent with the cable family.
# 5-bit buckets ignore minor antialias/highlight noise without inventing hue.
bucket=Counter((r//8,g//8,b//8) for r,g,b in pallet)
b= bucket.most_common(1)[0][0]
base=tuple(min(255,k*8+4) for k in b)
def tint(k):
 return tuple(max(0,min(255,round(c*k))) for c in base)+(255,)
dark=tint(.53); mid=tint(.83); face=tint(1.04); shine=tint(1.28)
def socket(x,y):
 if x in (0,15) or y in (0,15):return dark
 if x in (1,14) or y in (1,14):return mid
 if (x in (3,12) and 3<=y<=12) or (y in (3,12) and 3<=x<=12):return shine
 if 4<=x<=11 and 4<=y<=11:return face
 return mid
def png(path,w,h,pixel):
 raw=bytearray()
 for y in range(h):
  raw.append(0)
  for x in range(w):raw.extend(pixel(x,y))
 def chunk(t,content):
  return len(content).to_bytes(4,"big")+t+content+(zlib.crc32(t+content)&0xffffffff).to_bytes(4,"big")
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
                   +chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b""))
png(A/"textures/block/xsx_energy_input_collar.png",16,16,socket)
(A/"models/block/xsx_energy_input_collar.json").write_text(json.dumps({
 "parent":"minecraft:block/cube_all",
 "textures":{"all":"obsidiannetwork:block/xsx_energy_input_collar"}},indent=2)+"\n",encoding="utf-8")
(A/"blockstates/xsx_energy_input_collar.json").write_text(json.dumps({
 "variants":{"":{"model":"obsidiannetwork:block/xsx_energy_input_collar"}}},indent=2)+"\n",encoding="utf-8")

# B552 joined reactor: uniform pale ceramic tile borders. Thin graphite
# horizontal channels extend all the way to neighboring tile edges;
# NO dark square frame surrounding each individual casing when assembled.
def reactor_face(x,y):
 if y in (11,12):
  c=(154,167,179,255) if y==11 else (92,110,122,255)
 elif y in (13,14):
  c=(225,233,239,255) if y==13 else (245,249,252,255)
 else:
  grain=((x*7+y*3)%5)-2
  c=(237+grain,243+grain,248+grain,255)
 if 12<=x<=19 and 20<=y<=22:
  c=(200,214,221,255)
 if 14<=x<=17 and y==21:c=(95,115,124,255)
 return c
def reactor_top(x,y):
 v=((x*7+y*5)%5)-2
 return (236+v,243+v,248+v,255)

# B552 joined charged bank: continuous rather than per-block cyan square
# borders. White cells read as one large machine; one fine cyan horizontal
# rail runs through adjacent tiles, with tiny technical indicators.
def bank_face(x,y,lit):
 grain=((x*3+y*11)%5)-2
 c=(239+grain,246+grain,251+grain,255)
 if y==12:
  c=(56,102,120,255)
 if y in (13,14):
  c=(85,235,251,255) if lit else (103,173,191,255)
 if y==15:
  c=(214,232,240,255)
 if 14<=x<=17 and 23<=y<=25:
  c=(94,220,241,255) if lit else (138,185,199,255)
 return c
def bank_top(x,y,lit):
 v=((x*3+y*7)%5)-2
 return (237+v,245+v,251+v,255)

for name,pixel in (
 ("reactor_casing_formed",reactor_face),
 ("reactor_casing_formed_top",reactor_top),
 ("powerbank_casing_formed",lambda x,y:bank_face(x,y,False)),
 ("powerbank_casing_formed_top",lambda x,y:bank_top(x,y,False)),
 ("powerbank_casing_formed_lit",lambda x,y:bank_face(x,y,True)),
 ("powerbank_casing_formed_lit_top",lambda x,y:bank_top(x,y,True)),
):
 png(A/"textures/block"/(name+".png"),32,32,pixel)
# Runtime state mapping is unmodified: only fully assembled casings use
# these faces. Unformed structures keep their recognizable standalone skins.
for n in ("reactor_casing","powerbank_casing"):
 variants=json.loads((A/"blockstates"/(n+".json")).read_text(encoding="utf-8"))["variants"]
 assert len(variants)==8 and all(("formed=true" in k)==("_formed" in v["model"]) for k,v in variants.items()),("B552_FORMED_VARIANTS",n)
print("B552_CLIENT_HUD_HALF_TEXT_LOWER_INPUT_SOLID_CABLE_COLLAR_JOINED_MULTIBLOCKS_PASS",source_name,base)
