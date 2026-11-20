#!/usr/bin/env python3
"""B1677 1-block-per-map-pixel topography and gapless Xaero-like claim overview.
Keeps original assets, cache identifiers and 1.7.8 options; upgrades 4x4 and
8x8 saved exploration to 16x16 in-place with bounded client-only sampling.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf8")
 if s.count(old)!=1:
  for d in (-2,-1,1,2):
   def shift(val):
    out=[]
    for line in val.split("\n"):
     if not line.strip():out.append(line);continue
     n=len(line)-len(line.lstrip(" "))
     if n+d<0:return None
     out.append(" "*(n+d)+line[n:])
    return "\n".join(out)
   a,b=shift(old),shift(new)
   if a and s.count(a)==1:old,new=a,b;break
 assert s.count(old)==1,("B1677_TERRAIN_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf8")

# 1 pixel per world X/Z column, 16x16 topography per explored chunk.
patch("client/V178TerrainMap.java",
 "public static final int RES=8;","public static final int RES=16;")
patch("client/V178TerrainMap.java",
'''    int wx=(cx<<4)+x*2+1,wz=(cz<<4)+z*2+1;''',
'''    int wx=(cx<<4)+x,wz=(cz<<4)+z;''')
# Higher relief contrast and additive, subtle material grain. Never draws or
# scans world data on the render thread; only on the existing client tick.
patch("client/V178TerrainMap.java",
'''    double shade=Math.max(.69,Math.min(1.11,.97+(y-east)*.045+(y-south)*.045));''',
'''    double shade=Math.max(.58,Math.min(1.17,.95+(y-east)*.095+(y-south)*.075));
    if(y>world.getSeaLevel()+15)shade*=.985;''')
# Persist 16x16 colors in a new version. Both 4x4 and 8x8 historic files are
# expanded on read. We never delete or discard explored terrain coordinates.
patch("client/V178TerrainMap.java",
'''     out.writeInt(0x58535839);out.writeInt(data.size());''',
'''     out.writeInt(0x5853583a);out.writeInt(data.size());''')
patch("client/V178TerrainMap.java",
'''    if(format!=0x58535838&&format!=0x58535839)return;''',
'''    if(format!=0x58535838&&format!=0x58535839&&format!=0x5853583a)return;''')
patch("client/V178TerrainMap.java",
'''     if(format==0x58535838){
      for(int y=0;y<4;y++)for(int x=0;x<4;x++){
       int color=in.readInt();
       for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++)
        pixels[(y*2+dy)*RES+x*2+dx]=color;
      }
      dirty=true; // on next bounded save, upgrade the old data in-place
     }else for(int j=0;j<pixels.length;j++)pixels[j]=in.readInt();''',
'''     int oldResolution=format==0x58535838?4:format==0x58535839?8:16;
     int scale=RES/oldResolution;
     for(int yy=0;yy<oldResolution;yy++)for(int xx=0;xx<oldResolution;xx++){
      int color=in.readInt();
      for(int dy=0;dy<scale;dy++)for(int dx=0;dx<scale;dx++)
       pixels[(yy*scale+dy)*RES+xx*scale+dx]=color;
     }
     if(format!=0x5853583a)dirty=true; // transparent upgrade on next save''')
# Do not paint navy gaps between chunk terrain tiles in the minimap.
patch("client/V178ClaimsClient.java",
'''     if(drawTerrain)V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,step-1);
     else g.fill(x,y,x+step-1,y+step-1,0xff1c2530);
     if(drawClaims)V178TerrainMap.drawClaim(g,x,y,step-1,''',
'''     if(drawTerrain)V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,step);
     else g.fill(x,y,x+step,y+step,0xff1c2530);
     if(drawClaims)V178TerrainMap.drawClaim(g,x,y,step,''')
# Unclaimed chunks should not have big black lines: claims themselves are
# shown as soft outlines above full-resolution terrain.
patch("client/V178ClaimsMapScreen.java",
'''    else if(tile>=8){
     g.fill(px,py,px+tile,py+1,0x44557788);
     g.fill(px,py,px+1,py+tile,0x44557788);
    }''',
'''    // Leave wild terrain unobscured; draw outlines only for actual claims.''')
# Add unambiguous pointing head to the player locator on the live minimap.
patch("client/V178ClaimsClient.java",
'''     g.fill(px,py-4,px+1,py+1,0xffffffff);''',
'''     double heading=Math.toRadians(mc.player.getYRot());
     int hx=px-(int)Math.round(Math.sin(heading)*5),
         hz=py+(int)Math.round(Math.cos(heading)*5);
     g.fill(hx-1,hz-1,hx+2,hz+2,0xffffffff);''')
patch("client/V178ClaimsMapScreen.java",
'''     g.fill(px,py-4,px+1,py+1,0xffffffff);''',
'''     double heading=Math.toRadians(p.getYRot());
     int hx=px-(int)Math.round(Math.sin(heading)*5),
         hz=py+(int)Math.round(Math.cos(heading)*5);
     g.fill(hx-1,hz-1,hx+2,hz+2,0xffffffff);''')
assert "RES=16" in (J/"client/V178TerrainMap.java").read_text()
assert "format!=0x5853583a" in (J/"client/V178TerrainMap.java").read_text()
assert "Math.toRadians(mc.player.getYRot())" in (J/"client/V178ClaimsClient.java").read_text()
print("B1677_MAP_16X16_REAL_TERRAIN_NO_BLACK_TILE_GAPS_EXACT_PLAYER_HEADING_PASS")
