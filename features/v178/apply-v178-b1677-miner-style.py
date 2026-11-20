#!/usr/bin/env python3
"""B1677 original xSxLabs miner resource overhaul: dark-purple body, violet
cartridges, emerald status, cyan display and visibly modeled diamond drill.
Matches the supplied visual direction without using assets from another mod.
Static vanilla baked geometry, no BE renderer, no FPS/tick hotpath changes.
"""
import os,json,struct,zlib
from pathlib import Path
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
model_path=R/"models/block/mining_builder.json"
model=json.loads(model_path.read_text(encoding="utf8"))
assert len(model["elements"])>=32,("B1677_MODEL_BASE_DRIFT",len(model["elements"]))
def rgb(c):return (c>>16&255,c>>8&255,c&255,255)
def png(size,pixel):
 raw=bytearray()
 for y in range(size):
  raw.append(0)
  for x in range(size):raw.extend(rgb(pixel(x,y)))
 def chunk(tag,b):
  return struct.pack(">I",len(b))+tag+b+struct.pack(">I",zlib.crc32(tag+b)&0xffffffff)
 return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")
def texture(kind,x,y):
 edge=x in (0,1,30,31) or y in (0,1,30,31)
 metal=0x1b1525 if ((x//4+y//4)%2) else 0x241b30
 if kind=="shell":
  if edge:return 0x383047
  if x in (3,28) or y in (3,28):return 0x4b3d5c
  if y in (7,24) and 5<x<27:return 0x3c2d4a
  if (x,y) in ((5,5),(26,5),(5,26),(26,26)):return 0x89dfe3
  return metal
 if kind=="panel":
  if edge:return 0x3e3153
  if 4<x<28 and y in (5,6,26,27):return 0x6e378e
  if 5<x<27 and 9<y<24:
   if (x+y)%5==0:return 0x59316f
   return 0x36203f
  return 0x292036
 if kind=="trim":
  if edge:return 0x39d8ea
  if x in (3,4,27,28) or y in (3,4,27,28):return 0x51708c
  if 6<x<25 and y in (9,10,21,22):return 0x8433af
  return 0x2b2039
 if kind=="core":
  dx=x-15.5;dy=y-15.5;r=dx*dx+dy*dy
  if edge:return 0x352640
  if r<13:return 0xd2f9ff
  if r<45:return 0x5beaf2
  if r<105:return 0x2785a1
  if r<180:return 0x56336f
  return 0x22182f
 if kind=="front":
  if edge:return 0x382745
  if x in (2,29) or y in (2,29):return 0x553560
  if 4<=y<=8 and 3<=x<=28:
   if 5<=x<=9 and y in (5,6,7):return 0x39ed71 # green live LED
   if 13<=x<=27 and y in (5,6):return 0x45e7eb # cyan energy data stripe
   return 0x10111a
  if y in (10,11) and 4<=x<=28:return 0xa24cc0
  if 14<=y<=27:
   for a in (5,13,21):
    if a<=x<=a+5:
     if x in (a,a+5) or y in (14,27):return 0x71429d
     if y in (16,17):return 0x563276
     if y in (23,24) and x in (a+2,a+3):return 0x34d6c6
     return 0x9c5db9 if x%2 else 0x8347aa
  return 0x161320
 if kind=="vent":
  if edge:return 0x413049
  if 4<x<28 and y in (5,26):return 0x753b92
  if 5<x<27 and (y%5 in (0,1)):return 0x101018
  if x in (3,28):return 0x4fdae4
  return 0x281e36
 if kind=="sensor":
  dx=x-15.5;dy=y-15.5;r=dx*dx+dy*dy
  if edge:return 0x694d7d
  if r<14:return 0xe8fcff
  if r<48:return 0x5de8f4
  if r<110:return 0x328ba9
  if r<160:return 0x6b4494
  return 0x20172e
 if kind=="display":
  # Engraved crossed mining pick and drill symbol.
  if edge:return 0x4fdbeb
  if 6<=y<=8 and 5<=x<=27:return 0x4eebea
  pick=(abs((x-16)-(y-16))<=1 and 9<=y<=24)
  cross=(9<=y<=12 and 9<=x<=24 and abs(y-10+(x-16)//10)<=1)
  drill=(x in (15,16) and 14<=y<=27)
  if pick or cross:return 0xbdf8ff
  if drill:return 0x46d8ee
  return 0x122334 if (x+y)%7 else 0x244565
 raise AssertionError(kind)
folder=R/"textures/block"
for name in ("shell","panel","trim","core","front","vent","sensor","display"):
 target=folder/("mining_builder_"+name+".png")
 assert target.exists(),("B1677_MISSING_PRIOR_TEXTURE",target)
 target.write_bytes(png(32,lambda x,y:texture(name,x,y)))
def part(lo,hi,tex):
 assert all(0<=v<=16 for v in (*lo,*hi)) and all(a<b for a,b in zip(lo,hi))
 model["elements"].append({
  "from":list(lo),"to":list(hi),
  "faces":{side:{"texture":"#"+tex} for side in
         ("north","south","west","east","up","down")}})
# Front drill head / identifiable mine spindle with protective claws.
part((6,5,0),(10,10,1),"sensor")
part((7,3,0),(9,5,1),"core")
part((5,5,0),(6,10,2),"trim")
part((10,5,0),(11,10,2),"trim")
part((6,10,0),(10,11,2),"trim")
part((7,2,1),(9,3,3),"shell")
# Green status lamp and cyan command strip, same visual placement as reference.
part((3,12,0),(5,14,1),"core")
part((7,13,0),(13,14,1),"display")
# Upper service panel / extraction head and purple drive housings.
part((3,15,3),(13,16,13),"shell")
part((5,15,5),(11,16,11),"sensor")
for x in (2,7,12):
 part((x,2,0),(x+2,4,2),"panel")
# Side cooling / mechanical drill support braces.
for x in (1,14):
 part((x,5,2),(x+1,12,14),"vent")
# Rear output access port.
part((6,4,15),(10,12,16),"display")
model_path.write_text(json.dumps(model,indent=2)+"\n",encoding="utf8")
assert len(model["elements"])>=48
print("B1677_PURPLE_CYAN_GREEN_MINER_BAKED_3D_PICK_DRILL_TEXTURES_PASS")
