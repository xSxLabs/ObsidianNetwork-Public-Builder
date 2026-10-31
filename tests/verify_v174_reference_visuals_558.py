#!/usr/bin/env python3
"""Verify the actual generated resources or packaged release JAR.

B558 hard acceptance: reactor #3 has THREE independent industrial panel
modules in each assembled rail; bank #4 cyan strips are continuous,
charged rails are brighter, corner-posts are distinct, transparent tinted
glass and simulated cyan core reflections are packaged. No old-style
single block frame models used for formed casings.
"""
import argparse,io,json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

BASE="assets/obsidiannetwork/"

def verify(read):
 def sprite(name):
  return Image.open(io.BytesIO(read(BASE+"textures/block/"+name+".png"))).convert("RGBA")
 def variants(name):
  return json.loads(read(BASE+"blockstates/"+name+".json"))["variants"]
 for name in ("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass"):
  states=variants(name)
  assert len(states)==144,(name,len(states))
  assert all("rim=" in k and "corner=" in k and "detail=" in k for k in states)
  for key,value in states.items():
   if "formed=false" in key:
    assert value["model"]=="obsidiannetwork:block/"+name,(name,key,value)
   if "formed=true" in key and name=="reactor_casing":
    assert "design3" in value["model"] and "_detail" in value["model"]
   if "formed=true" in key and name=="powerbank_casing":
    assert "design4" in value["model"]
   if "formed=true" in key and name=="powerbank_glass" and "lit=true" in key:
    assert "glass_formed_lit_detail" in value["model"]
 for n in ("reactor_casing_formed_design3_top_detail0",
           "reactor_casing_formed_design3_top_detail1",
           "reactor_casing_formed_design3_top_detail2",
           "reactor_casing_formed_design3_top_corner_detail0",
           "reactor_casing_formed_design3_middle_corner_detail0",
           "powerbank_casing_formed_design4_top_lit",
           "powerbank_casing_formed_design4_bottom_lit",
           "powerbank_casing_formed_design4_top_corner_lit",
           "powerbank_casing_formed_design4_middle_corner_lit",
           "powerbank_glass_formed_lit_detail1"):
  assert len(read(BASE+"textures/block/"+n+".png"))>180,n
  if "glass" not in n:
   model=json.loads(read(BASE+"models/block/"+n+".json"))
   assert model["parent"]=="minecraft:block/cube",n
 # User reference #3: 3 distinct technical motifs, dark grilles vs white.
 t=[sprite(f"reactor_casing_formed_design3_top_detail{i}") for i in range(3)]
 assert len({a.tobytes() for a in t})==3,"Reactors have no mixed industry panels"
 assert min(t[0].getpixel((7,y))[0] for y in (12,13,14,15))<120
 assert t[2].getpixel((8,5))[0]>215,"Reactor should retain white ceramic"
 # User reference #4: lit horizontal teal lines; correctly darker offline.
 on=sprite("powerbank_casing_formed_design4_top_lit")
 off=sprite("powerbank_casing_formed_design4_top")
 bottom=sprite("powerbank_casing_formed_design4_bottom_lit")
 assert on.getpixel((16,26))[1]>=230 and on.getpixel((16,26))[2]>=245
 assert off.getpixel((16,26))[1]<190
 assert bottom.getpixel((16,4))[1]>=230,"Missing lit bottom rail"
 assert on.getpixel((16,10))[0]>=220,"Bank beam is not white"
 # The corner post must be different from its straight beam and body.
 corner=sprite("powerbank_casing_formed_design4_top_corner_lit")
 middle=sprite("powerbank_casing_formed_design4_middle_corner_lit")
 assert corner.getpixel((16,26))[0]<120,"Bank rail no longer locks into graphite corner"
 assert corner.getpixel((5,26))[1]>230,"Cyan rail does not enter top corner"
 assert corner.getpixel((16,15))[0]>210,"White corner pillar replaced by black screen"
 assert middle.getpixel((3,15))[1]>190,"Vertical corner LED missing"
 assert corner.tobytes()!=on.tobytes()
 # B559 reactor operating glass has true blue equipment glow, still transparent.
 assert "obsidiannetwork:block/reactor_glass_formed_lit" in {
  v["model"] for k,v in variants("reactor_glass").items()
  if "formed=true" in k and "lit=true" in k}
 assert json.loads(read(BASE+"models/block/reactor_glass_formed_lit.json"))["parent"]=="minecraft:block/cube_all"
 glow=sprite("reactor_glass_formed_lit")
 assert glow.getpixel((16,15))[2]>210 and glow.getpixel((16,15))[3]<180
 # Glass is physical translucent tinted glazing, not empty alpha 9.
 glass1=sprite("reactor_glass_formed")
 glass2=sprite("powerbank_glass_formed")
 core=sprite("powerbank_glass_formed_lit_detail1")
 assert 20<=glass1.getpixel((12,12))[3]<=120
 assert 20<=glass2.getpixel((12,12))[3]<=120
 assert core.getpixel((10,14))[1]>200,"Charged internal turquoise reflection absent"
 assert core.getpixel((10,14))[3]<255,"Interior reflection must stay transparent"
 print("B558_PACKAGED_REFERENCE_REACTOR3_BANK4_VISUAL_MATERIALS_PASS")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--jar",type=Path)
 p.add_argument("--assets",type=Path)
 args=p.parse_args()
 assert bool(args.jar)!=bool(args.assets),"Select exactly one source"
 if args.jar:
  assert args.jar.is_file()
  with ZipFile(args.jar) as z:verify(z.read)
 else:
  root=args.assets.parent.parent
  assert args.assets.name=="obsidiannetwork"
  verify(lambda p:(root/p).read_bytes())
