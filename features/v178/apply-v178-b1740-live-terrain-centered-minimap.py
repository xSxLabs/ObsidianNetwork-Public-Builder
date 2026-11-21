#!/usr/bin/env python3
"""B1740: repair stale snow/earth terrain, player-centered detailed circular map,
wide zoom-out, proportional positional information and skin arrow. Apply AFTER
B1730. The terrain raster uses ONLY existing 16x16 explored chunk arrays on
the client tick and never accesses the world during GUI rendering.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel,old,new,n=1):
    p=J/rel
    s=p.read_text("utf8")
    count=s.count(old)
    if count!=n:
        # Only tolerate source indentation drift, never changed expressions.
        rows=[line.strip() for line in old.splitlines()]
        pattern=r"(?m)^[ \t]*"+r"[ \t]*\r?\n[ \t]*".join(re.escape(x) for x in rows)
        matches=list(re.finditer(pattern,s))
        assert n==1 and len(matches)==1,("B1740_ANCHOR",rel,old[:100],count,len(matches))
        m=matches[0]
        s=s[:m.start()]+new+s[m.end():]
    else:s=s.replace(old,new,n)
    p.write_text(s,"utf8")

def insert(rel,anchor,addition):
    patch(rel,anchor,addition+anchor)

def emit(rel,java):
    p=J/rel
    assert not p.exists(),("B1740_DUPLICATE",rel)
    p.write_text(java,"utf8")

# Full visible zoom-out goes to 19 chunks wide (304 Minecraft blocks).
# Unlike the earlier 7-chunk atlas crop, this has actual distant cached tiles.
prefs="client/V178MiniPreferences.java"
patch(prefs,'fineZoom=Math.max(100,Math.min(200,fineZoom));',
            'fineZoom=Math.max(30,Math.min(300,fineZoom));')
patch(prefs,'fineZoom=Math.max(100,Math.min(200,fineZoom+delta));',
            'fineZoom=Math.max(30,Math.min(300,fineZoom+delta));')
patch(prefs,'''public static int cropPixels(){ensure();return Math.max(16,
       visibleChunks()*16*100/fineZoom);}''',
'''public static int cropPixels(){ensure();return Math.max(16,
       Math.min(19*16,visibleChunks()*16*100/fineZoom));}''')

# Expose a revision for the lightweight crop raster and resample existing
# loaded terrain around the player after terraforming. Previously a chunk was
# sampled once and stayed SNOW forever even after uncovered DIRT was visible.
terrain="client/V178TerrainMap.java"
insert(terrain,''' private static int atlasRevision;''',
''' private static int liveRefreshCursor;
 public static int terrainRevision(){return atlasRevision;}
''')
# Do not touch original disk serialization, 16x16 resolution, cache ownership,
# dimension reset or mining builder. Revalidate 1 loaded chunk / 10 ticks.
# Mark atlas dirty ONLY when an actual 16x16 tile differs.
patch(terrain,'''   updateAtlas(world,cx,cz);''',
'''   if(world.getGameTime()%10L==0L){
    int index=(liveRefreshCursor++ + 12)%25;
    int rx=cx+(index%5)-2,rz=cz+(index/5)-2;
    if(world.hasChunk(rx,rz)){
     var previousMap=cache(world.dimension().identifier().toString());
     long key=pos(rx,rz);
     int[] previous=previousMap.remove(key);
     int oldRevision=atlasRevision;
     sample(world,rx,rz);
     int[] refreshed=previousMap.get(key);
     if(previous!=null&&java.util.Arrays.equals(previous,refreshed)){
      previousMap.put(key,previous);
      atlasRevision=oldRevision;
     }
    }
   }
   updateAtlas(world,cx,cz);
   V178MiniRaster.tick(world);
   V178MapInfo.tick(world);''')
# Common coarse_dirt and exposed soil must be distinguishable from snow.
patch(terrain,'''   else if(state.is(net.minecraft.world.level.block.Blocks.DIRT_PATH))
     color=0xa69770;''',
'''   else if(state.is(net.minecraft.world.level.block.Blocks.DIRT))
     color=0x96704d;
   else if(state.is(net.minecraft.world.level.block.Blocks.COARSE_DIRT))
     color=0x856243;
   else if(state.is(net.minecraft.world.level.block.Blocks.ROOTED_DIRT))
     color=0x775944;
   else if(state.is(net.minecraft.world.level.block.Blocks.FARMLAND))
     color=0x755136;
   else if(state.is(net.minecraft.world.level.block.Blocks.MUD))
     color=0x4f5156;
   else if(state.is(net.minecraft.world.level.block.Blocks.DIRT_PATH))
     color=0xa69770;''')
# Keep the previous full-screen map atlas untouched. The small minimap is
# rasterized from cached tiles into its own round 304x304 GPU image on demand.
patch(terrain,'''    MINI_ATLAS.draw(g,cx,cz,ox,oy,step,circular);''',
'''    V178MiniRaster.draw(g,ox,oy,diameter*step);''')
# Existing MINIMAP atlas is redundant now; avoid its 7x7 uploads.
patch(terrain,'''   else if(V178ClaimsClient.option("minimap"))
    MINI_ATLAS.update(world,cx,cz,V178MiniPreferences.circle());''',
'''   // B1740 circular minimap uses V178MiniRaster's cached view instead.''')

emit("client/V178MiniRaster.java",r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;
import com.mojang.blaze3d.platform.NativeImage;

/** B1740 client-only explored map raster: no world block/height/chunk reads
 * in rendering. One 304px square GPU texture, updated only after movement,
 * zoom or actual terrain cache revisions; maximum once per two client ticks.
 */
public final class V178MiniRaster{
 private V178MiniRaster(){}
 private static final int SIDE=19*16,UNKNOWN=0xff1c2530;
 private static final Identifier ID=Identifier.fromNamespaceAndPath(
    "obsidiannetwork","runtime/centered_minimap");
 private static DynamicTexture texture;
 private static String dimension="";
 private static int lastX=Integer.MIN_VALUE,lastZ,lastCrop,lastRevision=-1;
 private static boolean lastCircle;
 private static long lastTick=Long.MIN_VALUE;
 private static boolean valid;
 public static void reset(){
  if(texture!=null){Minecraft.getInstance().getTextureManager().release(ID);texture=null;}
  dimension="";valid=false;lastX=Integer.MIN_VALUE;lastRevision=-1;
  lastTick=Long.MIN_VALUE;
 }
 public static void tick(ClientLevel world){
  var mc=Minecraft.getInstance();
  if(world==null||mc.player==null||mc.screen!=null||
     !V178ClaimsClient.option("minimap")||!V178ClaimsClient.option("terrain"))
   return;
  String dim=world.dimension().identifier().toString();
  if(!dim.equals(dimension)){reset();dimension=dim;}
  int x=mc.player.blockPosition().getX(),z=mc.player.blockPosition().getZ();
  int crop=V178MiniPreferences.cropPixels(),rev=V178TerrainMap.terrainRevision();
  boolean round=V178MiniPreferences.circle();
  if(valid&&x==lastX&&z==lastZ&&crop==lastCrop&&rev==lastRevision
     &&round==lastCircle)return;
  long tick=world.getGameTime();
  if(lastTick!=Long.MIN_VALUE&&tick>=lastTick&&tick-lastTick<2)return;
  lastTick=tick;
  if(texture==null){
   texture=new DynamicTexture(()->"xSxLabs live minimap",
          new NativeImage(SIDE,SIDE,false));
   mc.getTextureManager().register(ID,texture);
  }
  var img=texture.getPixels();if(img==null)return;
  int startX=x-crop/2,startZ=z-crop/2;
  int firstCX=startX>>4,firstCZ=startZ>>4;
  int chunksX=((startX+crop-1)>>4)-firstCX+1;
  int chunksZ=((startZ+crop-1)>>4)-firstCZ+1;
  int[][] tiles=new int[chunksX*chunksZ][];
  for(int zz=0;zz<chunksZ;zz++)for(int xx=0;xx<chunksX;xx++)
   tiles[zz*chunksX+xx]=V178TerrainMap.pixels(world,firstCX+xx,firstCZ+zz);
  double radius=(crop-1)*0.5,inner=radius-1.25;
  double outer2=radius*radius,inner2=inner*inner;
  for(int py=0;py<crop;py++)for(int px=0;px<crop;px++){
   int wx=startX+px,wz=startZ+py;
   int[] tile=tiles[((wz>>4)-firstCZ)*chunksX+((wx>>4)-firstCX)];
   int color=tile==null?UNKNOWN:tile[(wz&15)*16+(wx&15)];
   if(round){
    double dx=px+0.5-crop*0.5,dz=py+0.5-crop*0.5;
    double distance=dx*dx+dz*dz;
    if(distance>outer2)color=0;
    else if(distance>=inner2)color=0xff95adbc;
   }
   img.setPixel(px,py,color);
  }
  texture.upload();
  valid=true;lastX=x;lastZ=z;lastCrop=crop;lastRevision=rev;
  lastCircle=round;
 }
 public static void draw(GuiGraphicsExtractor g,int x,int y,int width){
  if(!valid||texture==null)return;
  int crop=lastCrop;
  g.blit(RenderPipelines.GUI_TEXTURED,ID,x,y,0.0f,0.0f,
       width,width,crop,crop,SIDE,SIDE);
 }
}
''')

# Cache biome name at the same bounded client tick, never during rendering.
emit("client/V178MapInfo.java",r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import java.util.Locale;

public final class V178MapInfo{
 private V178MapInfo(){}
 private static String biome="Unknown",dimension="";
 private static long nextTick=Long.MIN_VALUE;
 public static void tick(ClientLevel level){
  var p=Minecraft.getInstance().player;
  if(level==null||p==null)return;
  String dim=level.dimension().identifier().toString();
  long now=level.getGameTime();
  if(dim.equals(dimension)&&now>=0&&now<nextTick)return;
  dimension=dim;nextTick=now+40;
  biome=level.getBiome(p.blockPosition()).unwrapKey()
     .map(key->key.identifier().getPath()).orElse("Unknown");
  String[] words=biome.replace('_',' ').split(" ");
  StringBuilder display=new StringBuilder();
  for(String word:words){
   if(word.isEmpty())continue;
   if(!display.isEmpty())display.append(' ');
   display.append(word.substring(0,1).toUpperCase(Locale.ROOT))
          .append(word.substring(1));
  }
  biome=display.toString();
 }
 public static String biome(){return biome;}
 public static void line(GuiGraphicsExtractor g,String value,int x,int y){
  var mc=Minecraft.getInstance();
  float scale=Math.max(.65f,Math.min(1.6f,V178MiniPreferences.step()/24.0f));
  scale=Math.min(scale,Math.max(.35f,
      (7f*V178MiniPreferences.step()-8f)/Math.max(1,mc.font.width(value))));
  g.pose().pushMatrix();
  g.pose().translate(x,y);
  g.pose().scale(scale,scale);
  g.text(mc.font,value,0,0,0xfff4f6fa);
  g.pose().popMatrix();
 }
}
''')

# Correct the player marker for EVERY map size: a white direction arrow,
# real Minecraft skin face+hat and a thin dark outline. Drawn in the center.
markers="client/V178MapMarkers.java"
p=J/markers
s=p.read_text("utf8")
method=re.search(r'(?m)^[ \\t]*public static void player\\(',s)
assert method,("B1740_MARKER_METHOD_MISSING",)
a=method.start()
b=s.index("\n }\n}",a)
assert b>a,("B1740_MARKER_METHOD_END",a,b)
s=s[:a]+r'''  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
   double heading=Math.toRadians(yaw);
   double dx=-Math.sin(heading),dy=Math.cos(heading);
   // White directional arrow extends beyond the player's 8px face.
   int tipX=x+(int)Math.round(dx*10),tipY=y+(int)Math.round(dy*10);
   for(int t=0;t<6;t++){
    int mx=tipX-(int)Math.round(dx*t),my=tipY-(int)Math.round(dy*t);
    int r=t<2?t+1:t<4?3:1;
    for(int v=-r;v<=r;v++){
     int xx=mx+(int)Math.round(-dy*v),yy=my+(int)Math.round(dx*v);
     g.fill(xx-1,yy-1,xx+2,yy+2,0xff092432);
     g.fill(xx,yy,xx+1,yy+1,0xffffffff);
    }
   }
   g.fill(x-5,y-5,x+5,y+5,0xff071824);
   var mc=net.minecraft.client.Minecraft.getInstance();
   if(mc.player==null){
    g.fill(x-4,y-4,x+4,y+4,0xffffffff);
    return;
   }
   net.minecraft.client.gui.components.PlayerFaceExtractor.extractRenderState(
       g,mc.player.getSkin(),x-4,y-4,8);
  }'''+s[b+3:]
p.write_text(s,"utf8")

# Keep center marker immovable, move terrain and overlays around actual XYZ.
client="client/V178ClaimsClient.java"
patch(client,'''     int px=ox+4+7*step/2+
          (Math.floorMod(mc.player.blockPosition().getX(),16)-8)*markerStep/16;
      int py=oy+15+7*step/2+
          (Math.floorMod(mc.player.blockPosition().getZ(),16)-8)*markerStep/16;''',
'''     int px=ox+4+7*step/2;
      int py=oy+15+7*step/2;''')
patch(client,'''     int x=ox+4+7*step/2+dx*markerStep-markerStep/2;
      int y=oy+15+7*step/2+dz*markerStep-markerStep/2;''',
'''     int x=ox+4+7*step/2+dx*markerStep-
         Math.floorMod(mc.player.blockPosition().getX(),16)*markerStep/16;
      int y=oy+15+7*step/2+dz*markerStep-
         Math.floorMod(mc.player.blockPosition().getZ(),16)*markerStep/16;''')
patch(client,'''for(int dz=-radius;dz<=radius;dz++)for(int dx=-radius;dx<=radius;dx++){''',
'''int claimRadius=Math.min(10,Math.max(radius,
       V178MiniPreferences.cropPixels()/32+2));
   for(int dz=-claimRadius;dz<=claimRadius;dz++)
    for(int dx=-claimRadius;dx<=claimRadius;dx++){''')
# Map's title was duplicating XYZ and using a font larger than the info.
patch(client,'''g.text(mc.font,option("coords")?
     "X: "+mc.player.blockPosition().getX()+" Y: "+mc.player.blockPosition().getY()+
     " Z: "+mc.player.blockPosition().getZ():"xSxLabs MAP",
     ox+3,oy+2,0xffb2ecfa);''',
'''// B1740: No duplicate oversized XYZ header; compact rows follow the map.''')
patch(client,'''int infoRows=(option("coords")?2:0)+(option("chunk")?1:0)
      +(option("daytime")?1:0);''',
'''int infoRows=(option("coords")?1:0)+(option("biome")?1:0)
      +(option("chunk")?1:0)+(option("daytime")?1:0);''')
patch(client,'''int miniWidth=7*step+7,miniHeight=7*step+20+infoRows*10,miniCorner=1;''',
'''int lineHeight=Math.max(9,Math.round(step*.44f));
   int miniWidth=7*step+7,miniHeight=7*step+20+infoRows*lineHeight,miniCorner=1;''')
patch(client,'''int oy=V178HudLayout.y(miniCorner,mc.getWindow().getGuiScaledHeight(),miniHeight);''',
'''int oy=V178HudLayout.y(miniCorner,mc.getWindow().getGuiScaledHeight(),miniHeight);
   // Lower corners: reserve space ABOVE the map, upper corners: BELOW.
   if(miniCorner>=2)oy+=infoRows*lineHeight;''')
patch(client,'''   int infoY=oy+7*step+22;''',
'''   int infoY=miniCorner>=2?oy-infoRows*lineHeight+5:oy+7*step+20;''')
patch(client,'''   if(option("coords")){
    g.text(mc.font,"X "+pos.getX()+" Y "+pos.getY(),ox+3,infoY,0xffcce8f6);
    infoY+=10;
    g.text(mc.font,"Z "+pos.getZ(),ox+3,infoY,0xffcce8f6);
    infoY+=10;
   }
   if(option("chunk")){
    g.text(mc.font,"Chunk "+cx+", "+cz,ox+3,infoY,0xffcce8f6);
    infoY+=10;
   }
   if(option("daytime")){
    g.text(mc.font,"Day "+(mc.level.getGameTime()/24000L),ox+3,infoY,0xffcce8f6);
   }''',
'''   if(option("coords")){
    V178MapInfo.line(g,"Player Pos: "+pos.getX()+" "+pos.getY()+" "+pos.getZ(),
        ox+4,infoY);infoY+=lineHeight;
   }
   if(option("biome")){
    V178MapInfo.line(g,"Biome: "+V178MapInfo.biome(),ox+4,infoY);
    infoY+=lineHeight;
   }
   if(option("chunk")){
    V178MapInfo.line(g,"Chunk: "+cx+" "+cz,ox+4,infoY);
    infoY+=lineHeight;
   }
   if(option("daytime")){
    V178MapInfo.line(g,"Day: "+(mc.level.getDayTime()/24000L),ox+4,infoY);
   }''')
# Player-follow marker projections: server snapshot stays chunk-oriented, but
# mob/waypoint HUD icons must share the same player-following local origin.
patch("client/V178MapMobCache.java",
'''   int x=left+7*step/2+(dx*16+Math.floorMod(m.x(),16)-8)*tile/16;
    int y=top+7*step/2+(dz*16+Math.floorMod(m.z(),16)-8)*tile/16;''',
'''   var player=Minecraft.getInstance().player;
    if(player==null)continue;
    int x=left+7*step/2+(dx*16+Math.floorMod(m.x(),16)-
         Math.floorMod(player.blockPosition().getX(),16))*tile/16;
    int y=top+7*step/2+(dz*16+Math.floorMod(m.z(),16)-
         Math.floorMod(player.blockPosition().getZ(),16))*tile/16;''')
patch("client/V178Waypoints.java",
'''   int x=ox+7*step/2+(dx*16)*tile/16;
    int y=oy+7*step/2+(dz*16)*tile/16;''',
'''   var player=Minecraft.getInstance().player;
    if(player==null)continue;
    int x=ox+7*step/2+(dx*16+8-
          Math.floorMod(player.blockPosition().getX(),16))*tile/16;
    int y=oy+7*step/2+(dz*16+8-
          Math.floorMod(player.blockPosition().getZ(),16))*tile/16;''')

# Biome is independently editable like every other map information row.
patch(client,'''"coords","chunk","daytime","map_terrain","map_claims",''',
            '''"coords","biome","chunk","daytime","map_terrain","map_claims",''')
patch(client,'''!key.equals("coords")&&!key.equals("chunk")&&!key.equals("daytime")''',
            '''!key.equals("coords")&&!key.equals("chunk")&&!key.equals("daytime")''')
# Default biome on, no extra packet or server work.
settings="client/V178MapSettingsScreen.java"
patch(settings,'''{"minimap","terrain","claims","loaded","waypoints","player","coords","chunk","daytime"},''',
'''{"minimap","terrain","claims","loaded","waypoints","player","coords","biome","chunk","daytime"},''')
patch(settings,''' "Waypoints","Player Arrow","XYZ Coordinates","Chunk Coordinates","Game Day"},''',
''' "Waypoints","Player Arrow","XYZ Coordinates","Biome","Chunk Coordinates","Game Day"},''')
# Dynamic settings layout was previously fixed to 9 rows; 10 toggles are two
# columns x five rows, same height. The existing 4 size/zoom controls remain.

assert "V178MiniRaster.draw" in (J/terrain).read_text()
assert "V178MapInfo.line" in (J/client).read_text()
assert "Math.floorMod(mc.player.blockPosition().getX(),16)*markerStep/16" in (J/client).read_text()
assert "new NativeImage(SIDE,SIDE,false)" in (J/"client/V178MiniRaster.java").read_text()
print("B1740_LIVE_DIRT_SNOW_REVALIDATION_CENTERED_19CHUNK_MINIMAP_PLAYER_SKIN_TEXT_PASS")
