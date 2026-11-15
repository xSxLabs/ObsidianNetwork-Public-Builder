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
  if(mc.screen instanceof V178ClaimsMapScreen screen)
   V178TerrainMap.tick(mc.level,screen.centerX(),screen.centerZ());
  else V178TerrainMap.tick(mc.level,playerCx,playerCz);
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
  dragMode=(hasShiftDown()?2:0)+(e.button()==1?1:0);
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
