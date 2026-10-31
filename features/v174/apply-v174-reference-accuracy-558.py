#!/usr/bin/env python3
"""B558: user-confirmed target skins: Reactor option 3 (industrial panels),
Powerbank option 4 (cyan light-lines). Run AFTER B553 and BEFORE build gates.

A full per-JAR look is baked from 32x32 material sprites and native models.
Only assembled states use the replacements; the standalone block models,
FE logic, networks, throughput, and existing renderer cadence remain untouched.
Detail selection happens once during the existing assembly skin pass.
"""
import json,os,struct,zlib
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def change(rel,old,new):
 p=J/rel
 t=p.read_text(encoding="utf8")
 assert t.count(old)==1,("B558_SOURCE_DRIFT",rel,old[:100],t.count(old))
 p.write_text(t.replace(old,new,1),encoding="utf8")

# Multiple industrial service modules are required by reactor reference #3.
# A real 3-state block property creates variety across the upper/lower
# shell without any per-frame renderer or neighbor scans.
change("multiblock/MultiblockSkinBlock.java",
 "IntegerProperty.create(\"rim\",0,2);",
 '''IntegerProperty.create("rim",0,2);
 public static final net.minecraft.world.level.block.state.properties.IntegerProperty DETAIL=
  net.minecraft.world.level.block.state.properties.IntegerProperty.create("detail",0,2); // B558_REACTOR_MIXED_PANELS''')
change("multiblock/MultiblockSkinBlock.java",
 ".setValue(RIM,0).setValue(CORNER,false));",
 ".setValue(RIM,0).setValue(CORNER,false).setValue(DETAIL,0));")
change("multiblock/MultiblockSkinBlock.java",
 "builder.add(FORMED,ACTIVE,LIT,RIM,CORNER);",
 "builder.add(FORMED,ACTIVE,LIT,RIM,CORNER,DETAIL);")
change("multiblock/MultiblockSkinBlock.java",
 "boolean corner=(p.getX()==minX||p.getX()==maxX)\n       &&(p.getZ()==minZ||p.getZ()==maxZ);",
 '''boolean corner=(p.getX()==minX||p.getX()==maxX)
       &&(p.getZ()==minZ||p.getZ()==maxZ);
   // B558_ONLY_ON_ASSEMBLY: vary vents, controls and blank ceramic
   // on the reactor perimeter; keep charged powerbank bands continuous.
   int detail=bank?0:Math.floorMod(p.getX()*11+p.getZ()*7,3);''')
change("multiblock/MultiblockSkinBlock.java",
 "if(state.getValue(RIM)!=band||state.getValue(CORNER)!=corner)\n    sl.setBlock(p,state.setValue(RIM,band).setValue(CORNER,corner),3);",
 """if(state.getValue(RIM)!=band||state.getValue(CORNER)!=corner||state.getValue(DETAIL)!=detail)
    sl.setBlock(p,state.setValue(RIM,band).setValue(CORNER,corner).setValue(DETAIL,detail),3);""")

# Strictly no alteration of multiblock geometry, inventory, energy routing,
# controller validation or existing FE/t and charge-driven LIT changes.
def rgba(rgb,alpha=255):return tuple(rgb)+(alpha,)
def col(n):return max(0,min(255,int(n)))
W=(238,244,249);HI=(251,253,255);SEAM=(211,222,231)
STEEL=(126,149,165);GRAPHITE=(32,48,64);SHADOW=(65,88,106)
CYAN=(66,239,255);CYANHI=(168,255,255);DIM=(83,148,172)

def neutral(x,y):
 d=(x*11+y*7+x*y)%3-1
 c=tuple(col(v+d) for v in W)
 if x==31:c=(221,230,236)
 if y==31:c=(222,230,236)
 if y in (0,1):c=(248,251,253)
 return rgba(c)
def groove(x,y):
 c=neutral(x,y)
 if x in (2,29):c=rgba((217,226,231))
 if (x,y) in ((5,5),(26,5),(5,26),(26,26)):c=rgba((178,194,204))
 return c

def bolt(x,y):
 return (x,y) in ((4,7),(27,7),(4,24),(27,24))

def grill_cell(x,y,x0,x1,y0,y1):
 if not (x0<=x<=x1 and y0<=y<=y1):return None
 if x in (x0,x1) or y in (y0,y1):return rgba(STEEL)
 if x in (x0+1,x1-1) or y in (y0+1,y1-1):return rgba((75,95,110))
 if (y-y0)%4==0:return rgba((160,174,181))
 if (y-y0)%4==1:return rgba((38,51,64))
 return rgba((22,37,49))

def reactor_panel(x,y,band,detail):
 c=neutral(x,y)
 # Uninterrupted ceramic lower rail and upper mechanical edge.
 if band==2 and y in (0,1):c=rgba((203,215,224))
 if band==1 and y in (30,31):c=rgba((194,208,217))
 if band==0:
  # Tall smooth white structural column, not a standalone bordered block.
  if x in (0,31):c=rgba((220,230,236))
  if x in (2,29):c=rgba((248,251,254))
  return c
 if detail==0: # Multiple vertical exhaust grills as in reference #3.
  for bounds in ((3,14,8,23),(18,29,8,23)):
   g=grill_cell(x,y,*bounds)
   if g is not None:c=g
 elif detail==1: # Diagnostics, digital control face, access and fasteners.
  g=grill_cell(x,y,3,14,9,22)
  if g is not None:c=g
  if 18<=x<=29 and 10<=y<=21:
   c=rgba((122,146,161)) if x in (18,29) or y in (10,21) else rgba((49,67,82))
   if 20<=x<=26 and y in (13,16):c=rgba((101,231,230))
   if x in (20,23,26) and y==18:c=rgba((197,219,221))
 else: # Industrial white service panel with compact extractor.
  if 4<=x<=28 and y in (8,23):c=rgba((205,216,225))
  if x in (4,28) and 8<=y<=23:c=rgba((227,234,241))
  g=grill_cell(x,y,20,28,11,20)
  if g is not None:c=g
  if (x,y) in ((7,11),(15,11),(7,20),(15,20)):c=rgba((86,102,120))
  if 7<=x<=15 and 14<=y<=16:c=rgba((158,175,187))
 if bolt(x,y):c=rgba((82,102,119))
 return c

def reactor_corner(x,y,band):
 c=groove(x,y)
 if band in (1,2):
  # Heavy technical collar only at corner nodes, not every side tile.
  if x in (0,1,30,31):c=rgba((110,128,145))
  if 5<=x<=26 and 6<=y<=25:
   g=grill_cell(x,y,5,26,6,25)
   if g is not None:c=g
  if (x,y) in ((3,3),(28,3),(3,28),(28,28)):c=rgba((57,76,90))
 else:
  # Smooth continuous white corner pillar, no rectangular gadget stamped
  # on every height segment. Reference #3 keeps the middle columns clean.
  if x in (3,28):c=rgba((222,230,237))
  if x in (4,27):c=rgba((250,252,254))
 return c

def bank_panel(x,y,band,lit):
 c=neutral(x,y)
 if band==2:
  # Top reference: thick *white* top beam, single thin glowing stripe
  # near its lower edge, protected by graphite channel.
  if y in (21,22):c=rgba((191,206,215))
  if y in (23,30):c=rgba((55,76,92))
  if y in (24,29):c=rgba((106,136,153))
  if 25<=y<=28:
   if lit:c=rgba(CYANHI if y in (26,27) else CYAN)
   else:c=rgba(DIM)
 elif band==1:
  # Bottom reference: matching rail *above* lower white plinth.
  if y in (1,8):c=rgba((55,76,92))
  if y in (2,7):c=rgba((106,136,153))
  if 3<=y<=6:
   if lit:c=rgba(CYANHI if y in (4,5) else CYAN)
   else:c=rgba(DIM)
  if y in (9,10):c=rgba((199,212,221))
 return c

def bank_corner(x,y,band,lit):
 c=groove(x,y)
 if band==0:
  # Reference #4 has a smooth WHITE pillar with two very thin running
  # cyan edges; dark metal appears at its top and base, not full height.
  if x in (1,30):c=rgba((179,194,206))
  if x in (3,28):c=rgba(CYAN if lit else DIM)
  if x in (4,27):c=rgba((227,237,243))
 else:
  # Metallic bridge / 90-degree corner fitting, NOT a full black screen.
  # The LED strips enter the corner from both sides at the SAME Y as
  # the straight upper and lower rails; short cyan stubs wrap around it.
  y0=25 if band==2 else 3
  if y in (y0-2,y0+4):c=rgba((128,146,159))
  if y in (y0-1,y0+3):c=rgba((59,84,100))
  if y0<=y<=y0+2:
   if x<=9 or x>=22:
    c=rgba(CYANHI if lit and y==y0+1 else CYAN if lit else DIM)
   else:
    c=rgba((42,64,82))
  # A narrow graphite square frames the white structural joint.
  if x in (10,21) and y0-4<=y<=y0+5:c=rgba((92,114,131))
  if 11<=x<=20 and y0-4<=y<=y0-2:c=rgba((70,92,107))
  if 11<=x<=20 and y0+3<=y<=y0+5:c=rgba((70,92,107))
  # Steel screws anchor the corner assembly without covering the beam.
  if (x,y) in ((7,y0-3),(24,y0-3),(7,y0+4),(24,y0+4)):
   c=rgba((181,196,207))
 return c

def glass(x,y,bank,lit=False,detail=0):
 # Multiblock glass is a framed smoky window (not an invisible hole).
 # Alpha remains < 255 so the true world behind the glass stays visible.
 grain=(x*7+y*13)%7-3
 if x in (0,31) or y in (0,31):return (22,37,50,187)
 if x in (1,30) or y in (1,30):return (52,73,91,142)
 if x in (2,29) or y in (2,29):return (105,139,160,81)
 c=(40+grain,67+grain,84+grain,39 if not lit else 49)
 if not bank and lit and 11<=x<=20 and 8<=y<=25:
  # Operated reactor: soft electric-blue machinery light behind dark
  # glass. This does not paint glowing strips on the white reactor shell.
  return (52,169,234,88 if x in (12,19) else 114)
 if bank and lit and detail in (1,2):
  # A translucent cyan vertical *core hint* seen through each lit pane.
  # This is a CLIENT material effect, not a fictitious energy container.
  x0=8 if detail==1 else 18
  if x0<=x<=x0+6 and 3<=y<=28:
   if x==x0 or x==x0+6:return (26,116,153,105)
   if x in (x0+2,x0+3) and 7<=y<=25:return (126,252,255,153)
   return (38,173,207,92)
 if bank and lit and x in (15,16):
  return (72,221,237,66)
 return c

def png(name,pixel):
 p=A/"textures/block"/(name+".png")
 p.parent.mkdir(parents=True,exist_ok=True)
 raw=bytearray()
 for y in range(32):
  raw.append(0)
  for x in range(32):
   value=pixel(x,y)
   assert len(value)==4 and all(0<=v<=255 for v in value),(name,x,y,value)
   raw.extend(value)
 def ck(typ,payload):
  return struct.pack(">I",len(payload))+typ+payload+struct.pack(">I",zlib.crc32(typ+payload)&0xffffffff)
 p.write_bytes(b"\x89PNG\r\n\x1a\n"+ck(b"IHDR",struct.pack(">IIBBBBB",32,32,8,6,0,0,0))
   +ck(b"IDAT",zlib.compress(bytes(raw),9))+ck(b"IEND",b""))
 assert p.stat().st_size>150,(name,p.stat().st_size)

def cube(name,side,top):
 p=A/"models/block"/(name+".json")
 assert p.parent.is_dir()
 m={"parent":"minecraft:block/cube","textures":{"particle":"obsidiannetwork:block/"+side,
  "up":"obsidiannetwork:block/"+top,"down":"obsidiannetwork:block/"+top,
  **{f:"obsidiannetwork:block/"+side for f in ("north","south","east","west")}}}
 p.write_text(json.dumps(m,indent=2)+"\n",encoding="utf8")

# Material colors at both horizontal and vertical faces, not an invented
# checkerboard where 20 neighbouring tiles all receive their own border.
for band,tag in ((0,"middle"),(1,"bottom"),(2,"top")):
 for corner in (False,True):
  for detail in range(3):
   name=f"reactor_casing_formed_design3_{tag}"+("_corner" if corner else "")+f"_detail{detail}"
   png(name,(lambda x,y,b=band,c=corner,d=detail:
     reactor_corner(x,y,b) if c else reactor_panel(x,y,b,d)))
   cube(name,name,"reactor_casing_formed_top")
 for lit in (False,True):
  suffix="_lit" if lit else ""
  for corner in (False,True):
   name=f"powerbank_casing_formed_design4_{tag}"+("_corner" if corner else "")+suffix
   png(name,lambda x,y,b=band,corner=corner,lit=lit:
     bank_corner(x,y,b,lit) if corner else bank_panel(x,y,b,lit))
   # B553 already registered the model; its faces remain white with top
   # and bottom rails on the sides, not all six faces.
   assert (A/"models/block"/(name+".json")).is_file(),name

# Roofs stay neutral white, never dark grilles repeated in all directions.
for nm in ("reactor_casing_formed_top","powerbank_casing_formed_top",
           "powerbank_casing_formed_lit_top"):
 png(nm,lambda x,y:neutral(x,y) if x not in (0,31) and y not in (0,31) else rgba((207,221,230)))

png("reactor_glass_formed",lambda x,y:glass(x,y,False))
png("reactor_glass_formed_lit",lambda x,y:glass(x,y,False,True))
# B559_REACTOR_LIT_GLASS: use the already-supported translucent cube_all
# model format, and the existing LIT BlockState (no new runtime ticker).
(A/"models/block/reactor_glass_formed_lit.json").write_text(json.dumps({
 "parent":"minecraft:block/cube_all","textures":{"all":{
 "sprite":"obsidiannetwork:block/reactor_glass_formed_lit",
 "force_translucent":True}}},indent=2)+"\n",encoding="utf8")
png("powerbank_glass_formed",lambda x,y:glass(x,y,True,False))
for detail in range(3):
 png("powerbank_glass_formed_lit_detail"+str(detail),
     lambda x,y,d=detail:glass(x,y,True,True,d))
 top="powerbank_glass_formed"
 name="powerbank_glass_formed_lit_detail"+str(detail)
 m={"parent":"minecraft:block/cube","textures":{
  "particle":{"sprite":"obsidiannetwork:block/"+name,"force_translucent":True},
  "up":{"sprite":"obsidiannetwork:block/"+top,"force_translucent":True},
  "down":{"sprite":"obsidiannetwork:block/"+top,"force_translucent":True},
  **{face:{"sprite":"obsidiannetwork:block/"+name,"force_translucent":True}
     for face in ("north","south","east","west")}}}
 (A/"models/block"/(name+".json")).write_text(json.dumps(m,indent=2)+"\n",encoding="utf8")

# 48 original formed/active/lit/rim/corner variants => 144 with detail.
# For unassembled blocks and the false/true combinations: same base models.
for block in ("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass"):
 p=A/"blockstates"/(block+".json")
 data=json.loads(p.read_text(encoding="utf8"))
 assert len(data["variants"])==48,("B558_EXPECT_48_B553_VARIANTS",block)
 new={}
 for key,value in data["variants"].items():
  for detail in range(3):
   formed="formed=true" in key
   model=value["model"]
   if formed and block=="reactor_casing":
    model=model+"_detail"+str(detail)
   elif formed and block=="reactor_glass" and "lit=true" in key:
    model="obsidiannetwork:block/reactor_glass_formed_lit"
   elif formed and block=="powerbank_glass" and "lit=true" in key:
    model="obsidiannetwork:block/powerbank_glass_formed_lit_detail"+str(detail)
   new[key+",detail="+str(detail)]={"model":model}
 assert len(new)==144,(block,len(new))
 p.write_text(json.dumps({"variants":new},indent=2)+"\n",encoding="utf8")
 for key,v in new.items():
  if "formed=false" in key:
   assert v["model"].endswith(block),("B558_UNASSEMBLED_SKIN_CHANGED",key,v)
  if block=="reactor_casing" and "formed=true" in key:
   assert "design3" in v["model"] and "_detail" in v["model"]
  if block=="powerbank_casing" and "formed=true" in key:
   assert "design4" in v["model"]
  if block=="reactor_glass" and "formed=true" in key and "lit=true" in key:
   assert v["model"].endswith("reactor_glass_formed_lit")
  if block=="powerbank_glass" and "formed=true" in key and "lit=true" in key:
   assert "glass_formed_lit_detail" in v["model"]
print("B558_EXACT_REFERENCE_FAMILIES_REACTOR_3_POWERBANK_4_FORMED_MATERIALS_PASS")
