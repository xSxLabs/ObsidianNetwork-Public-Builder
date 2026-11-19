#!/usr/bin/env python3
"""B1666 original xSxLabs Mining Shape Card pixel-art + upgraded baked 3D Builder.
Client resources only: no runtime renderer, extra ticks, or recipe regressions.
"""
import os,json,struct,zlib
from pathlib import Path
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def png(size,paint):
 rows=bytearray()
 for y in range(size):
  rows.append(0)
  for x in range(size):
   r,g,b,a=paint(x,y)
   rows.extend((r,g,b,a))
 def chunk(t,body):
  return struct.pack(">I",len(body))+t+body+struct.pack(">I",zlib.crc32(t+body)&0xffffffff)
 return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(rows,9))+chunk(b"IEND",b"")
def rgb(color):
 return (color>>16&255,color>>8&255,color&255,255)
card=R/"models/item/mining_shape_card.json"
j=json.loads(card.read_text(encoding="utf8"))
assert j["textures"]["layer0"]=="minecraft:item/map","B1666_CARD_MODEL_SOURCE_DRIFT"
j["textures"]["layer0"]="obsidiannetwork:item/mining_shape_card"
card.write_text(json.dumps(j,indent=2)+"\n",encoding="utf8")
item=R/"textures/item/mining_shape_card.png"
assert not item.exists(),"B1666_CARD_TEXTURE_COLLISION"
item.parent.mkdir(parents=True,exist_ok=True)
def card_pixel(x,y):
 # Technological beveled dark titanium card, aqua glass blueprint window.
 if x<6 or x>=58 or y<5 or y>=59:return (0,0,0,0)
 if (x<12 or x>=52) and (y<11 or y>=53) and ((x<10 or x>=54) and (y<9 or y>=55)):
  return (0,0,0,0)
 edge=x in (6,7,56,57) or y in (5,6,57,58)
 if edge:return rgb(0x66d7e4 if (x+y)%4 else 0xb4f9ff)
 if x in (9,54) or y in (8,55):return rgb(0x172c41)
 if (x in (12,51) and 10<y<54) or (y in (11,52) and 10<x<53):
  return rgb(0x2c647a)
 if 15<=x<=48 and 15<=y<=47:
  # Digital scan / pixel blueprint, diagonal laser and highlighted shape.
  if x in (15,48) or y in (15,47):return rgb(0x55d9ec)
  if (x-32)**2+(y-31)**2<48:return rgb(0x77e6fc)
  if x in (23,40) and 20<y<44:return rgb(0x32c9e5)
  if y in (23,39) and 19<x<45:return rgb(0x32c9e5)
  if (x+y)%7==0:return rgb(0x2a6889)
  return rgb(0x0c344d if (y%3) else 0x144765)
 if (x in (12,51) and y in (14,49)) or (y in (13,50) and x in (13,50)):
  return rgb(0xb7f5ff)
 if 18<=x<=45 and y in (49,50):
  return rgb(0x1a91ae if x%4==0 else 0x253f55)
 if 15<=y<=47 and x in (11,52):return rgb(0x21abbf)
 return rgb(0x17283b if (x+y)%9 else 0x253e55)
item.write_bytes(png(64,card_pixel))

model=R/"models/block/mining_builder.json"
data=json.loads(model.read_text(encoding="utf8"))
assert len(data.get("elements",[]))==20,"B1666_BUILDER_MODEL_SOURCE_DRIFT"
texroot=R/"textures/block";texroot.mkdir(parents=True,exist_ok=True)
def texture(kind,x,y):
 noise=((x*7+y*13)%13)-6
 if kind=="sensor":
  xx=x-15.5;yy=y-15.5;radius=xx*xx+yy*yy
  if x in (2,3,28,29) or y in (2,3,28,29):return rgb(0x69ddeb)
  if radius<20:return rgb(0xd4fbff)
  if radius<64:return rgb(0x4ed9ef)
  if radius<129:return rgb(0x1b759a)
  return rgb(0x14283d if (x+y)%5 else 0x263b51)
 if x in (0,1,30,31) or y in (0,1,30,31):return rgb(0x74ecf1)
 if 5<x<26 and y in (8,9,22,23):return rgb(0x4fcfe8)
 if 6<y<25 and x in (8,9,22,23):return rgb(0x316e98)
 if 11<x<21 and y in (12,13,14,15,16,17,18):return rgb(0x65e9ef)
 base=0x172b43 if (x//4+y//4)%2 else 0x233f58
 return rgb(base)
for name in ("sensor","display"):
 path=texroot/("mining_builder_"+name+".png")
 assert not path.exists(),("B1666_BUILDER_TEXTURE_COLLISION",name)
 path.write_bytes(png(32,lambda x,y:texture(name,x,y)))
 data["textures"][name]="obsidiannetwork:block/mining_builder_"+name
def box(lo,hi,material):
 assert all(0<=x<=16 for x in (*lo,*hi))
 data["elements"].append({"from":list(lo),"to":list(hi),
   "faces":{face:{"texture":"#"+material} for face in
            ("north","south","west","east","up","down")}})
# Front-mounted holographic mining sensor, inset console, protective frame,
# recessed conduits and raised caps. Geometry is all static/baked.
box((4,4,0),(12,12,1),"trim")
box((5,5,0),(11,11,.4),"display")
box((6,6,0),(10,10,.2),"sensor")
box((4,3,0),(12,4,2),"shell")
box((4,12,0),(12,13,2),"shell")
box((3,4,0),(4,12,2),"shell")
box((12,4,0),(13,12,2),"shell")
for x in (1,14):
 box((x,4,3),(x+1,12,4),"trim")
 box((x,4,12),(x+1,12,13),"trim")
box((5,15,5),(11,16,11),"sensor")
box((2,2,5),(3,14,11),"vent")
box((13,2,5),(14,14,11),"vent")
box((6,4,15.5),(10,12,16),"display")
model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
assert len(data["elements"])>=32
print("B1666_XSXLABS_MINING_CARD_64PX_ORIGINAL_ART_AND_BUILDER_3D_MODEL_PASS")
