#!/usr/bin/env python3
"""B1804, v1.7.8 v13: loaded terrain revalidation, guaranteed builder model
faces, compact player pointer, user-controlled FlyModule wheel entry.

Keeps the exact same terrain disk format, waypoints and claims. Loaded-only
world reads on client ticks, no forced chunks or render-frame block sampling.
"""
import json, os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 n=s.count(old)
 assert n==1,("B1804_V13_SOURCE_DRIFT",rel,n,old[:130])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# 1. Revalidate what the client ACTUALLY sees. A persisted explored tile is
# never an authoritative final terrain snapshot. The current loaded chunk is
# checked every tick; surrounding loaded chunks rotate with an elapsed CPU cap.
# No new network packets, server hooks, generation, forced loads, file deletion.
terrain="client/V178TerrainMap.java"
patch(terrain,
 "if((world.getGameTime()&1L)==0)refreshSurface(world,cx,cz);",
 "refreshSurface(world,cx,cz);")
patch(terrain,
'''  for(int n=0;n<2;n++){
   if(System.nanoTime()-start>=1_600_000L)break;
   int i=b1802NearCursor++%25;''',
'''  for(int n=0;n<4;n++){
   if(System.nanoTime()-start>=1_600_000L)break;
   int i=b1802NearCursor++%25;''')
patch(terrain,
'''   for(int n=0;n<2;n++){
    if(System.nanoTime()-start>=1_600_000L)break;
    int i=b1802FarCursor++%625;''',
'''   // Also recheck the player's chunk if the fullscreen map has been panned.
   var mc=Minecraft.getInstance();
   if(mc.player!=null){
    var playerPos=mc.player.blockPosition();
    int pcx=playerPos.getX()>>4,pcz=playerPos.getZ()>>4;
    if(pcx!=cx||pcz!=cz)refreshSurface(world,pcx,pcz);
   }
   for(int n=0;n<4;n++){
    if(System.nanoTime()-start>=1_600_000L)break;
    int i=b1802FarCursor++%625;''')
# A *changed* sampled tile already increments atlasRevision in sample(), which
# drives both the worldmap atlas and the centered minimap GPU image. Keep the
# legacy pixel comparison and disk persistence, but make their linkage explicit.
java=(J/terrain).read_text(encoding="utf-8")
for token in ("java.util.Arrays.equals(before,after)",
              "atlasRevision=revisionBefore",
              "if(!world.hasChunk(cx,cz))return;",
              "b1802RefreshTravel(world,cx,cz);",
              "updateAtlas(world,cx,cz);",
              "V178MiniRaster.tick(world);",
              "private static final int ATLAS_UPDATE_TICKS=1;"):
 assert token in java,("B1804_TERRAIN_LINK_MISSING",token)

# 2. The B1792 model occlusion pass made 2 power-tube model elements have
# ZERO faces (both remained in the final v12 JAR). Restore the authored full
# six-sided geometry for this one machine model only. The change is bounded to
# 26 baked cuboids, not a dynamic or tick-time BlockEntityRenderer.
modelPath=R/"models/block/mining_builder.json"
model=json.loads(modelPath.read_text(encoding="utf-8"))
assert len(model["elements"])==26,("B1804_BUILDER_GEOMETRY_DRIFT",len(model["elements"]))
directions=("north","south","east","west","up","down")
restored=0
for element in model["elements"]:
 faces=element.get("faces",{})
 if not faces:
  # These two known tubes lost all faces in the B1792 optimization.
  assert element["from"][1:]==[5,6] and element["to"][1:]==[10,11]
  assert element["from"][0] in (0.3,14.3)
  material="#core"
  restored+=1
 else:
  materials={face.get("texture") for face in faces.values()}
  assert len(materials)==1,("B1804_MULTIMATERIAL_ELEMENT",materials)
  material=next(iter(materials))
 assert isinstance(material,str) and material.startswith("#")
 assert material[1:] in model["textures"]
 element["faces"]={side:{"texture":material} for side in directions}
assert restored==2,("B1804_MISSING_TUBE_COUNT",restored)
for key,asset in model["textures"].items():
 assert asset.startswith("obsidiannetwork:block/"),("B1804_BAD_TEX_LOCATION",key,asset)
 png=R/"textures"/(asset.split(":",1)[1]+".png")
 assert png.is_file() and png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"),("B1804_MISSING_PNG",str(png))
state=json.loads((R/"blockstates/mining_builder.json").read_text(encoding="utf-8"))
assert set(state["variants"])=={f"facing={d}" for d in ("north","south","east","west")}
for data in state["variants"].values():
 assert data["model"]=="obsidiannetwork:block/mining_builder"
# BaseEntityBlock has a registered facing property; don't change placement.
block=(J/"mining/V178MiningBuilderBlock.java").read_text(encoding="utf-8")
assert "FACING" in block and "getStateForPlacement" in block
modelPath.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")

# 3. White direction arrow + REAL player skin face, at a fraction of the v12
# footprint. Keep legacy B1780 marker IDs for dependent tests/HUD callers.
marker="client/V178MapMarkers.java"
src=(J/marker).read_text(encoding="utf-8")
start="  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){"
assert src.count(start)==1
i=src.index(start)
j=src.index("\n  }\n}",i)
old=src[i:j+4]
assert "B1780_COMPACT_SKIN_ARROW" in old
new=r'''  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
   // B1765_DIRECTION_ARROW / B1775_WHITE_HEAD_POINTER / B1780_COMPACT_SKIN_ARROW / B1804_SMALL_POINTER
   double heading=Math.toRadians(yaw);
   double dx=-Math.sin(heading),dy=Math.cos(heading);
   double ax=-dy,ay=dx;
   // Narrow white pointer, 6px in front of the player's centered skin.
   for(int t=3;t<=6;t++){
    int wing=t==3?1:0;
    for(int w=-wing;w<=wing;w++){
     int px=x+(int)Math.round(dx*t+ax*w);
     int py=y+(int)Math.round(dy*t+ay*w);
     g.fill(px-1,py-1,px+2,py+2,0xff091923);
     g.fill(px,py,px+1,py+1,0xffffffff);
    }
   }
   // 4px original player face + 1px border; center remains stationary.
   g.fill(x-3,y-3,x+3,y+3,0xff091923);
   var mc=net.minecraft.client.Minecraft.getInstance();
   if(mc.player==null){g.fill(x-2,y-2,x+2,y+2,0xffffffff);return;}
   net.minecraft.client.gui.components.PlayerFaceExtractor.extractRenderState(
       g,mc.player.getSkin(),x-2,y-2,4);
  }'''
assert old.endswith("  }")
src=src[:i]+new+src[j+4:]
(J/marker).write_text(src,encoding="utf-8")

# 4. The settings "FlyModule SHOW" should control visibility directly.
# Before, withFly() dropped action 11 if the *current* equipped suit was not
# available, BEFORE the saved visible/hidden preference filter ran. Always
# add the item; the existing customize() removes it only when HIDE was chosen.
fly="client/V178FlyModuleClient.java"
patch(fly,
 "if(!available())return wheel;",
 "// B1804: wheel visibility is user-controlled; server still authorizes flight.")
patch(fly,
 "if(available()&&mc.player!=null&&mc.player.connection!=null)",
 """if(mc.player==null||mc.player.connection==null)return;
   if(!available())return; // Wheel says FLY LOCKED; no unauthorized command.""")
wheel="client/NetworkActionWheelClient.java"
patch(wheel,
'''i==11?(V178FlyModuleClient.active()?"FLY OFF":"FLY ON"):i==12?"WHEEL SETTINGS":ACTIONS[i];''',
'''i==11?(V178FlyModuleClient.available()?
       (V178FlyModuleClient.active()?"FLY OFF":"FLY ON"):"FLY LOCKED"):
       i==12?"WHEEL SETTINGS":ACTIONS[i];''')
pref=(J/"client/V178WheelPreferences.java").read_text(encoding="utf-8")
assert "for(int action:original)if(enabled(action))" in pref
assert "if(!hidden.add(action))hidden.remove(action);" in pref
assert "filtered[count++]=12;" in pref

print("B1804_V13_TERRAIN_CONTINUOUS_LOADED_RESAMPLE_BUILDER_VALID_FACES_SMALL_SKIN_FLY_SHOWN_PASS")
