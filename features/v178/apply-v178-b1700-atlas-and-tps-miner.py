#!/usr/bin/env python3
"""B1700: compact GPU map atlas + bounded faster mining, after all B1692 patches.

Independent xSxLabs implementation based on public API patterns, not copied FTB
Chunks or Xaero source. Built from the existing explored 16x16 per-chunk colors.
No map terrain or network queries are performed during GUI rendering.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 src=p.read_text(encoding="utf8")
 assert src.count(old)==1,("B1700_SOURCE_DRIFT",rel,old[:125],src.count(old))
 p.write_text(src.replace(old,new,1),encoding="utf8")

# Prior 16x16 slope raster used THREE getHeight calls PER pixel. Cache a
# 17x17 height grid; 289 calls, not 768, for the exact same colors and relief.
patch("client/V178TerrainMap.java",
 '''   int[] colors=new int[RES*RES];
   for(int z=0;z<RES;z++)for(int x=0;x<RES;x++){''',
 '''   int[] colors=new int[RES*RES];
   int[] heights=new int[(RES+1)*(RES+1)];
   for(int hz=0;hz<=RES;hz++)for(int hx=0;hx<=RES;hx++)
    heights[hz*(RES+1)+hx]=world.getHeight(Heightmap.Types.WORLD_SURFACE,
        (cx<<4)+hx,(cz<<4)+hz)-1;
   for(int z=0;z<RES;z++)for(int x=0;x<RES;x++){''')
patch("client/V178TerrainMap.java",
 '''    int y=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx,wz)-1;''',
 '''    int y=heights[z*(RES+1)+x];''')
patch("client/V178TerrainMap.java",
 '''    int east=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx+1,wz)-1;
    int south=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx,wz+1)-1;''',
 '''    int east=heights[z*(RES+1)+x+1];
    int south=heights[(z+1)*(RES+1)+x];''')
patch("client/V178TerrainMap.java",
 ''' private static int roundRobin;''',
 ''' private static int roundRobin;
 // Revision only changes when new 16x16 explored terrain becomes available.
 private static int atlasRevision;''')
patch("client/V178TerrainMap.java",
 '''  map.put(key,colors);dirty=true;''',
 '''  map.put(key,colors);dirty=true;atlasRevision++;''')

# Only one background raster sample per tick while the large map is open.
# Every sampled region remains full 1-block-per-pixel detail.
patch("client/V178TerrainMap.java",
 '''  for(int n=0;n<2;n++){
   int index=roundRobin++%625;''',
 '''  for(int n=0;n<1;n++){
   int index=roundRobin++%625;''')

atlas=r"""
 // One texture for 7x7 minimap chunks, one texture for 25x25 world/map GUI.
 // This replaces 12,544+ per-pixel GUI rectangles with a single atlas blit.
 private static final int ATLAS_UPDATE_TICKS=4;
 private static final int UNKNOWN_PIXEL=0xff1c2530;
 private static final class Atlas{
  final int diameter,side;
  final net.minecraft.resources.Identifier id;
  net.minecraft.client.renderer.texture.DynamicTexture texture;
  String dimension="";
  int cx=Integer.MIN_VALUE,cz,revision=Integer.MIN_VALUE;
  boolean round;
  long lastUpload=Long.MIN_VALUE;
  Atlas(int diameter,String name){
   this.diameter=diameter;side=diameter*RES;
   id=net.minecraft.resources.Identifier.fromNamespaceAndPath("obsidiannetwork",
       "runtime/"+name);
  }
  void close(){
   if(texture!=null){
    Minecraft.getInstance().getTextureManager().release(id);
    texture=null;
   }
   cx=Integer.MIN_VALUE;revision=Integer.MIN_VALUE;
   lastUpload=Long.MIN_VALUE;dimension="";
  }
  void update(ClientLevel world,int centerX,int centerZ,boolean circle){
   String dim=world.dimension().identifier().toString();
   if(!dim.equals(dimension)){close();dimension=dim;}
   long tick=world.getGameTime();
   if(texture!=null&&cx==centerX&&cz==centerZ&&revision==atlasRevision
      &&round==circle)return;
   if(lastUpload!=Long.MIN_VALUE&&tick>=lastUpload
      &&tick-lastUpload<ATLAS_UPDATE_TICKS)return;
   if(texture==null){
    texture=new net.minecraft.client.renderer.texture.DynamicTexture(
        ()->"xSxLabs explored terrain atlas",
        new com.mojang.blaze3d.platform.NativeImage(side,side,false));
    Minecraft.getInstance().getTextureManager().register(id,texture);
   }
   var img=texture.getPixels();
   if(img==null)return;
   int radius=side/2;
   long radius2=(long)(radius-1)*(radius-1);
   for(int dz=0;dz<diameter;dz++)for(int dx=0;dx<diameter;dx++){
    int[] tile=pixels(world,centerX+dx-diameter/2,
                     centerZ+dz-diameter/2);
    for(int y=0;y<RES;y++)for(int x=0;x<RES;x++){
     int xx=dx*RES+x, yy=dz*RES+y;
     int color=tile==null?UNKNOWN_PIXEL:tile[y*RES+x];
     if(circle){
      long xx2=(long)(2*xx+1-side),yy2=(long)(2*yy+1-side);
      if(xx2*xx2+yy2*yy2>radius2*4)color=0;
     }
     img.setPixel(xx,yy,color);
    }
   }
   texture.upload();
   cx=centerX;cz=centerZ;revision=atlasRevision;
   round=circle;lastUpload=tick;
  }
  void draw(GuiGraphicsExtractor g,int centerX,int centerZ,
            int ox,int oy,int step,boolean circle){
   int width=diameter*step;
   if(texture==null||cx!=centerX||cz!=centerZ||round!=circle){
    g.fill(ox,oy,ox+width,oy+width,UNKNOWN_PIXEL);
    return;
   }
   g.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED,
        id,ox,oy,0.0f,0.0f,width,width,side,side);
  }
 }
 private static final Atlas MINI_ATLAS=new Atlas(7,"minimap_gpu_atlas");
 private static final Atlas WORLD_ATLAS=new Atlas(25,"worldmap_gpu_atlas");
 private static void resetAtlas(){MINI_ATLAS.close();WORLD_ATLAS.close();}
 private static void updateAtlas(ClientLevel world,int cx,int cz){
  var mc=Minecraft.getInstance();
  boolean big=mc.screen instanceof V178ClaimsMapScreen ||
              mc.screen instanceof V178MiningAreaScreen;
  if(big)WORLD_ATLAS.update(world,cx,cz,false);
  else if(V178ClaimsClient.option("minimap"))
   MINI_ATLAS.update(world,cx,cz,V178MiniPreferences.circle());
 }
 public static void drawViewport(ClientLevel world,GuiGraphicsExtractor g,
      int cx,int cz,int ox,int oy,int step,int diameter,boolean circular){
  if(world==null)return;
  if(diameter==7)MINI_ATLAS.draw(g,cx,cz,ox,oy,step,circular);
  else if(diameter==25)WORLD_ATLAS.draw(g,cx,cz,ox,oy,step,false);
 }
"""
patch("client/V178TerrainMap.java",
 ''' public static void draw(ClientLevel world,GuiGraphicsExtractor g,''',
 atlas+''' public static void draw(ClientLevel world,GuiGraphicsExtractor g,''')
patch("client/V178TerrainMap.java",
 '''   sample(world,cx+(index%11)-5,cz+(index/11)-5);''',
 '''   sample(world,cx+(index%11)-5,cz+(index/11)-5);
   updateAtlas(world,cx,cz);''')
patch("client/V178TerrainMap.java",
 '''  mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;''',
 '''  mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;
  resetAtlas();atlasRevision=0;''')
patch("client/V178TerrainMap.java",
 '''   dirty=false;mapIdentity=next;mapDimension=dim;lastFlushTick=Long.MIN_VALUE;''',
 '''   resetAtlas();atlasRevision=0;
   dirty=false;mapIdentity=next;mapDimension=dim;lastFlushTick=Long.MIN_VALUE;''')

# The native original 7x7 minimap loop remains for claim/waypoint/player
# overlays only. Terrain is one opaque/round masked GPU quad.
patch("client/V178ClaimsClient.java",
 '''   for(int dz=-3;dz<=3;dz++)for(int dx=-3;dx<=3;dx++){''',
 '''   if(drawTerrain)V178TerrainMap.drawViewport(mc.level,g,cx,cz,
      ox+4,oy+15,step,7,V178MiniPreferences.circle());
   for(int dz=-3;dz<=3;dz++)for(int dx=-3;dx<=3;dx++){''')
patch("client/V178ClaimsClient.java",
 '''if(drawTerrain)V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,step);''',
 '''if(drawTerrain){} // B1700 GPU atlas drawn before status overlays.''')

# Full-screen FTB-style claim map: same 25x25 cached terrain, ONE quad,
# followed by the unchanged server-authoritative claims/load overlays.
patch("client/V178ClaimsMapScreen.java",
 '''   for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){''',
 '''   if(showTerrain)V178TerrainMap.drawViewport(world,g,cx,cz,
       x0,y0,tile,DIAMETER,false);
   for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){''')
patch("client/V178ClaimsMapScreen.java",
 '''if(showTerrain)V178TerrainMap.draw(world,g,cxWorld,czWorld,px,py,tile);''',
 '''if(showTerrain){} // B1700 full 25x25 terrain atlas rendered above.''')

# Mining-selection map shares the exact same raster without extra world work.
patch("client/V178MiningAreaScreen.java",
 '''    for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){''',
 '''    V178TerrainMap.drawViewport(mc.level,g,cx,cz,x0,y0,t,DIAMETER,false);
    for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){''')
patch("client/V178MiningAreaScreen.java",
 '''      V178TerrainMap.draw(mc.level,g,wx,wz,px,py,t);''',
 '''      // B1700 terrain already blitted as a single GPU atlas.''')

# Make the 16x16 samples actually readable: normal => one GUI pixel per
# world block. The current tiny map compressed 16 columns into only 12 px.
patch("client/V178MiniPreferences.java",
 '''case 0->10;case 2->16;default->12;''',
 '''case 0->12;case 2->20;default->16;''')

# Bounded throughput improvement: from 2 to 8 mined blocks per machine tick,
# but with a shared per-world 1.3ms wall-clock deadline and the unchanged
# maximum 64 global breaks/tick. Stops automatically when the tick is busy;
# no worker threads, concurrent world modification, forced chunks or extra FE.
patch("mining/V178MiningBuilderBE.java",
 '''public static final int MAX_VISITS=8,MAX_BREAKS=2;''',
 '''public static final int MAX_VISITS=32,MAX_BREAKS=8;
 private static final long GLOBAL_MINER_TIME_BUDGET_NS=1_300_000L;''')
patch("mining/V178MiningBuilderBE.java",
 '''  int remain=GLOBAL_BLOCK_BUDGET;''',
 '''  int remain=GLOBAL_BLOCK_BUDGET;
  long deadline;''')
patch("mining/V178MiningBuilderBE.java",
 ''' private static boolean budget(ServerLevel world){
  TickBudget t=BUDGETS.computeIfAbsent(world,k->new TickBudget());
  long tick=world.getGameTime();
  if(t.tick!=tick){t.tick=tick;t.remain=GLOBAL_BLOCK_BUDGET;}
  if(t.remain<=0)return false;
  --t.remain;return true;
 }''',
 ''' private static boolean canMineThisTick(ServerLevel world){
  TickBudget t=BUDGETS.computeIfAbsent(world,k->new TickBudget());
  long tick=world.getGameTime();
  if(t.tick!=tick){
   t.tick=tick;t.remain=GLOBAL_BLOCK_BUDGET;
   t.deadline=System.nanoTime()+GLOBAL_MINER_TIME_BUDGET_NS;
  }
  return t.remain>0&&System.nanoTime()<t.deadline;
 }
 private static boolean budget(ServerLevel world){
  if(!canMineThisTick(world))return false;
  --BUDGETS.get(world).remain;return true;
 }''')
patch("mining/V178MiningBuilderBE.java",
 '''   if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;
   // Read-only loot calculation.''',
 '''   if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;
   if(!canMineThisTick(world))return; // skip loot work if TPS budget is exhausted
   // Read-only loot calculation.''')

# If subsequent B1692 text altered the old comment, anchor here instead.
# The conditional code above must target the same one-time transaction path.
assert "GLOBAL_MINER_TIME_BUDGET_NS" in (J/"mining/V178MiningBuilderBE.java").read_text()
assert "drawViewport" in (J/"client/V178ClaimsClient.java").read_text()
assert "img.setPixel(xx,yy,color)" in (J/"client/V178TerrainMap.java").read_text()
print("B1700_GPU_ATLAS_1_QUAD_16PIX_CLIENT_TICK_SAMPLING_TPS_BOUNDED_8_BREAKS_PASS")
