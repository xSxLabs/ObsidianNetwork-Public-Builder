#!/usr/bin/env python3
"""Flux-Point-inspired original compact wireless nodes (not copied mod assets).

Replace only transmitter/receiver block models and pixel textures. Keep two
existing registered devices, four facing variants, recipes, loot and items.
Run AFTER apply-antenna-assets.py. No network or FE code is touched.
"""
from pathlib import Path
import json
import math
import os
import struct
import zlib

root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def write_json(name,data):
    p=root/name
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

def png_chunk(kind,payload):
    return struct.pack(">I",len(payload))+kind+payload+struct.pack(">I",zlib.crc32(kind+payload)&0xffffffff)

def pixel_png(path,theme,variant):
    # Three handmade pixel surfaces for a compact metallic point block.
    # Bright colored insets and a dark carbon chassis; no borrowed PNGs.
    rows=[]
    for y in range(16):
        row=bytearray(b"\x00")
        for x in range(16):
            d=max(abs(x-7.5),abs(y-7.5))
            frame=x in (0,15) or y in (0,15)
            if variant=="case":
                base=(27,30,40)
                if (x+y)%5==0:base=(37,41,54)
                if frame:base=(12,14,21)
                if x in (2,13) or y in (2,13):base=(53,55,73)
                if 5<=x<=10 and 5<=y<=10:base=(55,61,79)
            elif variant=="trim":
                base=(27,30,40) if d<3.5 else (51,54,68)
                if 3.5<=d<=5.5:
                    base=tuple(int(v*(0.85 if (x+y)%3==0 else 1)) for v in theme)
                if frame:base=(14,16,24)
            else:
                base=(16,17,30) if d>6 else theme
                if d>=4:base=tuple(int(v*.42) for v in theme)
                if d<=2.5:base=(226,236,249)
                if (x==7 or y==7) and d<=5:base=tuple(min(255,int(v*1.25)) for v in theme)
                if frame:base=(17,19,31)
            row.extend((*base,255))
        rows.append(bytes(row))
    raw=b"".join(rows)
    file=root/("textures/block/"+path+".png")
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_bytes(b"\x89PNG\r\n\x1a\n"+
        png_chunk(b"IHDR",struct.pack(">IIBBBBB",16,16,8,6,0,0,0))+
        png_chunk(b"IDAT",zlib.compress(raw,9))+png_chunk(b"IEND",b""))

def cuboid(frm,to,texture):
    return {"from":frm,"to":to,"faces":{
      k:{"texture":"#"+texture,"cullface":k} if frm==[0,0,0] and to==[16,16,16]
      else {"texture":"#"+texture}
      for k in ("north","south","east","west","up","down")}}

# Dark low base + inset ring + raised glowing point. Not an antenna mast.
def model(slug,receiver):
    elements=[
        cuboid([1,0,1],[15,4,15],"case"),
        cuboid([2,4,2],[14,6,14],"trim"),
        cuboid([4,6,4],[12,10,12],"case"),
        cuboid([3,10,3],[13,12,13],"trim"),
        cuboid([5,12,5],[11,16,11],"core"),
        cuboid([5,13,4],[11,15,5],"case"),
        cuboid([5,13,11],[11,15,12],"case"),
        cuboid([4,13,5],[5,15,11],"case"),
        cuboid([11,13,5],[12,15,11],"case"),
    ]
    if not receiver:
        # A raised transmission cross/point differentiates TX from RX.
        elements.extend([
           cuboid([7,6,2],[9,10,4],"core"),
           cuboid([7,6,12],[9,10,14],"core"),
           cuboid([2,6,7],[4,10,9],"core"),
           cuboid([12,6,7],[14,10,9],"core"),
        ])
    return {"ambientocclusion":False,"textures":{
       "particle":"obsidiannetwork:block/"+slug+"_case",
       "case":"obsidiannetwork:block/"+slug+"_case",
       "trim":"obsidiannetwork:block/"+slug+"_trim",
       "core":"obsidiannetwork:block/"+slug+"_core",
    },"elements":elements}

for slug,rgb,is_receiver in (
    ("network_transmitter",(175,82,238),False),
    ("network_receiver",(58,193,243),True),
):
    model_path=root/("models/block/"+slug+".json")
    assert model_path.exists(),"run after antenna assets"
    write_json("models/block/"+slug+".json",model(slug,is_receiver))
    for surface in ("case","trim","core"):
        pixel_png(slug+"_"+surface,rgb,surface)
    # Existing blockstates, item definitions, craft and loot point to this
    # same block model; they remain unchanged.
    item=root/("models/item/"+slug+".json")
    assert json.loads(item.read_text()).get("parent")=="obsidiannetwork:block/"+slug
    states=root/("blockstates/"+slug+".json")
    assert len(json.loads(states.read_text())["variants"])==4
print("WIRELESS_POINT_STYLE_V2 PASS original compact node models; TX violet / RX cyan")
