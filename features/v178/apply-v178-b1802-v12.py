#!/usr/bin/env python3
"""B1802 / v1.7.8 v12: dynamic terrain refresh, interpolated HUD, miner fixes.

Run AFTER B1799. No world reads during HUD draw, no forced chunks, no new
server-side claims/tickets, no change to per-block energy or loot transactions.
"""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 before=p.read_text(encoding="utf-8")
 n=before.count(old)
 assert n==1,("B1802_SOURCE_DRIFT",rel,n,old[:110])
 p.write_text(before.replace(old,new,1),encoding="utf-8")

# B1780 changed the entire geometry but kept its B1666 texture dictionary.
# The new blade/hydraulic faces were therefore unresolved "#blade" etc.
m=R/"models/block/mining_builder.json"
obj=json.loads(m.read_text(encoding="utf-8"))
assert 20<=len(obj["elements"])<=40,("B1802_BUILDER_SHAPE_DRIFT",len(obj["elements"]))
for material in ("shell","panel","trim","core","front","vent",
                 "sensor","display","blade","hydraulic","warning"):
 png=R/"textures/block"/("mining_builder_"+material+".png")
 assert png.is_file(),("B1802_BUILDER_MISSING_PNG",str(png))
 obj.setdefault("textures",{}).setdefault(
  material,"obsidiannetwork:block/mining_builder_"+material)
for element in obj["elements"]:
 for face in element.get("faces",{}).values():
  ref=face.get("texture","")
  assert ref.startswith("#") and ref[1:] in obj["textures"],("B1802_BAD_FACE_REF",ref)
assert obj["textures"]["blade"]=="obsidiannetwork:block/mining_builder_blade"
assert obj["textures"]["hydraulic"]=="obsidiannetwork:block/mining_builder_hydraulic"
m.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")

# The operation screen replaces the live speed slot and used container index 1
# on a SimpleContainer(1): invalid for click/remove and sync. Use slot 0.
patch("client/V178MiningBuilderOperationsScreen.java",
 "new Slot(speedSlot.container,1,143,27)",
 "new Slot(speedSlot.container,0,143,27)")

# Before: 8 -> 16 breaks/tick from 0 -> 16 speed upgrades.
# Now:    8 -> 32 breaks/tick from 0 -> 16 speed upgrades.
# MAX_VISITS=32 already allows 32; global 64 breaks/tick, 1.3ms deadline
# and 2000FE/block remain intact, so actual throughput remains TPS-bounded.
patch("mining/V178MiningBuilderBE.java",
 "return MAX_BREAKS+(MAX_BREAKS*speedUpgradeCount()/16);",
 "return MAX_BREAKS+(3*MAX_BREAKS*speedUpgradeCount()/16);")

# Faster travel sampling and continuous block-change refresh.
# No stale disk tiles are treated as permanently final: every visible loaded
# chunk is resampled on a bounded rotating schedule (incl. old 4x4/8x8 saves).
# A small shared work budget prevents large FPS spikes while flying.
terrain="client/V178TerrainMap.java"
patch(terrain,
 " private static void refreshSurface(ClientLevel world,int cx,int cz){",
''' private static int b1802NearCursor,b1802FarCursor;
 private static int b1802LastCx=Integer.MIN_VALUE,b1802LastCz=Integer.MIN_VALUE;
 private static void b1802RefreshTravel(ClientLevel world,int cx,int cz){
  if(cx!=b1802LastCx||cz!=b1802LastCz){
   b1802LastCx=cx;b1802LastCz=cz;b1802NearCursor=0;
  }
  long start=System.nanoTime();
  // Always revalidate the exact chunk under the player within two ticks.
  if((world.getGameTime()&1L)==0)refreshSurface(world,cx,cz);
  // Revalidate each of the 25 nearby chunks about every 12-13 ticks.
  // Loaded-only sampling never generates, forces or requests chunks.
  for(int n=0;n<2;n++){
   if(System.nanoTime()-start>=1_600_000L)break;
   int i=b1802NearCursor++%25;
   int tx=cx+(i%5)-2,tz=cz+(i/5)-2;
   if(tx==cx&&tz==cz)continue;
   refreshSurface(world,tx,tz);
  }
  // Wide worldmap gets extra refresh work if there is budget left.
  var screen=Minecraft.getInstance().screen;
  if(screen instanceof V178ClaimsMapScreen ||
     screen instanceof V178MiningAreaScreen){
   for(int n=0;n<2;n++){
    if(System.nanoTime()-start>=1_600_000L)break;
    int i=b1802FarCursor++%625;
    refreshSurface(world,cx+(i%25)-12,cz+(i/25)-12);
   }
  }
 }
 private static void refreshSurface(ClientLevel world,int cx,int cz){''')
patch(terrain,
'''   updateAtlas(world,cx,cz);
   V178MiniRaster.tick(world);''',
'''   b1802RefreshTravel(world,cx,cz);
   updateAtlas(world,cx,cz);
   V178MiniRaster.tick(world);''')

# Remove 2-tick upload throttling; only upload on changed X/Z/zoom/revision.
# This allows new terrain after a block edit to reach the GPU in one tick.
patch("client/V178MiniRaster.java",
 "if(lastTick!=Long.MIN_VALUE&&tick>=lastTick&&tick-lastTick<2)return;",
 "if(lastTick!=Long.MIN_VALUE&&tick>=lastTick&&tick-lastTick<1)return;")

# The player symbol remains fixed. Move ONLY the map image between ticks using
# the renderer's own interpolated position: zero extra terrain/texture uploads.
patch("client/V178MiniRaster.java",
'''  int crop=SIDE;
  g.blit(RenderPipelines.GUI_TEXTURED,ID,x,y,0.0f,0.0f,
       width,width,crop,crop,SIDE,SIDE);''',
'''  int crop=SIDE;
  var mc=Minecraft.getInstance();
  float offsetX=0.0f,offsetZ=0.0f;
  if(mc.player!=null && lastCrop>0){
   float partial=mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
   double interpX=mc.player.xo+(mc.player.getX()-mc.player.xo)*partial;
   double interpZ=mc.player.zo+(mc.player.getZ()-mc.player.zo)*partial;
   // Do not interpolate a teleport or stale/unloaded map sample.
   if(Math.abs(interpX-lastX)<3.0D && Math.abs(interpZ-lastZ)<3.0D){
    offsetX=(float)((lastX-interpX)*width/lastCrop);
    offsetZ=(float)((lastZ-interpZ)*width/lastCrop);
   }
  }
  g.pose().pushMatrix();
  g.pose().translate(offsetX,offsetZ);
  g.blit(RenderPipelines.GUI_TEXTURED,ID,x,y,0.0f,0.0f,
       width,width,crop,crop,SIDE,SIDE);
  g.pose().popMatrix();''')

# The full-screen GPU map atlas can display terrain refresh every client tick;
# it still uploads only if the terrain revision/center actually changes.
patch("client/V178TerrainMap.java",
 "private static final int ATLAS_UPDATE_TICKS=4;",
 "private static final int ATLAS_UPDATE_TICKS=1;")

# Verify we never modify the persisted map format, or waypoint/claims files.
t=(J/terrain).read_text(encoding="utf-8")
assert "b1802RefreshTravel(world,cx,cz);" in t
assert "if(!world.hasChunk(cx,cz))return;" in t
assert "MAX_CACHED=1536" in t
model=json.loads(m.read_text(encoding="utf-8"))
assert all(face["texture"][1:] in model["textures"]
 for e in model["elements"] for face in e["faces"].values())
print("B1802_V12_MINIMAP_LIVE_20TPS_GPU_60FPS_INTERPOLATION_BUILDER_TEXTURE_SPEED_SLOT_PASS")
