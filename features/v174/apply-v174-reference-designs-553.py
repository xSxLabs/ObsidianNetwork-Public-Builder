#!/usr/bin/env python3
"""B553 exact user-chosen design families: reactor #3 Industrie Panels;
powerbank #4 Leucht Linien. The assembled shell receives Y-band-aware
prebaked models, with no BER and no periodic visual scan.

B552 already creates the shared white/cyan base; B553 decorates ONLY
formed casing faces and leaves unformed blocks/FE/t/capabilities untouched.
"""
import json,os,struct,zlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
skin=J/"multiblock/MultiblockSkinBlock.java"
src=skin.read_text(encoding="utf-8")
def once(s,old,new):
 assert s.count(old)==1,("B553_SOURCE_CHANGED",old[:100],s.count(old))
 return s.replace(old,new,1)

src=once(src,
 'public static final BooleanProperty LIT=BooleanProperty.create("lit");',
 '''public static final BooleanProperty LIT=BooleanProperty.create("lit");
 // B553_ASSEMBLED_RIM: 0=mid/neutral, 1=bottom, 2=top.
 // Only assigned once on forming, never recalculated every frame/tick.
 public static final BooleanProperty CORNER=BooleanProperty.create("corner");
 public static final net.minecraft.world.level.block.state.properties.IntegerProperty RIM=
    net.minecraft.world.level.block.state.properties.IntegerProperty.create("rim",0,2);''')
src=once(src,
 'registerDefaultState(defaultBlockState().setValue(FORMED,false).setValue(ACTIVE,false).setValue(LIT,false));',
 'registerDefaultState(defaultBlockState().setValue(FORMED,false).setValue(ACTIVE,false).setValue(LIT,false).setValue(RIM,0).setValue(CORNER,false));')
src=once(src,'builder.add(FORMED,ACTIVE,LIT);','builder.add(FORMED,ACTIVE,LIT,RIM,CORNER);')
# The cyan strips on the charged powerbank casing must actually switch from
# standby to active. Previously B530 illuminated only the GLASS block; that
# meant the B533 charged casing texture could NEVER display in gameplay.
# B535 already lights charged powerbank CASINGS. Do not overwrite it.
assert 'if((glass||(bank&&state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_CASING.get())))&&state.getValue(LIT)!=lit)' in src, "B555_BANK_LIT_STATE_MISSING"

anchor=' @Override protected MapCodec<? extends Block> codec()'
method=r''' // B553_ON_FORM_VISUAL_BANDS: one bounded scan per successful assembly.
 // Formed blocks are already valid before this runs. No chunk tickets and
 // no new ticker. Only a state property is updated; rendering stays vanilla.
 public static void applyAssemblyBands(net.minecraft.server.level.ServerLevel sl,
     net.minecraft.core.BlockPos controller,boolean bank){
  java.util.ArrayDeque<net.minecraft.core.BlockPos> queue=new java.util.ArrayDeque<>();
  java.util.HashSet<Long> visited=new java.util.HashSet<>();
  java.util.ArrayList<net.minecraft.core.BlockPos> skinPositions=new java.util.ArrayList<>();
  queue.add(controller);
  int low=Integer.MAX_VALUE,high=Integer.MIN_VALUE;
  int minX=Integer.MAX_VALUE,maxX=Integer.MIN_VALUE;
  int minZ=Integer.MAX_VALUE,maxZ=Integer.MIN_VALUE;
  final int radius=bank?12:64,limit=bank?1200:90000;
  while(!queue.isEmpty()&&visited.size()<limit){
   var p=queue.removeFirst();
   if(!visited.add(p.asLong())||!sl.hasChunkAt(p))continue;
   var state=sl.getBlockState(p);
   boolean shell=bank
    ?state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_CASING.get())
      ||state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_GLASS.get())
      ||state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_CONTROLLER.get())
      ||state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_INPUT.get())
      ||state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_OUTPUT.get())
    :dev.obsidiannetwork.reactor.ReactorStructure.shell(state);
   if(!shell)continue;
   if(state.getBlock() instanceof MultiblockSkinBlock&&state.getValue(FORMED)){
    skinPositions.add(p);
   }
   low=Math.min(low,p.getY());high=Math.max(high,p.getY());
   minX=Math.min(minX,p.getX());maxX=Math.max(maxX,p.getX());
   minZ=Math.min(minZ,p.getZ());maxZ=Math.max(maxZ,p.getZ());
   for(var d:net.minecraft.core.Direction.values()){
    var next=p.relative(d);
    if(!visited.contains(next.asLong())
      &&Math.abs(next.getX()-controller.getX())<=radius
      &&Math.abs(next.getY()-controller.getY())<=radius
      &&Math.abs(next.getZ()-controller.getZ())<=radius)queue.add(next);
   }
  }
  // Fail closed on truncated traversal. Do not decorate partial multiblocks.
  if(!queue.isEmpty()||high<=low)return;
  for(var p:skinPositions){
   var state=sl.getBlockState(p);
   if(!(state.getBlock() instanceof MultiblockSkinBlock)
      ||!state.getValue(FORMED))continue;
   int band=p.getY()==low?1:p.getY()==high?2:0;
   // Corner pillars stay white: the dark vents belong on the beams.
   boolean corner=(p.getX()==minX||p.getX()==maxX)
       &&(p.getZ()==minZ||p.getZ()==maxZ);
   if(state.getValue(RIM)!=band||state.getValue(CORNER)!=corner)
    sl.setBlock(p,state.setValue(RIM,band).setValue(CORNER,corner),3);
  }
 }
'''
src=once(src,anchor,method+anchor)
skin.write_text(src,encoding="utf-8")
# Hook after existing B485 formed appearance transition, not on runtime tick.
for file,old,new in (
 ("reactor/ReactorControllerBlockEntity.java",
  "skin(sl,worldPosition,formed,true,64,64,64);",
  """skin(sl,worldPosition,formed,true,64,64,64);
    if(formed)dev.obsidiannetwork.multiblock.MultiblockSkinBlock.applyAssemblyBands(
       sl,worldPosition,false); // B553_REACTOR_DESIGN_3"""),
 ("powerbank/PowerbankBlockEntity.java",
  "skin(sl,worldPosition,formed);",
  """skin(sl,worldPosition,formed);
    if(formed)dev.obsidiannetwork.multiblock.MultiblockSkinBlock.applyAssemblyBands(
       sl,worldPosition,true); // B553_POWERBANK_DESIGN_4"""),
):
 p=J/file
 p.write_text(once(p.read_text(encoding="utf-8"),old,new),encoding="utf-8")

# Four combinations: top/bottom/middle; bank charged/unpowered. White
# industrial hard-surface palettes copy the image's material hierarchy:
# white ceramic walls; dark charcoal inset vents in REACTOR top/base;
# flat white BANK walls and continuous cyan top/base LED edge strips.
def texture(file,pixel):
 p=A/"textures/block"/(file+".png")
 raw=bytearray()
 for y in range(32):
  raw.append(0)
  for x in range(32):raw.extend(pixel(x,y))
 def chunk(name,data):
  return struct.pack(">I",len(data))+name+data+struct.pack(">I",zlib.crc32(name+data)&0xffffffff)
 p.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",32,32,8,6,0,0,0))
  +chunk(b"IDAT",zlib.compress(bytes(raw),9))+chunk(b"IEND",b""))
def white(x,y):
 d=((x*3+y*5)%5)-2
 return (238+d,244+d,249+d,255)
def reactor(x,y,band):
 c=white(x,y)
 # Slim stainless support rim, only at the horizontal ends of structure.
 if band==2 and y<=2 or band==1 and y>=29:
  c=(169,184,195,255)
 if band in (1,2):
  # Industrial engineering grille modules across each horizontal panel.
  # Only 3-26px are grilles; 0..2 and 27..31 are white corner breaks.
  if 4<=x<=27 and 8<=y<=17:
   c=(190,204,214,255)
   if 5<=x<=26 and 9<=y<=16:
    c=(39,52,65,255)
    if x in (5,26) or y in (9,16):c=(107,128,143,255)
    if 7<=x<=24 and 11<=y<=14 and x%4 in (0,1):
     c=(99,116,129,255)
   if (x,y) in ((4,8),(27,8),(4,17),(27,17)):
    c=(67,81,95,255)
  # Mid-plane panel access / metal joining plates, not dark full-tile boxes.
  if band==1 and 5<=x<=10 and 22<=y<=26:
   c=(199,211,220,255) if x in (5,10) or y in (22,26) else (89,112,128,255)
 return c
def corner_face(x,y,band,lit,bank):
 c=white(x,y)
 # Corner posts: white structural corner beams, never a ventilation grate.
 # Image #4: slender cyan LEDs join the horizontal rails at the corners.
 if bank and band in (1,2):
  strip=band==2 and 25<=y<=30 or band==1 and 1<=y<=6
  if strip:
   if y in (25,30,1,6):c=(68,90,105,255)
   else:c=(102,243,255,255) if lit else (90,163,185,255)
  # Dark graphite node with a bright inner LED; not a full dark tile.
  if (x,y) in ((5,5),(26,5),(5,26),(26,26)):
   c=(53,80,97,255)
 elif not bank and band in (1,2):
  if (y<=2 and band==2) or (y>=29 and band==1):
   c=(177,191,203,255)
  if x in (1,30):c=(203,214,222,255)
 return c

def bank(x,y,band,charged):
 c=white(x,y)
 if band==2:
  # Image #4: unbroken cyan rail directly above the glass facade.
  if 25<=y<=30:
   c=(54,79,95,255) if y in (25,30) else (
      (118,250,255,255) if y in (27,28) else (44,202,239,255)) if charged else (
      (73,157,184,255) if y in (27,28) else (49,91,112,255))
 elif band==1:
  # Same strip on the lower base frame, just under the glass.
  if 1<=y<=6:
   c=(54,79,95,255) if y in (1,6) else (
      (118,250,255,255) if y in (3,4) else (44,202,239,255)) if charged else (
      (73,157,184,255) if y in (3,4) else (49,91,112,255))
 return c

def mkmodel(name,texture_name,top_name):
 p=A/"models/block"/(name+".json")
 p.write_text(json.dumps({"parent":"minecraft:block/cube","textures":{
 "particle":"obsidiannetwork:block/"+texture_name,
 "up":"obsidiannetwork:block/"+top_name,
 "down":"obsidiannetwork:block/"+top_name,
 **{k:"obsidiannetwork:block/"+texture_name for k in ("north","south","east","west")}}},indent=2)+"\n",encoding="utf-8")

for band,postfix in ((0,"middle"),(1,"bottom"),(2,"top")):
 name="reactor_casing_formed_design3_"+postfix
 texture(name,lambda x,y,band=band:reactor(x,y,band))
 mkmodel(name,name,"reactor_casing_formed_top")
 cornername="reactor_casing_formed_design3_"+postfix+"_corner"
 texture(cornername,lambda x,y,band=band:corner_face(x,y,band,False,False))
 mkmodel(cornername,cornername,"reactor_casing_formed_top")
 for lit in (False,True):
  variant="_lit" if lit else ""
  name="powerbank_casing_formed_design4_"+postfix+variant
  texture(name,lambda x,y,band=band,lit=lit:bank(x,y,band,lit))
  mkmodel(name,name,"powerbank_casing_formed"+("_lit" if lit else "")+"_top")
  cornername="powerbank_casing_formed_design4_"+postfix+"_corner"+variant
  texture(cornername,lambda x,y,band=band,lit=lit:corner_face(x,y,band,lit,True))
  mkmodel(cornername,cornername,"powerbank_casing_formed"+("_lit" if lit else "")+"_top")

# All four skins use one stable property shape; the two glass families ignore
# position, retaining uninterrupted transparency and B530 light variants.
for name in ("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass"):
 p=A/"blockstates"/(name+".json")
 old=json.loads(p.read_text(encoding="utf-8"))
 assert len(old["variants"])==8,("B553_EXPECT_EIGHT_PREEXISTING_STATES",name)
 variants={}
 for base_key,base_value in old["variants"].items():
  for band in range(3):
   for corner in (False,True):
    key=base_key+",rim="+str(band)+",corner="+str(corner).lower()
    model=base_value["model"]
    if "casing" in name and "formed=true" in base_key:
     part={0:"middle",1:"bottom",2:"top"}[band]
     flavor="design3" if name.startswith("reactor") else "design4"
     suffix="_lit" if (name.startswith("powerbank") and "lit=true" in base_key) else ""
     model="obsidiannetwork:block/"+name+"_formed_"+flavor+"_"+part+("_corner" if corner else "")+suffix
    variants[key]={"model":model}
 assert len(variants)==48
 p.write_text(json.dumps({"variants":variants},indent=2)+"\n",encoding="utf-8")

# Verify the compiled materials are precisely selected by assembly state:
# 6 actual models/texture families for reactor and bank, no unformed change.
for machine,design in (("reactor","design3"),("powerbank","design4")):
 p=A/"blockstates"/(machine+"_casing.json")
 variants=json.loads(p.read_text(encoding="utf-8"))["variants"]
 for key,model in variants.items():
  if "formed=false" in key:
   assert "_formed_" not in model["model"]
  else:
   assert design in model["model"],(key,model)
print("B553_REACTOR_3_INDUSTRIE_PANELS_POWERBANK_4_LEUCHT_LINIEN_ASSEMBLED_PASS")
