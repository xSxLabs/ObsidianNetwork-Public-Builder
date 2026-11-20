#!/usr/bin/env python3
"""B1715: xSxLabs Mining Builder – original mechanical drill/miner visual overhaul.

Static vanilla block-model JSON with a forward-facing stepped drill, exposed
hydraulic arms, power cartridges, armored chassis, cooling fins, diamond teeth,
and legible top/front control surfaces. No BE renderer, ticks, packets,
world queries, gameplay changes, Java changes, or new third-party assets.
Remove only the unwanted 'CLAIMS' heading above the minimap.
"""
import json
import os
import struct
import zlib
from pathlib import Path

root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
modelpath=root/"models/block/mining_builder.json"
itempath=root/"items/mining_builder.json"
statepath=root/"blockstates/mining_builder.json"
old=json.loads(modelpath.read_text(encoding="utf-8"))
assert len(old.get("elements",[]))>=48, ("B1715_EXPECTED_OLDER_BUILDER",len(old.get("elements",[])))
assert json.loads(itempath.read_text())["model"]["model"]=="obsidiannetwork:block/mining_builder"
states=json.loads(statepath.read_text())["variants"]
assert set(states)=={f"facing={side}" for side in ("north","east","south","west")}

# Compact but genuinely three-dimensional. Deliberately retained entirely in
# [0,16] for reliable block rendering/culling on all rotations.
parts=[]
def box(lo,hi,material,sides=None):
    assert all(0<=v<=16 for v in (*lo,*hi)),(lo,hi)
    assert all(a<b for a,b in zip(lo,hi)),(lo,hi)
    faces=sides or ("north","south","west","east","up","down")
    parts.append({"from":list(lo),"to":list(hi),
                  "faces":{side:{"texture":"#"+material} for side in faces}})

# Tough two-level footing, undercarriage, rubber pads and separated support feet.
box((1,1,1),(15,3,15),"shell")
box((2,2,2),(14,4,14),"panel")
box((3,0,3),(13,1,13),"vent")
for x in (1,12):
    for z in (1,12):
        box((x,0,z),(x+3,2,z+3),"hydraulic")
        box((x+.4,1,z+.4),(x+2.6,2.6,z+2.6),"shell")

# Distinct raised engine block and purple armored angled-looking plate tiers.
box((3,3,4),(13,12,15),"shell")
box((4,4,5),(12,11,14),"panel")
box((3,11,4),(13,13,15),"trim")
box((4,13,5),(12,14,14),"shell")
box((5,14,6),(11,15,13),"panel")
for x in (2,12):
    for z in (4,12):
        box((x,3,z),(x+2,14,z+2),"hydraulic")
        box((x,5,z),(x+2,7,z+2),"trim")

# Side-mounted independent power cartridges / radiator ribs / side cylinders.
for x in (1,13):
    box((x,4,5),(x+2,12,13),"panel")
    box((x+.25,5,6),(x+1.75,11,12),"core")
    box((x,4,6),(x+2,5,12),"hydraulic")
    box((x,11,6),(x+2,12,12),"hydraulic")
    for z in (6,8,10,12):
        box((x,5.5,z),(x+2,6.3,z+.5),"trim")
    # Visible floating lower skids make it feel like a real machine, not a cube.
    box((x,2,4),(x+2,3,14),"warning")

# Readable front mechanical machine face with a large drill assembly;
# front is NORTH (z=0). Three differently sized axial stages create a
# forward-narrowing stepped cutter with a visible *physical* drill point.
box((3,3,3),(13,12,5),"hydraulic")
box((4,4,2),(12,11,4),"trim")
box((5,5,1.25),(11,10,3),"blade")
box((6,5.8,.55),(10,9.2,2),"hydraulic")
box((7,6.5,0),(9,8.5,1),"blade")
box((7.45,6.95,0),(8.55,8.05,.3),"sensor")
# Four projecting cutting teeth around the central high-power auger.
for x,y in ((5,7),(10,7)):
    box((x,6,.6),(x+1,9,2.25),"blade")
for x,y in ((7,5),(7,9)):
    box((7,y,.6),(9,y+1,2.25),"blade")
# Protective mandibles and exposed hydraulic guide rods to each side.
for x in (2,12):
    box((x,4,1),(x+2,5,6),"hydraulic")
    box((x,10,1),(x+2,11,6),"hydraulic")
    box((x+.5,5,1),(x+1.5,10,2),"trim")
    box((x+.5,5.5,2),(x+1.5,9.5,5),"vent")
box((4,3,1),(12,4,5),"warning")
box((4,11,1),(12,12,5),"warning")

# Status panel above the cutter, large enough to read in the world.
box((5,12,2),(11,14,4),"panel")
box((5.5,12.35,1.75),(10.5,13.65,2),"display")
box((3.5,12.3,1.75),(4.6,13.45,2),"sensor")
box((11.4,12.3,1.75),(12.5,13.45,2),"core")

# Top turbine/maintenance hatch: a strong read from above, not a flat lid.
box((4,14,4),(12,15,14),"hydraulic")
box((5,15,6),(11,16,12),"trim")
box((6,15.1,7),(10,16,11),"core")
for x in (4,11):
    box((x,14.2,5),(x+1,15.8,13),"vent")
for z in (4,13):
    box((4,14.2,z),(12,15.3,z+1),"hydraulic")
# Cable sockets, access lights and rear output port.
box((5,4,14),(11,11,16),"panel")
box((6,5,15.5),(10,10.5,16),"display")
for x in (4,11):
    box((x,7,14.5),(x+1,9,16),"sensor")
# Dark groove between the rear output and armor panels.
box((6,11,14),(10,12,16),"vent")

# Thin external longitudinal power lines make the silhouette visually distinct.
for x in (2,13):
    box((x,12,4),(x+1,13,14),"trim")
for z in (5,13):
    box((3,3,z),(13,4,z+1),"hydraulic")

assert 75<=len(parts)<=125,("B1715_PART_BUDGET",len(parts))
textures=("shell","panel","trim","core","front","vent","sensor",
          "display","blade","warning","hydraulic")
model={"ambientocclusion":True,
       "textures":{"particle":"obsidiannetwork:block/mining_builder_shell",
         **{name:"obsidiannetwork:block/mining_builder_"+name for name in textures}},
       "elements":parts}
assert all(face["texture"][1:] in model["textures"]
           for part in parts for face in part["faces"].values())
modelpath.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")

SIZE=64
def pix(kind,x,y):
    # All graphics are newly authored procedural pixel art. No borrowed assets.
    border=x in (0,1,2,61,62,63) or y in (0,1,2,61,62,63)
    screw=(x in (7,56) and y in (7,56))
    jitter=((x*17+y*23+(x^y)*5)%13)-6
    if kind=="shell":
        c=0x211c2e if (x//8+y//8)%2 else 0x282136
        if border:c=0x4a385f
        if x in (5,58) or y in (5,58):c=0x4c3a62
        if 13<=x<=50 and y in (13,14,49,50):c=0x342c42
    elif kind=="panel":
        c=0x1a2231 if (x//6+y//6)%2 else 0x20293a
        if border:c=0x364e5f
        if x in (9,54) or y in (9,54):c=0x45576a
        if y in (18,45) and 12<=x<=51:c=0x4c3773
    elif kind=="trim":
        c=0x532b83
        if border:c=0x241d3a
        if x in (5,6,57,58) or y in (5,6,57,58):c=0x925cce
        if (x+y)%23 in (0,1):c=0x754ab1
        if x in (12,51) and 13<=y<=50:c=0x40d8ef
    elif kind=="core":
        dx=x-31.5;dy=y-31.5;r=dx*dx+dy*dy
        c=(0xc9ffff if r<35 else 0x69edfb if r<160 else 0x3196bd
           if r<400 else 0x543e83 if r<720 else 0x171729)
        if border:c=0x38495c
        if 550<r<680 and (x+y)%5==0:c=0x51e2e8
    elif kind=="sensor":
        dx=x-31.5;dy=y-31.5;r=dx*dx+dy*dy
        c=(0xe7fcff if r<50 else 0x57edff if r<230 else 0x257db0
           if r<510 else 0x342a56 if r<790 else 0x151b2c)
        if (x==32 or y==32) and 200<r<570:c=0xc5faff
    elif kind=="display":
        c=0x071725 if border else 0x0a2939
        if x in (4,59) or y in (4,59):c=0x47e4ee
        if 12<=y<=16 and 11<=x<=50:c=0x30d4fa
        if 20<=y<=44 and 10<=x<=53:
            if abs(x-32)<2 and 25<=y<=47:c=0xb9faff
            elif 19<=y<=23 and 13<=x<=52:c=0x8ae6f2
            elif abs((x-32)-(y-32))<=2:c=0x4ae4fa
            elif y%7==0:c=0x225572
        if 51<=y<=54 and 8<=x<=55:c=0x38e6a3
    elif kind=="front":
        c=0x19243b if (x+y)%13 else 0x3b5264
        if border:c=0x49345c
        if 12<=y<=51 and x in (12,51):c=0x38ddec
    elif kind=="vent":
        c=0x0e111c if (y//6)%2 else 0x263647
        if y%6==0:c=0x557489
        if border:c=0x422d56
        if x in (7,56):c=0x42b0c8
    elif kind=="blade":
        c=0x85b1ca if ((x+y)//8)%2 else 0xb0d2df
        if border:c=0x354b65
        if abs((x-32)-(y-32))<3:c=0xf1ffff
        if (x+y)%17 in (0,1):c=0x52e8f5
    elif kind=="warning":
        c=0x241d2a if ((x+y)//11)%2 else 0xe39b32
        if border:c=0x60466e
    elif kind=="hydraulic":
        c=0x576879 if (x//8+y//8)%2 else 0x7d91a4
        if border:c=0x293447
        if x in (11,12,51,52):c=0xbdc9d0
        if y in (10,53):c=0x40c6d9
    else:
        raise AssertionError(("B1715_TEXTURE_UNKNOWN",kind))
    if screw:c=0xc8efff
    r,g,b=(c>>16)&255,(c>>8)&255,c&255
    # Tiny fixed micrograin: restrained variation, never per-frame random.
    if not border and kind in ("shell","panel","hydraulic"):
        r=max(0,min(255,r+jitter))
        g=max(0,min(255,g+jitter))
        b=max(0,min(255,b+jitter))
    return (r,g,b,255)

def chunk(tag,body):
    return (struct.pack(">I",len(body))+tag+body+
            struct.pack(">I",zlib.crc32(tag+body)&0xffffffff))
def encode(kind):
    raw=bytearray()
    for y in range(SIZE):
        raw.append(0)
        for x in range(SIZE):
            raw.extend(pix(kind,x,y))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR",struct.pack(">IIBBBBB",SIZE,SIZE,8,6,0,0,0))+
            chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b""))
folder=root/"textures/block"
folder.mkdir(parents=True,exist_ok=True)
for name in textures:
    path=folder/("mining_builder_"+name+".png")
    path.write_bytes(encode(name))
    assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

# Keep the actual minimap feature intact; remove its redundant title ONLY.
# If coordinates are enabled, show coordinates without a forced "CLAIMS" tag.
java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V178ClaimsClient.java"
current=java.read_text(encoding="utf-8")
oldtitle='''   g.text(mc.font,showCoordinates?"CLAIMS "+(mc.player.blockPosition().getX()>>4)+","+(mc.player.blockPosition().getZ()>>4):"CLAIMS M",ox+3,oy+2,0xffb2ecfa);'''
newtitle='''   if(showCoordinates)g.text(mc.font,
       (mc.player.blockPosition().getX()>>4)+","+(mc.player.blockPosition().getZ()>>4),
       ox+3,oy+2,0xffb2ecfa);'''
assert current.count(oldtitle)==1,("B1715_MINIMAP_TITLE_SOURCE_DRIFT",current.count(oldtitle))
java.write_text(current.replace(oldtitle,newtitle,1),encoding="utf-8")
assert '"CLAIMS M"' not in java.read_text()
print("B1715_MECHANICAL_DIAMOND_DRILL_BUILDER_STATIC_"+str(len(parts))+
      "_PARTS_64PX_ART_MINIMAP_CLAIMS_TITLE_REMOVED_PASS")
