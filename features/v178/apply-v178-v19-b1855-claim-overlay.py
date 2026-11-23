#!/usr/bin/env python3
"""B1855 / v1.7.8 v19: screenshot-style translucent chunk claims on both maps.

Only replace the existing common GUI claim painter, shared by the minimap and
world map. The server's ownership status, loaded bit, network format, world
terrain cache, persistence, and map sampling/tick budgets stay unchanged.
"""
from pathlib import Path
import os

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
terrain=root/"client/V178TerrainMap.java"
s=terrain.read_text(encoding="utf-8")
anchor="public static void drawClaim(GuiGraphicsExtractor g,int x,int y,int tile,int status){"
assert s.count(anchor)==1,("B1855_CLAIM_METHOD_ANCHOR",s.count(anchor))
a=s.index(anchor)
opening=s.index("{",a)
depth=0
end=None
for i in range(opening,len(s)):
    if s[i]=="{":depth+=1
    elif s[i]=="}":
        depth-=1
        if depth==0:
            end=i+1
            break
assert end is not None
old=s[a:end]
assert "status&3" in old and "g.fill(" in old
assert "status&4" in old, "B1855_LOADED_MARKER_LOST"

new="""public static void drawClaim(GuiGraphicsExtractor g,int x,int y,int tile,int status){
   // B1855: light-blue transparent territory, like an FTB-style chunk map.
   // Terrain remains visible underneath and each 16x16 chunk has a crisp rim.
   if(tile<=0||(status&3)==0)return;
   int fill=switch(status&3){
    case 1->0x5379b4ff; // own claim: translucent ice blue
    case 2->0x486acaf2; // allied/trusted: translucent turquoise
    case 3->0x497e94d5; // foreign: muted indigo
    default->0x00000000;
   };
   int edge=switch(status&3){
    case 1->0xff4a91f5;
    case 2->0xff4fbbdf;
    case 3->0xff7884c8;
    default->0x00000000;
   };
   // Constant-cost, cached-GUI draw only; never read chunks in render.
   g.fill(x,y,x+tile,y+tile,fill);
   g.fill(x,y,x+tile,y+1,edge);
   g.fill(x,y+tile-1,x+tile,y+tile,edge);
   g.fill(x,y,x+1,y+tile,edge);
   g.fill(x+tile-1,y,x+tile,y+tile,edge);
   if((status&4)!=0&&tile>=6){
    // Retain force-load distinction without covering the blue terrain tint.
    int mark=Math.max(2,Math.min(4,tile/4));
    g.fill(x+tile-mark-1,y+1,x+tile-1,y+1+mark,0xff76eeaa);
   }
  }"""
s=s[:a]+new+s[end:]
assert s.count("B1855: light-blue transparent territory")==1
assert "g.fill(x,y,x+tile,y+tile,fill);" in s
assert s.count(anchor)==1
# Explicitly preserve the two user-visible entry points, not merely dead code.
mini=(root/"client/V178ClaimsClient.java").read_text(encoding="utf-8")
full=(root/"client/V178ClaimsMapScreen.java").read_text(encoding="utf-8")
assert "V178TerrainMap.drawClaim(" in mini, "B1855_MINIMAP_ENTRY_LOST"
assert "V178TerrainMap.drawClaim(" in full, "B1855_WORLDMAP_ENTRY_LOST"
terrain.write_text(s,encoding="utf-8")
print("B1855_V19_TRANSLUCENT_BLUE_CHUNKS_BOTH_MAPS_VISIBLE_TERRAIN_GREEN_FORCELOAD_PASS")
