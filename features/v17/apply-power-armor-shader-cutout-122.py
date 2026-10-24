#!/usr/bin/env python3
"""Build122: shader-safe armor energy field for Bliss 2.1.2 and vanilla.

Use the same depth-tested armor CUTOUT pipeline as ordinary armor, rather than
entityTranslucent. A purpose-made 1-bit alpha honeycomb mask draws sparse blue
hex lines and leaves real holes; no translucent "solid glass" surface that
Bliss/Iris can accidentally composite as an opaque/dark entity.

Smooth breathing survives as color BRIGHTNESS rather than fractional alpha;
the hit flash still brightens the entire visible honeycomb. The six ModelPart
joints, Elytra/swimming pose, installed-card/FE checks and server shield remain
untouched. This is a visual-only client patch plus one texture overwrite.
"""
import math
import os
import struct
import zlib
from pathlib import Path

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
tex=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/textures/entity/power_armor_shield_hex.png"
src=java.read_text(encoding="utf-8")
for mark in ("BUILD111_POSED_ARMOR_SHIELD",
             "BUILD115_ARMOR_POSE_LOCK","BUILD115_SLOW_BLUE_BREATH",
             "BUILD120_ELYTRA_SHIELD_POSE"):
 assert mark in src,("Build122 missing shield prerequisite",mark)
assert tex.is_file(),("Build122 expected existing hex texture",tex)

# A 1-bit cutout texture guarantees fully transparent background and fully
# opaque hex LINE pixels. Avoid alpha=1..254, which engages shader translucency.
old='private static final RenderType SHIELD_RENDER=RenderTypes.entityTranslucent(SKIN);'
new='''// BUILD122_BLISS_SAFE_ARMOR_CUTOUT: shader-friendly, depth-tested holes.
 private static final RenderType SHIELD_RENDER=RenderTypes.armorCutoutNoCull(SKIN);'''
assert src.count(old)==1,("Build122 RenderType drift",src.count(old))
src=src.replace(old,new,1)

# Keep Build115's continuous ~7.5sec breathing and hit alpha calculation as
# an artistic BRIGHTNESS input, NOT actual GPU transparency; this prevents the
# shield becoming a ghostly blue opaque entity under Bliss deferred rendering.
old='''  // Fullbright preserves the energy glow at night. UV maps the same hex
  // membrane from Build110 separately across each limb.
  out.addVertex(pose,(cx+rx*vx)*PIXEL,(cy+ry*vy)*PIXEL,(cz+rz*vz)*PIXEL)
     .setColor(92,194,255,alpha)
     .setUv(u,v)
     .setOverlay(OverlayTexture.NO_OVERLAY)
     .setLight(0x00F000F0)
     .setNormal(pose,vx,vy,vz);'''
new='''  // BUILD122_CUTOUT_BREATH: fade the luminous hex color, never its alpha.
  // The texture's empty cells have alpha 0; edges have alpha 255. Thus the
  // outfit shows through actual holes and the renderer depth-tests properly.
  float strength=Math.min(1F,Math.max(0F,alpha/247F));
  int red=(int)(25F+95F*strength);
  int green=(int)(55F+142F*strength);
  int blue=(int)(96F+159F*strength);
  out.addVertex(pose,(cx+rx*vx)*PIXEL,(cy+ry*vy)*PIXEL,(cz+rz*vz)*PIXEL)
     .setColor(red,green,blue,255)
     .setUv(u,v)
     .setOverlay(OverlayTexture.NO_OVERLAY)
     .setLight(0x00E000E0) // 14/15 light, not shader-blowing fullbright
     .setNormal(pose,vx,vy,vz);'''
assert src.count(old)==1,("Build122 vertex drift",src.count(old))
src=src.replace(old,new,1)
assert "RenderTypes.entityTranslucent(SKIN)" not in src
assert "RenderTypes.armorCutoutNoCull(SKIN)" in src
assert ".setColor(red,green,blue,255)" in src
assert ".setLight(0x00F000F0)" not in src
assert "state.isFallFlying" in src
assert src.count("submitPart(stack,collector,model.")==6
assert src.count("joint.translateAndRotate(stack);")==1
assert 'id.equals("energy_shield")' in src
assert "EnergyTool.energy(armor)<20L" in src
java.write_text(src,encoding="utf-8")

# Recreate the original hex layout using only true 0/255 alpha, no colored
# membrane interior and no soft translucent edges. The thin, partly stippled
# honeycomb covers ~12% of its tile and reveals the other ~88% of the suit.
N=64
pixels=[]
line_pixels=0
for yy in range(N):
 row=bytearray((0,))
 for xx in range(N):
  px,py=xx+.5,yy+.5
  distance=999.0
  for j in range(-2,5):
   cy=32+j*27
   for i in range(-3,5):
    cx=32+i*31.2+(15.6 if (j&1) else 0)
    points=[(cx+18*math.cos(math.pi*k/3+math.pi/6),
             cy+18*math.sin(math.pi*k/3+math.pi/6))
            for k in range(6)]
    for k in range(6):
     ax,ay=points[k]
     bx,by=points[(k+1)%6]
     dx,dy=bx-ax,by-ay
     t=max(0.0,min(1.0,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
     distance=min(distance,math.hypot(px-(ax+t*dx),py-(ay+t*dy)))
  edge=(distance<=.72 or (distance<1.12 and ((xx*37+yy*59)%4)<2))
  opacity=255 if edge else 0
  line_pixels+=int(edge)
  # White mask: strength/color is controlled by one animated vertex tint.
  row.extend((255,255,255,opacity))
 pixels.append(bytes(row))
assert .07<line_pixels/(N*N)<.20,("unexpected shield opacity coverage",line_pixels)
def chunk(kind,data):
 return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
raw=b"".join(pixels)
png=(b"\x89PNG\r\n\x1a\n"
     +chunk(b"IHDR",struct.pack(">IIBBBBB",N,N,8,6,0,0,0))
     +chunk(b"IDAT",zlib.compress(raw,9))
     +chunk(b"IEND",b""))
tex.write_bytes(png)
assert tex.read_bytes()[:8]==b"\x89PNG\r\n\x1a\n"
assert all(a in (0,255) for row in pixels for a in row[4::4])
print("BUILD122_BLISS_SAFE_ARMOR_CUTOUT PASS: vanilla armor cutout layer, genuine open hex mesh (~12% line coverage), no fractional alpha, smooth blue brightness/hit pulse, six poses/FE intact")
