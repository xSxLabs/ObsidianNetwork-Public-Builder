#!/usr/bin/env python3
"""v1.7.8 independent terrain map, minimap, full-screen native GUI.

Replicates the documented FTB Chunks mouse/keyboard interactions with wholly
original code and a cache of only already-loaded client chunks. No worldgen,
no terrain packets, no per-frame world scans or server processing in render.
Execute AFTER apply-v178-ftb-batch.py.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def rep(s,old,new):
 assert s.count(old)==1,("V178_FTB_GUI_SOURCE_DRIFT",old[:100],s.count(old))
 return s.replace(old,new,1)

terrain=root/"client/V178TerrainMap.java"
assert not terrain.exists(),"V178_TERRAIN_DUPLICATE"
terrain.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.levelgen.Heightmap;
import java.util.*;

/** Lightweight explored-terrain map: 4x4 surface samples per loaded chunk.
 *  Surface reads ONLY in client tick (max 2 chunks / tick), never in rendering.
 *  1536 sampled chunks maximum per dimension (around 100 KiB of colors).
 *  No chunk generation, no client->server map data traffic.
 */
public final class V178TerrainMap {
 private V178TerrainMap(){}
 public static final int RES=4;
 private static final int MAX_CACHED=1536;
 private static final Map<String,LinkedHashMap<Long,int[]>> COLORS=new HashMap<>();
 private static final int UNKNOWN=0xff1c2530;
 private static int roundRobin;
 private static long pos(int x,int z){return ((long)x<<32)|(z&0xffffffffL);}
 private static LinkedHashMap<Long,int[]> cache(String dimension){
  return COLORS.computeIfAbsent(dimension,d->new LinkedHashMap<>(128,.75f,true){
   @Override protected boolean removeEldestEntry(Map.Entry<Long,int[]> eldest){
    return size()>MAX_CACHED;
   }
  });
 }
 public static void clear(){COLORS.clear();roundRobin=0;}
 public static int[] pixels(ClientLevel world,int cx,int cz){
  if(world==null)return null;
  var map=COLORS.get(world.dimension().identifier().toString());
  return map==null?null:map.get(pos(cx,cz));
 }
 private static void sample(ClientLevel world,int cx,int cz){
  String dim=world.dimension().identifier().toString();
  var map=cache(dim);long key=pos(cx,cz);
  if(map.containsKey(key)||!world.hasChunk(cx,cz))return;
  int[] colors=new int[RES*RES];
  for(int z=0;z<RES;z++)for(int x=0;x<RES;x++){
   int wx=(cx<<4)+x*4+2,wz=(cz<<4)+z*4+2;
   int y=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx,wz)-1;
   BlockPos block=new BlockPos(wx,y,wz);
   int color=world.getBlockState(block).getMapColor(world,block).col;
   if(color==0)color=0x4e6471;
   // Match ordinary Minecraft map shading without constructing MapItemSavedData.
   double shade=1.0+((y&7)-3)*.024;
   int red=Math.min(255,(int)(((color>>16)&255)*shade));
   int green=Math.min(255,(int)(((color>>8)&255)*shade));
   int blue=Math.min(255,(int)((color&255)*shade));
   colors[z*RES+x]=0xff000000|(red<<16)|(green<<8)|blue;
  }
  map.put(key,colors);
 }
 /** One or two already-loaded chunks per client tick; near-player first. */
 public static void tick(ClientLevel world,int cx,int cz){
  if(world==null)return;
  sample(world,cx,cz);
  // Scan a radius of 5 (121 chunks) across 121 client ticks.
  int index=roundRobin++%121;
  sample(world,cx+(index%11)-5,cz+(index/11)-5);
 }
 public static void draw(ClientLevel world,GuiGraphicsExtractor g,
                         int cx,int cz,int px,int py,int size){
  int[] colors=pixels(world,cx,cz);
  if(colors==null){
   g.fill(px,py,px+size,py+size,UNKNOWN);
   return;
  }
  // The only work in render is cached integer lookups and UI rectangles.
  for(int z=0;z<RES;z++)for(int x=0;x<RES;x++){
   int x0=px+x*size/RES,x1=px+(x+1)*size/RES;
   int y0=py+z*size/RES,y1=py+(z+1)*size/RES;
   if(x1>x0&&y1>y0)g.fill(x0,y0,x1,y1,colors[z*RES+x]);
  }
 }
 public static void drawClaim(GuiGraphicsExtractor g,int x,int y,int tile,int status){
  if(status==0)return;
  int tone=switch(status&3){
   case 1->0xff4deb91;case 2->0xff7be3f9;case 3->0xffdf6b75;
   default->0xffaaaaaa;
  };
  // Tint only the border so the actual terrain stays readable.
  g.fill(x,y,x+tile,y+1,tone);
  g.fill(x,y+tile-1,x+tile,y+tile,tone);
  g.fill(x,y,x+1,y+tile,tone);
  g.fill(x+tile-1,y,x+tile,y+tile,tone);
  if((status&4)!=0){
   // Force-loaded chunks marked with the same green diagonal motif.
   for(int k=0;k<tile;k+=4)
    g.fill(x+k,y+Math.max(1,tile-3),x+Math.min(tile,k+2),y+tile,0xff66ee71);
  }
 }
}
''',encoding="utf8")

client=root/"client/V178ClaimsClient.java"
s=client.read_text(encoding="utf8")
s=rep(s,
''' private static boolean minimap=true;''',
''' private static boolean minimap=true;
 public static boolean minimapEnabled(){return minimap;}
 public static void toggleMinimap(){minimap=!minimap;}
 public static void batch(int mode,int x1,int z1,int x2,int z2){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.player.connection==null)return;
  net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
    new dev.obsidiannetwork.claims.V178ClaimsBatch(mode,x1,z1,x2,z2));
 }''')
s=rep(s,
'''   last=null;lastRequestX=Integer.MIN_VALUE;lastRequestZ=Integer.MIN_VALUE;
   return;''',
'''   last=null;lastRequestX=Integer.MIN_VALUE;lastRequestZ=Integer.MIN_VALUE;
   V178TerrainMap.clear();
   return;''')
s=rep(s,
'''  // Update ONLY on crossing a chunk boundary or every 100 ticks, and never''',
'''  int playerCx=mc.player.blockPosition().getX()>>4;
  int playerCz=mc.player.blockPosition().getZ()>>4;
  if(mc.screen instanceof V178ClaimsMapScreen screen){
   V178TerrainMap.tick(mc.level,screen.centerX(),screen.centerZ());
   // A quick drag can move the map while the server's 20-tick snapshot
   // throttle rejects an earlier request. Retry only when the displayed
   // snapshot is stale, at most once per 25 ticks (no request flood).
   V178ClaimsSnapshot pending=last;
   long now=mc.level.getGameTime();
   if((pending==null||pending.cx()!=screen.centerX()||pending.cz()!=screen.centerZ()
       ||!pending.dimension().equals(mc.level.dimension().identifier().toString()))
       &&(lastRequestTime==Long.MIN_VALUE||now<lastRequestTime
          ||now-lastRequestTime>=25))
    request(screen.centerX(),screen.centerZ());
  }else V178TerrainMap.tick(mc.level,playerCx,playerCz);
  // Update ONLY on crossing a chunk boundary or every 100 ticks, and never''')
s=rep(s,
'''   g.fill(x,y,x+11,y+10,shade(s));
   if((s&4)!=0)g.fill(x+7,y+1,x+10,y+4,0xffffff90);''',
'''   V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,11);
   V178TerrainMap.drawClaim(g,x,y,11,s);''')
client.write_text(s,encoding="utf8")

screen=root/"client/V178ClaimsMapScreen.java"
prior=screen.read_text(encoding="utf8")
assert "xSxLabs CHUNK CLAIMS" in prior and "mouseClicked(net.minecraft.client.input.MouseButtonEvent" in prior, "V178_MAP_GUI_INJECT_BASELINE_DRIFT"
screen.write_text(r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.claims.V178ClaimsSnapshot;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.network.chat.Component;
import org.lwjgl.glfw.GLFW;

/** Original FTB-style world/claim interface. Claim mode:
 * left: claim, right: unclaim, SHIFT-left: load, SHIFT-right: unload.
 * Drag: rectangle; jobs run at bounded server tick rate, not per-cell spam.
 * Map mode: pan by dragging, zoom with mouse wheel, space to center.
 */
public final class V178ClaimsMapScreen extends Screen {
 private static final int DIAMETER=25;
 private static final int MARGIN=88;
 private int cx=Integer.MIN_VALUE,cz,zoom=13;
 private boolean claiming=true,grid=true,help;
 private boolean dragging;
 private int dragMode,firstX,firstZ,lastX,lastZ;
 private double panX,panY;
 public V178ClaimsMapScreen(){super(Component.literal("xSxLabs | World Map & Claims"));}
 public int centerX(){return cx==Integer.MIN_VALUE?0:cx;}
 public int centerZ(){return cz;}
 private int tile(){return Math.min(zoom,Math.max(4,(Math.min(width,height)-MARGIN)/DIAMETER));}
 private int left(){return (width-DIAMETER*tile())/2;}
 private int top(){return (height-DIAMETER*tile())/2;}
 private void center(){
  var p=Minecraft.getInstance().player;
  if(p!=null){cx=p.blockPosition().getX()>>4;cz=p.blockPosition().getZ()>>4;}
  request();
 }
 private void request(){if(cx!=Integer.MIN_VALUE)V178ClaimsClient.request(cx,cz);}
 @Override protected void init(){
  if(cx==Integer.MIN_VALUE)center();
  addRenderableWidget(Button.builder(Component.literal("Map"),b->claiming=false)
     .bounds(5,5,46,20).build());
  addRenderableWidget(Button.builder(Component.literal("Claims"),b->claiming=true)
     .bounds(55,5,57,20).build());
  addRenderableWidget(Button.builder(Component.literal("Center"),b->center())
     .bounds(116,5,60,20).build());
  addRenderableWidget(Button.builder(Component.literal("Mini"),b->V178ClaimsClient.toggleMinimap())
     .bounds(180,5,45,20).build());
  addRenderableWidget(Button.builder(Component.literal("i"),b->help=!help)
     .bounds(229,5,22,20).build());
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int tile=tile(),x0=left(),y0=top(),w=DIAMETER*tile;
  g.fill(x0-4,y0-5,x0+w+4,y0+w+34,0xe8081a28);
  V178ClaimsSnapshot map=V178ClaimsClient.snapshot();
  boolean good=map!=null&&map.cx()==cx&&map.cz()==cz&&
      Minecraft.getInstance().level!=null&&
      map.dimension().equals(Minecraft.getInstance().level.dimension().identifier().toString());
  var world=Minecraft.getInstance().level;
  for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){
   int px=x0+x*tile,py=y0+z*tile,cxWorld=cx+x-12,czWorld=cz+z-12;
   V178TerrainMap.draw(world,g,cxWorld,czWorld,px,py,tile);
   if(!grid)continue;
   int state=good?Byte.toUnsignedInt(V178ClaimsClient.state(map,cxWorld,czWorld)):0;
   if(state!=0)V178TerrainMap.drawClaim(g,px,py,tile,state);
   else if(tile>=8){
    g.fill(px,py,px+tile,py+1,0x44557788);
    g.fill(px,py,px+1,py+tile,0x44557788);
   }
  }
  // Local position pointer (does not imply a chunk is loaded).
  if(world!=null&&Minecraft.getInstance().player!=null){
   var p=Minecraft.getInstance().player;
   int dx=(p.blockPosition().getX()>>4)-cx+12;
   int dz=(p.blockPosition().getZ()>>4)-cz+12;
   if(dx>=0&&dx<DIAMETER&&dz>=0&&dz<DIAMETER){
    int px=x0+dx*tile+tile/2,py=y0+dz*tile+tile/2;
    g.fill(px-2,py-2,px+3,py+3,0xfffceca8);
   }
  }
  if(dragging&&claiming){
   int a=Math.max(cx-12,Math.min(firstX,lastX)),b=Math.min(cx+12,Math.max(firstX,lastX));
   int c=Math.max(cz-12,Math.min(firstZ,lastZ)),d=Math.min(cz+12,Math.max(firstZ,lastZ));
   int tone=dragMode<2?0xaa80c4ff:0xaa65ef83;
   g.fill(x0+(a-cx+12)*tile,y0+(c-cz+12)*tile,
       x0+(b-cx+13)*tile,y0+(d-cz+13)*tile,0x3055e9e6);
   g.fill(x0+(a-cx+12)*tile,y0+(c-cz+12)*tile,
       x0+(b-cx+13)*tile,y0+(c-cz+12)*tile+2,tone);
  }
  String mode=claiming?"CLAIM / LOAD":"EXPLORED WORLD MAP";
  g.text(font,"xSxLabs "+mode+" | "+cx+","+cz+" | Zoom "+zoom,x0,y0-17,0xff88e7f8);
  g.text(font,claiming?
    "Left: claim  Right: unclaim  Shift+Left: load  Shift+Right: unload":
    "Drag: pan  Wheel: zoom  C: claims  Space: center",
    x0,y0+w+6,0xffc3d5e9);
  g.text(font,"C: mode  G: grid  N: minimap  H: help  Arrows: pan",
    x0,y0+w+18,0xff9baec4);
  if(!good&&claiming)g.text(font,"Updating claim ownership...",x0+2,y0+4,0xfff3c479);
  if(help){
   int bx=Math.max(3,x0+5),by=y0+10;
   g.fill(bx,by,bx+Math.min(w-10,285),by+89,0xf00d2334);
   g.text(font,"CLAIMING / LOADING",bx+5,by+6,0xff94dff6);
   g.text(font,"L click + drag  Claim area",bx+5,by+19,0xfff4f4f4);
   g.text(font,"R click + drag  Unclaim area",bx+5,by+31,0xfff4f4f4);
   g.text(font,"Shift + L drag  Force-load claimed",bx+5,by+43,0xff78ed89);
   g.text(font,"Shift + R drag  Unload",bx+5,by+55,0xff78ed89);
   g.text(font,"Green stripes = loaded chunks",bx+5,by+67,0xffa5efb1);
   g.text(font,"Map mode: see terrain, scroll zoom",bx+5,by+79,0xffaddef4);
  }
 }
 private boolean inside(double mx,double my){
  return mx>=left()&&mx<left()+DIAMETER*tile()
     &&my>=top()&&my<top()+DIAMETER*tile();
 }
 private int chunkX(double mouseX){
  return cx-12+Math.max(0,Math.min(24,((int)mouseX-left())/tile()));
 }
 private int chunkZ(double mouseY){
  return cz-12+Math.max(0,Math.min(24,((int)mouseY-top())/tile()));
 }
 @Override public boolean mouseClicked(MouseButtonEvent e,boolean doubleClick){
  if(super.mouseClicked(e,doubleClick))return true; // GUI buttons first
  if(!inside(e.x(),e.y())||(e.button()!=0&&e.button()!=1))return false;
  if(!claiming){dragging=true;panX=0;panY=0;return true;}
  V178ClaimsSnapshot map=V178ClaimsClient.snapshot();
  if(map==null||map.cx()!=cx||map.cz()!=cz)return true;
  dragging=true;
  firstX=lastX=chunkX(e.x());firstZ=lastZ=chunkZ(e.y());
  dragMode=((e.modifiers()&GLFW.GLFW_MOD_SHIFT)!=0?2:0)+(e.button()==1?1:0);
  return true;
 }
 @Override public boolean mouseDragged(MouseButtonEvent e,double dx,double dy){
  if(!dragging)return super.mouseDragged(e,dx,dy);
  if(claiming){
   lastX=chunkX(e.x());lastZ=chunkZ(e.y());
  }else{
   panX+=dx;panY+=dy;int tile=tile();
   if(Math.abs(panX)>=tile||Math.abs(panY)>=tile){
    cx-=(int)(panX/tile);cz-=(int)(panY/tile);
    panX%=tile;panY%=tile;request();
   }
  }
  return true;
 }
 @Override public boolean mouseReleased(MouseButtonEvent e){
  if(!dragging)return super.mouseReleased(e);
  dragging=false;
  if(claiming){
   V178ClaimsClient.batch(dragMode,firstX,firstZ,lastX,lastZ);
  }
  return true;
 }
 @Override public boolean mouseScrolled(double mx,double my,double horizontal,double vertical){
  zoom=Math.max(6,Math.min(18,zoom+(vertical>0?1:vertical<0?-1:0)));
  return true;
 }
 @Override public boolean keyPressed(KeyEvent e){
  int k=e.key();
  if(k==GLFW.GLFW_KEY_M){Minecraft.getInstance().setScreen(null);return true;}
  if(k==GLFW.GLFW_KEY_C){claiming=!claiming;return true;}
  if(k==GLFW.GLFW_KEY_N){V178ClaimsClient.toggleMinimap();return true;}
  if(k==GLFW.GLFW_KEY_G){grid=!grid;return true;}
  if(k==GLFW.GLFW_KEY_H){help=!help;return true;}
  if(k==GLFW.GLFW_KEY_SPACE||k==GLFW.GLFW_KEY_R){center();return true;}
  if(k==GLFW.GLFW_KEY_LEFT)cx-=6;
  else if(k==GLFW.GLFW_KEY_RIGHT)cx+=6;
  else if(k==GLFW.GLFW_KEY_UP)cz-=6;
  else if(k==GLFW.GLFW_KEY_DOWN)cz+=6;
  else return super.keyPressed(e);
  request();return true;
 }
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf8")
print("V178_FTB_TERRAIN_MINIMAP_SCREEN_AND_DRAG_GUI_INSTALLED")


# B1624: durable explored terrain, waypoints and deaths, team GUI.
# This runs after the map implementation above and keeps the server packet
# protocol, chunk tickets, the mining cursor, and legacy UI untouched.
terrain=root/"client/V178TerrainMap.java"
s=terrain.read_text(encoding="utf8")
s=rep(s,''' private static int roundRobin;''',r''' private static int roundRobin;
 private static String mapIdentity;
 private static java.nio.file.Path mapFile;
 private static String mapDimension;
 private static boolean dirty;
 private static long lastFlushTick=Long.MIN_VALUE;
 private static void flush(){
  if(!dirty||mapFile==null||mapDimension==null)return;
  var data=COLORS.get(mapDimension);
  if(data==null)return;
  java.nio.file.Path tmp=null;
  try{
   java.nio.file.Files.createDirectories(mapFile.getParent());
   tmp=java.nio.file.Files.createTempFile(mapFile.getParent(),"xsxlabs-explored-",".tmp");
   try(var out=new java.io.DataOutputStream(new java.io.BufferedOutputStream(
       java.nio.file.Files.newOutputStream(tmp)))){
    out.writeInt(0x58535838);out.writeInt(data.size());
    for(var e:data.entrySet()){
     out.writeLong(e.getKey());
     for(int pixel:e.getValue())out.writeInt(pixel);
    }
   }
   try{java.nio.file.Files.move(tmp,mapFile,java.nio.file.StandardCopyOption.ATOMIC_MOVE,
                                  java.nio.file.StandardCopyOption.REPLACE_EXISTING);}
   catch(java.nio.file.AtomicMoveNotSupportedException unsupported){
    java.nio.file.Files.move(tmp,mapFile,java.nio.file.StandardCopyOption.REPLACE_EXISTING);
   }
   dirty=false;
  }catch(java.io.IOException error){
   System.err.println("[xSxLabs] explored map save failed: "+error);
  }finally{
   if(tmp!=null)try{java.nio.file.Files.deleteIfExists(tmp);}catch(java.io.IOException ignored){}
  }
 }
 private static void ensureWorld(ClientLevel world){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return;
  String dim=world.dimension().identifier().toString();
  String server=mc.getCurrentServer()==null?"singleplayer":mc.getCurrentServer().ip;
  String next=server+"|"+mc.player.getUUID()+"|"+dim;
  if(next.equals(mapIdentity))return;
  flush();COLORS.clear();roundRobin=0;
  dirty=false;mapIdentity=next;mapDimension=dim;lastFlushTick=Long.MIN_VALUE;
  // One bounded 4x4-pixel file per player/server/dimension. No server packets.
  mapFile=mc.gameDirectory.toPath().resolve("config").resolve("xsxlabs-worldmap")
      .resolve("terrain-"+Integer.toHexString(next.hashCode())+".bin");
  if(!java.nio.file.Files.isRegularFile(mapFile))return;
  try(var in=new java.io.DataInputStream(new java.io.BufferedInputStream(
      java.nio.file.Files.newInputStream(mapFile)))){
   if(in.readInt()!=0x58535838)return;
   int count=in.readInt();
   if(count<0||count>MAX_CACHED)return;
   var found=cache(dim);
   for(int i=0;i<count;i++){
    long pos=in.readLong();
    int[] pixels=new int[RES*RES];
    for(int j=0;j<pixels.length;j++)pixels[j]=in.readInt();
    found.put(pos,pixels);
   }
  }catch(java.io.IOException error){
   COLORS.remove(dim);
   System.err.println("[xSxLabs] explored map read failed: "+error);
  }
 }
''')
s=rep(s,''' public static void clear(){COLORS.clear();roundRobin=0;}''',
''' public static void clear(){
  flush();COLORS.clear();roundRobin=0;
  mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;
 }''')
s=rep(s,'''  map.put(key,colors);
 }''','''  map.put(key,colors);dirty=true;
 }''')
s=rep(s,''' public static void tick(ClientLevel world,int cx,int cz){
  if(world==null)return;
  sample(world,cx,cz);''',''' public static void tick(ClientLevel world,int cx,int cz){
  if(world==null)return;
  ensureWorld(world);
  long now=world.getGameTime();
  if(dirty&&(lastFlushTick==Long.MIN_VALUE||now<lastFlushTick
             ||now-lastFlushTick>=1200)){
   flush();lastFlushTick=now;
  }
  sample(world,cx,cz);''')
terrain.write_text(s,encoding="utf8")

waypoints=root/"client/V178Waypoints.java"
assert not waypoints.exists(),"V178_WAYPOINT_DUPLICATE"
waypoints.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Client-local, player/server-isolated markers. No world scans or packets.
 * Snapshots are persisted on marker changes only. A falling health edge adds
 * one death marker, never one every death-screen frame.
 */
public final class V178Waypoints {
 private V178Waypoints(){}
 private record Marker(String dim,int x,int y,int z,String label,boolean death){}
 private static final int MAX=128;
 private static final ArrayList<Marker> MARKERS=new ArrayList<>();
 private static Path file;
 private static String identity;
 private static boolean deathLatch;
 private static String dimension(ClientLevel w){return w.dimension().identifier().toString();}
 private static void save(){
  if(file==null)return;
  Path tmp=null;
  try{
   Files.createDirectories(file.getParent());
   tmp=Files.createTempFile(file.getParent(),"xsxlabs-waypoints-",".tmp");
   try(var out=Files.newBufferedWriter(tmp)){
    for(Marker m:MARKERS){
     out.write(m.dim()+"\t"+m.x()+"\t"+m.y()+"\t"+m.z()+"\t"+
               (m.death()?"1":"0")+"\t"+m.label()+"\n");
    }
   }
   try{Files.move(tmp,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
   catch(AtomicMoveNotSupportedException noAtomic){
    Files.move(tmp,file,StandardCopyOption.REPLACE_EXISTING);
   }
  }catch(IOException ex){System.err.println("[xSxLabs] marker save failed: "+ex);}
  finally{if(tmp!=null)try{Files.deleteIfExists(tmp);}catch(IOException ignored){}}
 }
 private static void load(){
  MARKERS.clear();
  if(file==null||!Files.isRegularFile(file))return;
  try(var in=Files.newBufferedReader(file)){
   String line;
   while((line=in.readLine())!=null&&MARKERS.size()<MAX){
    String[] v=line.split("\t",6);
    if(v.length!=6||v[0].length()>100||v[5].length()>32)continue;
    try{
     int x=Integer.parseInt(v[1]),y=Integer.parseInt(v[2]),z=Integer.parseInt(v[3]);
     if(Math.abs((long)x)>30000000||Math.abs((long)z)>30000000)continue;
     MARKERS.add(new Marker(v[0],x,y,z,v[5],v[4].equals("1")));
    }catch(NumberFormatException ignored){}
   }
  }catch(IOException ex){System.err.println("[xSxLabs] marker read failed: "+ex);}
 }
 private static void initialize(LocalPlayer player){
  var mc=Minecraft.getInstance();
  String server=mc.getCurrentServer()==null?"singleplayer":mc.getCurrentServer().ip;
  String id=server+"|"+player.getUUID();
  if(id.equals(identity))return;
  identity=id;deathLatch=false;
  file=mc.gameDirectory.toPath().resolve("config").resolve("xsxlabs-worldmap")
      .resolve("waypoints-"+Integer.toHexString(id.hashCode())+".tsv");
  load();
 }
 public static void clear(){MARKERS.clear();identity=null;file=null;deathLatch=false;}
 public static void tick(LocalPlayer player){
  initialize(player);
  boolean dead=player.isDeadOrDying();
  if(dead&&!deathLatch){
   BlockPos at=player.blockPosition();
   // Keep old deaths available but bounded, like other waypoints.
   append(new Marker(dimension((ClientLevel)player.level()),at.getX(),at.getY(),
       at.getZ(),"Death",true));
  }
  deathLatch=dead;
 }
 private static void append(Marker m){
  if(MARKERS.size()>=MAX)MARKERS.remove(0);
  MARKERS.add(m);save();
 }
 public static void add(ClientLevel w,int cx,int cz){
  var mc=Minecraft.getInstance();
  if(w==null||mc.player==null)return;
  initialize(mc.player);
  if(Math.abs((long)cx)>1875000||Math.abs((long)cz)>1875000)return;
  String label="WP "+(MARKERS.size()+1);
  append(new Marker(dimension(w),cx*16+8,mc.player.blockPosition().getY(),
       cz*16+8,label,false));
 }
 public static void remove(ClientLevel w,int cx,int cz){
  if(w==null)return;
  String dim=dimension(w);
  for(int i=MARKERS.size()-1;i>=0;i--){
   Marker m=MARKERS.get(i);
   if(m.dim().equals(dim)&&(m.x()>>4)==cx&&(m.z()>>4)==cz){
    MARKERS.remove(i);save();return;
   }
  }
 }
 public static void drawMap(ClientLevel world,GuiGraphicsExtractor g,
                            int cx,int cz,int x0,int y0,int tile){
  if(world==null)return;
  String dim=dimension(world);
  for(Marker m:MARKERS){
   if(!m.dim().equals(dim))continue;
   int dx=(m.x()>>4)-cx+12,dz=(m.z()>>4)-cz+12;
   if(dx<0||dx>=25||dz<0||dz>=25)continue;
   int px=x0+dx*tile+tile/2,py=y0+dz*tile+tile/2;
   g.fill(px-2,py-2,px+3,py+3,m.death()?0xffff5c63:0xffffff69);
   if(tile>=9)g.text(Minecraft.getInstance().font,
       m.death()?"X":m.label(),px+3,py-3,m.death()?0xffff898e:0xffffeaa0);
  }
 }
 public static void drawMini(ClientLevel world,GuiGraphicsExtractor g,
                             int cx,int cz,int ox,int oy){
  if(world==null)return;
  String dim=dimension(world);
  for(Marker m:MARKERS){
   if(!m.dim().equals(dim))continue;
   int dx=(m.x()>>4)-cx,dz=(m.z()>>4)-cz;
   if(dx< -3||dx>3||dz< -3||dz>3)continue;
   int x=ox+(dx+3)*12+5,y=oy+(dz+3)*11+5;
   g.fill(x-2,y-2,x+2,y+2,m.death()?0xffef485e:0xffffe764);
  }
 }
}
''',encoding="utf8")

team=root/"client/V178ClaimsTeamScreen.java"
assert not team.exists(),"V178_TEAM_DUPLICATE"
team.write_text(r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
/** Trust management backed by existing server-authoritative xsxchunks commands. */
public final class V178ClaimsTeamScreen extends Screen {
 private final Screen previous;
 private EditBox name;
 public V178ClaimsTeamScreen(Screen parent){
  super(Component.literal("xSxLabs | Trusted Players"));previous=parent;
 }
 @Override protected void init(){
  int x=width/2-114,y=height/2-45;
  name=new EditBox(font,x,y,228,20,Component.literal("Player name"));
  name.setMaxLength(16);
  addRenderableWidget(name);
  addRenderableWidget(Button.builder(Component.literal("Trust"),b->execute(true))
      .bounds(x,y+27,110,20).build());
  addRenderableWidget(Button.builder(Component.literal("Untrust"),b->execute(false))
      .bounds(x+118,y+27,110,20).build());
  addRenderableWidget(Button.builder(Component.literal("Back"),b->onClose())
      .bounds(x,y+54,228,20).build());
 }
 private void execute(boolean trust){
  String player=name.getValue().trim();
  if(!player.matches("[A-Za-z0-9_]{3,16}"))return;
  var me=Minecraft.getInstance().player;
  if(me!=null&&me.connection!=null)
   me.connection.sendCommand("xsxchunks "+(trust?"trust ":"untrust ")+player);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  g.text(font,"TRUSTED PLAYERS",width/2-65,height/2-67,0xff9ce8f2);
  g.text(font,"Enter an online player's name.",width/2-113,height/2+39,0xffbfd4e4);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf8")

client=root/"client/V178ClaimsClient.java"
s=client.read_text(encoding="utf8")
s=rep(s,'''   V178TerrainMap.clear();
   return;''',
'''   V178TerrainMap.clear();
   V178Waypoints.clear();
   return;''')
s=rep(s,'''  while(WORLD_MAP.consumeClick()){''',
'''  V178Waypoints.tick(mc.player);
  while(WORLD_MAP.consumeClick()){''')
s=rep(s,'''  g.fill(ox+43,oy+45,ox+48,oy+50,0xffffffff);''',
'''  V178Waypoints.drawMini(mc.level,g,cx,cz,ox+4,oy+15);
  g.fill(ox+43,oy+45,ox+48,oy+50,0xffffffff);''')
client.write_text(s,encoding="utf8")

screen=root/"client/V178ClaimsMapScreen.java"
s=screen.read_text(encoding="utf8")
s=rep(s,'''  addRenderableWidget(Button.builder(Component.literal("i"),b->help=!help)
     .bounds(229,5,22,20).build());''',
'''  addRenderableWidget(Button.builder(Component.literal("i"),b->help=!help)
     .bounds(229,5,22,20).build());
  addRenderableWidget(Button.builder(Component.literal("+WP"),b->
      V178Waypoints.add(Minecraft.getInstance().level,centerX(),centerZ()))
     .bounds(255,5,43,20).build());
  addRenderableWidget(Button.builder(Component.literal("-WP"),b->
      V178Waypoints.remove(Minecraft.getInstance().level,centerX(),centerZ()))
     .bounds(301,5,43,20).build());
  addRenderableWidget(Button.builder(Component.literal("Team"),b->
      Minecraft.getInstance().setScreen(new V178ClaimsTeamScreen(this)))
     .bounds(347,5,47,20).build());''')
s=rep(s,'''  // Local position pointer (does not imply a chunk is loaded).''',
'''  V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile);
  // Local position pointer (does not imply a chunk is loaded).''')
s=rep(s,'''  g.text(font,"C: mode  G: grid  N: minimap  H: help  Arrows: pan",''',
'''  g.text(font,"C: mode  G: grid  N: minimap  Middle: waypoint  Shift+Middle: delete",''')
s=rep(s,'''  if(!inside(e.x(),e.y())||(e.button()!=0&&e.button()!=1))return false;
  if(!claiming){''',
'''  if(!inside(e.x(),e.y()))return false;
  if(e.button()==2){
   int x=chunkX(e.x()),z=chunkZ(e.y());
   if((e.modifiers()&GLFW.GLFW_MOD_SHIFT)!=0)
    V178Waypoints.remove(Minecraft.getInstance().level,x,z);
   else V178Waypoints.add(Minecraft.getInstance().level,x,z);
   return true;
  }
  if(e.button()!=0&&e.button()!=1)return false;
  if(!claiming){''')
screen.write_text(s,encoding="utf8")
print("V178_EXPLORED_PERSISTENCE_WAYPOINTS_DEATH_MARKERS_TRUST_GUI_INSTALLED")


# B1628: editor/manager for named colored waypoints, real scalable map zoom,
# and a minimap position that does not overlap an active JARVIS radar.
waypoints=root/"client/V178Waypoints.java"
s=waypoints.read_text(encoding="utf8")
s=rep(s,''' private record Marker(String dim,int x,int y,int z,String label,boolean death){}''',
''' public record Marker(String dim,int x,int y,int z,String label,boolean death,int color){}''')
s=rep(s,r'''               (m.death()?"1":"0")+"\t"+m.label()+"\n");''',
r'''               (m.death()?"1":"0")+"\t"+m.label()+"\t"+m.color()+"\n");''')
s=rep(s,r'''    String[] v=line.split("\t",6);
    if(v.length!=6||v[0].length()>100||v[5].length()>32)continue;''',
r'''    String[] v=line.split("\t",7);
    if((v.length!=6&&v.length!=7)||v[0].length()>100||v[5].length()>32)continue;''')
s=rep(s,'''     MARKERS.add(new Marker(v[0],x,y,z,v[5],v[4].equals("1")));''',
'''     int tint=v.length==7?Integer.parseInt(v[6]):
          (v[4].equals("1")?0xffff5c63:0xffffff69);
     MARKERS.add(new Marker(v[0],x,y,z,v[5],v[4].equals("1"),tint));''')
s=rep(s,'''       at.getZ(),"Death",true));''',
'''       at.getZ(),"Death",true,0xffff5c63));''')
s=rep(s,'''       cz*16+8,label,false));''',
'''       cz*16+8,label,false,0xffffff69));''')
s=rep(s,''' public static void remove(ClientLevel w,int cx,int cz){''',
''' public static java.util.List<Marker> list(ClientLevel w){
  if(w==null)return java.util.List.of();
  String d=dimension(w);
  var list=new java.util.ArrayList<Marker>();
  for(Marker m:MARKERS)if(m.dim().equals(d))list.add(m);
  return java.util.List.copyOf(list);
 }
 public static Marker lookup(ClientLevel w,int cx,int cz){
  if(w==null)return null;
  String d=dimension(w);
  for(int i=MARKERS.size()-1;i>=0;i--){
   Marker m=MARKERS.get(i);
   if(m.dim().equals(d)&&(m.x()>>4)==cx&&(m.z()>>4)==cz)return m;
  }
  return null;
 }
 public static void saveAt(ClientLevel w,int cx,int cz,String text,int y,int color){
  if(w==null||text==null||text.isBlank()||text.length()>32
     ||Math.abs((long)cx)>1875000||Math.abs((long)cz)>1875000)return;
  // Never serialize tabs/newlines or path characters from GUI input.
  String label=text.replace('\\t',' ').replace('\\n',' ').replace('\\r',' ');
  if(label.isBlank())return;
  String d=dimension(w);
  for(int i=MARKERS.size()-1;i>=0;i--){
   Marker old=MARKERS.get(i);
   if(old.dim().equals(d)&&(old.x()>>4)==cx&&(old.z()>>4)==cz){
    MARKERS.set(i,new Marker(d,cx*16+8,y,cz*16+8,label,old.death(),color));
    save();return;
   }
  }
  append(new Marker(d,cx*16+8,y,cz*16+8,label,false,color));
 }
 public static void remove(ClientLevel w,int cx,int cz){''')
s=rep(s,'''   g.fill(px-2,py-2,px+3,py+3,m.death()?0xffff5c63:0xffffff69);''',
'''   g.fill(px-2,py-2,px+3,py+3,m.color());''')
s=rep(s,'''       m.death()?"X":m.label(),px+3,py-3,m.death()?0xffff898e:0xffffeaa0);''',
'''       m.death()?"X":m.label(),px+3,py-3,m.color());''')
s=rep(s,'''   g.fill(x-2,y-2,x+2,y+2,m.death()?0xffef485e:0xffffe764);''',
'''   g.fill(x-2,y-2,x+2,y+2,m.color());''')
waypoints.write_text(s,encoding="utf8")

editor=root/"client/V178WaypointEditorScreen.java"
assert not editor.exists(),"V178_WAYPOINT_EDITOR_DUPLICATE"
editor.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Named and color-selectable local marker editor; no server RPC. */
public final class V178WaypointEditorScreen extends Screen {
 private static final int[] PALETTE={
  0xffffff69,0xff56e5a0,0xff65d7ff,0xffac91ff,0xffff8ec4,0xffff6b63
 };
 private final Screen previous;
 private final int cx,cz;
 private EditBox label,altitude;
 private int tint=0;
 public V178WaypointEditorScreen(Screen previous,int cx,int cz){
  super(Component.literal("xSxLabs | Waypoint Editor"));
  this.previous=previous;this.cx=cx;this.cz=cz;
 }
 private void save(){
  var mc=Minecraft.getInstance();
  if(mc.level==null||label==null||altitude==null)return;
  int y;
  try{y=Integer.parseInt(altitude.getValue().trim());}
  catch(NumberFormatException invalid){return;}
  if(y< -2048||y>4096)return;
  V178Waypoints.saveAt(mc.level,cx,cz,label.getValue().trim(),y,PALETTE[tint]);
  onClose();
 }
 @Override protected void init(){
  var mc=Minecraft.getInstance();
  V178Waypoints.Marker old=V178Waypoints.lookup(mc.level,cx,cz);
  int x=width/2-105,y=height/2-58;
  label=new EditBox(font,x,y,210,20,Component.literal("Waypoint name"));
  label.setMaxLength(32);
  label.setValue(old==null?"Waypoint":old.label());
  addRenderableWidget(label);
  altitude=new EditBox(font,x,y+26,210,20,Component.literal("Y coordinate"));
  altitude.setMaxLength(6);
  altitude.setValue(Integer.toString(old==null?
    (mc.player==null?64:mc.player.blockPosition().getY()):old.y()));
  addRenderableWidget(altitude);
  if(old!=null)for(int i=0;i<PALETTE.length;i++)
   if(old.color()==PALETTE[i])tint=i;
  addRenderableWidget(Button.builder(Component.literal("Change Color"),
      b->tint=(tint+1)%PALETTE.length).bounds(x,y+54,210,20).build());
  addRenderableWidget(Button.builder(Component.literal("Save"),b->save())
      .bounds(x,y+81,102,20).build());
  addRenderableWidget(Button.builder(Component.literal("Cancel"),b->onClose())
      .bounds(x+108,y+81,102,20).build());
  if(old!=null)addRenderableWidget(Button.builder(Component.literal("Remove Marker"),b->{
     V178Waypoints.remove(Minecraft.getInstance().level,cx,cz);onClose();
  }).bounds(x,y+108,210,20).build());
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int x=width/2-105,y=height/2-77;
  g.text(font,"WAYPOINT | chunk "+cx+", "+cz,x,y,0xff96e3f1);
  g.fill(x+186,y+62,x+210,y+78,PALETTE[tint]);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf8")

manager=root/"client/V178WaypointManagerScreen.java"
assert not manager.exists(),"V178_WAYPOINT_MANAGER_DUPLICATE"
manager.write_text(r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
/** Paged per-dimension waypoint list; no per-tick scans or packets. */
public final class V178WaypointManagerScreen extends Screen {
 private final Screen previous;
 private int page;
 public V178WaypointManagerScreen(Screen previous){
  super(Component.literal("xSxLabs | Waypoints"));this.previous=previous;
 }
 @Override protected void init(){
  var mc=Minecraft.getInstance();
  var marks=V178Waypoints.list(mc.level);
  int pages=Math.max(1,(marks.size()+6)/7);
  page=Math.max(0,Math.min(page,pages-1));
  int x=width/2-140,y=Math.max(32,height/2-101);
  for(int i=page*7;i<Math.min(marks.size(),page*7+7);i++){
   var mark=marks.get(i);
   int mx=mark.x()>>4,mz=mark.z()>>4,yy=y+((i-page*7)*24);
   String name=mark.label()+" ["+mx+","+mz+"]";
   addRenderableWidget(Button.builder(Component.literal(name),b->
       mc.setScreen(new V178WaypointEditorScreen(this,mx,mz)))
       .bounds(x,yy,234,20).build());
   addRenderableWidget(Button.builder(Component.literal("X"),b->{
       V178Waypoints.remove(mc.level,mx,mz);rebuildWidgets();
   }).bounds(x+240,yy,35,20).build());
  }
  addRenderableWidget(Button.builder(Component.literal("<"),b->{
    page=Math.max(0,page-1);rebuildWidgets();
  }).bounds(x,y+176,38,20).build());
  addRenderableWidget(Button.builder(Component.literal("Back"),b->onClose())
      .bounds(x+43,y+176,185,20).build());
  addRenderableWidget(Button.builder(Component.literal(">"),b->{
    page=Math.min(pages-1,page+1);rebuildWidgets();
  }).bounds(x+233,y+176,42,20).build());
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  g.text(font,"WAYPOINT MANAGER | click to edit",width/2-139,
      Math.max(12,height/2-122),0xff9debf2);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf8")

screen=root/"client/V178ClaimsMapScreen.java"
s=screen.read_text(encoding="utf8")
s=rep(s,''' private static final int DIAMETER=25;''',
''' private int DIAMETER=25;''')
s=rep(s,''' private int tile(){return Math.min(zoom,Math.max(4,(Math.min(width,height)-MARGIN)/DIAMETER));}''',
''' private int tile(){return zoom;}
 private void adapt(){
  DIAMETER=Math.max(5,Math.min(25,
      (Math.min(width,height)-MARGIN)/Math.max(1,zoom)));
 }''')
s=rep(s,''' @Override protected void init(){
  if(cx==Integer.MIN_VALUE)center();''',
''' @Override protected void init(){
  adapt();
  if(cx==Integer.MIN_VALUE)center();''')
s=rep(s,'''  zoom=Math.max(6,Math.min(18,zoom+(vertical>0?1:vertical<0?-1:0)));
  return true;''',
'''  zoom=Math.max(6,Math.min(18,zoom+(vertical>0?1:vertical<0?-1:0)));
  adapt();
  return true;''')
s=rep(s,'''  addRenderableWidget(Button.builder(Component.literal("+WP"),b->
      V178Waypoints.add(Minecraft.getInstance().level,centerX(),centerZ()))
     .bounds(255,5,43,20).build());
  addRenderableWidget(Button.builder(Component.literal("-WP"),b->
      V178Waypoints.remove(Minecraft.getInstance().level,centerX(),centerZ()))
     .bounds(301,5,43,20).build());''',
'''  addRenderableWidget(Button.builder(Component.literal("+WP"),b->
      Minecraft.getInstance().setScreen(new V178WaypointEditorScreen(this,centerX(),centerZ())))
     .bounds(255,5,43,20).build());
  addRenderableWidget(Button.builder(Component.literal("WPs"),b->
      Minecraft.getInstance().setScreen(new V178WaypointManagerScreen(this)))
     .bounds(301,5,43,20).build());''')
s=rep(s,'''  if(e.button()!=0&&e.button()!=1)return false;
  if(!claiming){dragging=true;panX=0;panY=0;return true;}''',
'''  if(e.button()!=0&&e.button()!=1)return false;
  if(!claiming&&e.button()==1){
   Minecraft.getInstance().setScreen(new V178WaypointEditorScreen(this,chunkX(e.x()),chunkZ(e.y())));
   return true;
  }
  if(!claiming){dragging=true;panX=0;panY=0;return true;}''')
# Keep owner snapshot centered at 25x25 even if fewer chunks fit on screen.
for old,new in (
 ("(a-cx+12)","(a-cx+DIAMETER/2)"),
 ("(b-cx+13)","(b-cx+DIAMETER/2+1)"),
 ("(c-cz+12)","(c-cz+DIAMETER/2)"),
 ("(d-cz+13)","(d-cz+DIAMETER/2+1)"),
 ("cx+x-12","cx+x-DIAMETER/2"),
 ("cz+z-12","cz+z-DIAMETER/2"),
 ("-cx+12","-cx+DIAMETER/2"),
 ("-cz+12","-cz+DIAMETER/2"),
 ("cx-12","cx-DIAMETER/2"),
 ("cz-12","cz-DIAMETER/2"),
 ("cx+12","cx+DIAMETER/2"),
 ("cz+12","cz+DIAMETER/2"),
 ("Math.min(24,((int)mouseX-left())/tile())","Math.min(DIAMETER-1,((int)mouseX-left())/tile())"),
 ("Math.min(24,((int)mouseY-top())/tile())","Math.min(DIAMETER-1,((int)mouseY-top())/tile())")
):
 assert old in s,("V178_DYNAMIC_ZOOM_DRIFT",old)
 s=s.replace(old,new)
screen.write_text(s,encoding="utf8")

client=root/"client/V178ClaimsClient.java"
s=client.read_text(encoding="utf8")
s=rep(s,'''  int ox=mc.getWindow().getGuiScaledWidth()-99,oy=9;''',
'''  int ox=mc.getWindow().getGuiScaledWidth()-99,oy=9;
  // Avoid drawing the minimap over JARVIS radar/diagnostics.
  if(V177JarvisClient.enabled()&&V177JarvisClient.available()
      &&V177JarvisSettings.on("hud")&&V177JarvisSettings.on("hud_radar")){
   ox=9;oy=Math.max(45,mc.getWindow().getGuiScaledHeight()-111);
  }''')
client.write_text(s,encoding="utf8")
print("V178_WAYPOINT_EDITOR_MANAGER_DYNAMIC_ZOOM_HUD_MINIMAP_LAYOUT_PASS")

# B1633: dynamic 5..25 tile viewport must align waypoint markers.
# No network traffic, no new render scanning, no changes to persisted data.
waypoints=root/"client/V178Waypoints.java"
s=waypoints.read_text(encoding="utf8")
s=rep(s,''' public static void drawMap(ClientLevel world,GuiGraphicsExtractor g,
                            int cx,int cz,int x0,int y0,int tile){''',
''' public static void drawMap(ClientLevel world,GuiGraphicsExtractor g,
                            int cx,int cz,int x0,int y0,int tile,int diameter){''')
s=rep(s,'''   int dx=(m.x()>>4)-cx+12,dz=(m.z()>>4)-cz+12;
   if(dx<0||dx>=25||dz<0||dz>=25)continue;''',
'''   // B1633_VIEWPORT_MARKER_PARITY: same grid as terrain and claims.
   int half=diameter/2;
   int dx=(m.x()>>4)-cx+half,dz=(m.z()>>4)-cz+half;
   if(dx<0||dx>=diameter||dz<0||dz>=diameter)continue;''')
waypoints.write_text(s,encoding="utf8")
screen=root/"client/V178ClaimsMapScreen.java"
s=screen.read_text(encoding="utf8")
s=rep(s,'''  V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile);''',
'''  V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile,DIAMETER);''')
screen.write_text(s,encoding="utf8")
print("V178_B1633_RESPONSIVE_WAYPOINT_MAP_PARITY_PASS")
