#!/usr/bin/env python3
"""Build125: subtle normally, brilliantly blue only on actual absorbed damage.

Build124 fixed Bliss 2.1.2 compatibility using armorCutoutNoCull with truly
transparent cell interiors. KEEP that working shader-safe renderer, all six
joint poses and the multiplayer Elytra visual fix. Reduce the sparse hex line
coverage from ~12% to ~5-6%, dim the idle vertex tint dramatically, retain
smooth 7.5-second breathing and high-contrast damage flashes. Client visuals
and one PNG texture only; no server energy/shield/gameplay changes.
"""
import math
import os
import struct
import zlib
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
java=root/"client/PowerArmorShieldClient.java"
texture=res/"textures/entity/power_armor_shield_hex.png"
src=java.read_text(encoding="utf-8")
for marker in ("BUILD122_BLISS_SAFE_ARMOR_CUTOUT",
               "BUILD122_CUTOUT_BREATH",
               "BUILD115_SLOW_BLUE_BREATH",
               "BUILD120_ELYTRA_SHIELD_POSE"):
 assert marker in src,("missing prerequisite",marker)
assert texture.is_file()

old='''  float strength=Math.min(1F,Math.max(0F,alpha/247F));
  int red=(int)(25F+95F*strength);
  int green=(int)(55F+142F*strength);
  int blue=(int)(96F+159F*strength);'''
new='''  // BUILD125_SUBTLE_IDLE_AND_HIT_FLASH: never return to translucent pixels.
  // Build115 provides idle alpha 41..103 and hit alpha up to 247. Normalize
  // that artistic value into a *quadratic* brightness curve so the hexes are
  // barely there at idle and glow unmistakably when the suit absorbs damage.
  // Smooth 7.5s breathing remains from Build115, with no hard transitions.
  float energyGlow=Math.min(1F,Math.max(0F,(alpha-41F)/206F));
  float easedGlow=energyGlow*energyGlow;
  int red=(int)(9F+87F*easedGlow);
  int green=(int)(22F+190F*easedGlow);
  int blue=(int)(42F+213F*easedGlow);'''
assert src.count(old)==1,("Build125 original color curve drift",src.count(old))
src=src.replace(old,new,1)

# Shader-safe alpha and renderer stay IDENTICAL to Build124.
assert "RenderTypes.armorCutoutNoCull(SKIN)" in src
assert "RenderTypes.entityTranslucent(SKIN)" not in src
assert ".setColor(red,green,blue,255)" in src
assert ".setLight(0x00E000E0)" in src
assert "phase*phase*(3F-2F*phase)" in src
assert src.count("submitPart(stack,collector,model.")==6
assert src.count("joint.translateAndRotate(stack);")==1
assert "state.isFallFlying" in src
assert "EnergyTool.energy(armor)<20L" in src
assert 'id.equals("energy_shield")' in src
java.write_text(src,encoding="utf-8")

# Build124 hex texture is 12.1% solid white line pixels (binary alpha).
# Preserve the identical hexagon layout at a narrower 0.45px threshold and
# remove the extra stippled outer glow, which was overly pronounced in-game.
N=64
rows=[]
lines=0
for yy in range(N):
 row=bytearray((0,))
 for xx in range(N):
  px,py=xx+.5,yy+.5
  distance=999.0
  for j in range(-2,5):
   cy=32+j*27
   for i in range(-3,5):
    cx=32+i*31.2+(15.6 if j&1 else 0)
    points=[(cx+18*math.cos(math.pi*k/3+math.pi/6),
             cy+18*math.sin(math.pi*k/3+math.pi/6))
            for k in range(6)]
    for k in range(6):
     ax,ay=points[k]; bx,by=points[(k+1)%6]
     dx,dy=bx-ax,by-ay
     t=max(0.0,min(1.0,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
     distance=min(distance,math.hypot(px-(ax+t*dx),py-(ay+t*dy)))
  ink=distance<=.45
  lines+=int(ink)
  row.extend((255,255,255,255 if ink else 0))
 rows.append(bytes(row))
coverage=lines/(N*N)
assert .045<coverage<.065,("unexpected sparse hex coverage",coverage)
assert all(a in (0,255) for row in rows for a in row[4::4])
def chunk(kind,data):
 return (struct.pack(">I",len(data))+kind+data+
         struct.pack(">I",zlib.crc32(kind+data)&0xffffffff))
data=b"".join(rows)
png=(b"\x89PNG\r\n\x1a\n"+
     chunk(b"IHDR",struct.pack(">IIBBBBB",N,N,8,6,0,0,0))+
     chunk(b"IDAT",zlib.compress(data,9))+
     chunk(b"IEND",b""))
texture.write_bytes(png)
assert texture.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
print("BUILD125_SUBTLE_SHIELD PASS: Bliss-safe cutout preserved, ~5.6% fine hex ink, dark gently breathing blue at rest, bright on hit, no gameplay/FE changes")
