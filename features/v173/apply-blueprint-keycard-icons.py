#!/usr/bin/env python3
"""Build174: original pixel textures for blueprint, quill and linked key card."""
from pathlib import Path
import os,json,struct,zlib
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def image():
 return [[(0,0,0,0) for x in range(32)] for y in range(32)]
def paint(a,x1,y1,x2,y2,color):
 for y in range(max(0,y1),min(32,y2)):
  for x in range(max(0,x1),min(32,x2)):a[y][x]=color
def line(a,x1,y1,x2,y2,col,stroke=1):
 n=max(abs(x2-x1),abs(y2-y1),1)
 for i in range(n+1):
  x=round(x1+(x2-x1)*i/n);y=round(y1+(y2-y1)*i/n)
  paint(a,x,y,x+stroke,y+stroke,col)
def save(slug,a):
 data=b"".join(b"\x00"+b"".join(bytes(p) for p in row) for row in a)
 def chunk(t,d):
  return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
 raw=(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",32,32,8,6,0,0,0))+
  chunk(b"IDAT",zlib.compress(data,9))+chunk(b"IEND",b""))
 p=R/"textures/item"/(slug+".png");p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(raw)
 obj={"parent":"minecraft:item/generated","textures":{"layer0":"obsidiannetwork:item/"+slug}}
 for rel,value in [
 ("models/item/"+slug+".json",obj),
 ("items/"+slug+".json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+slug}})]:
  p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(json.dumps(value,indent=2)+"\n")
cyan=(85,226,255,255);white=(230,246,255,255);paper=(36,95,183,255)
a=image()
paint(a,4,3,27,29,paper)
for x in (4,26):paint(a,x,3,x+1,29,white)
for y in (3,28):paint(a,4,y,27,y+1,white)
for x in (8,15,22):line(a,x,7,x,25,cyan)
for y in (8,16,24):line(a,8,y,24,y,cyan)
paint(a,11,11,19,21,(19,58,117,255))
for x in (11,18):paint(a,x,11,x+1,21,white)
for y in (11,20):paint(a,11,y,19,y+1,white)
save("network_blueprint",a)
b=[row.copy() for row in a]
line(b,8,27,28,7,(22,31,55,255),4)
line(b,11,24,27,8,(235,184,78,255),2)
paint(b,26,5,30,9,cyan)
save("network_schematic_quill",b)
c=image();paint(c,2,7,30,26,(60,87,116,255))
paint(c,2,7,30,8,white);paint(c,2,25,30,26,white)
paint(c,3,8,4,25,white);paint(c,29,8,30,25,white)
paint(c,4,10,28,14,(15,39,67,255))
paint(c,6,17,15,23,(239,195,87,255))
for y in (19,21):line(c,6,y,14,y,(115,85,49,255))
for x in (9,12):line(c,x,17,x,23,(115,85,49,255))
line(c,19,18,27,18,cyan);line(c,19,21,26,21,cyan)
save("network_link_card",c)
print("V173_ORIGINAL_ITEM_TEXTURES174_PASS")
