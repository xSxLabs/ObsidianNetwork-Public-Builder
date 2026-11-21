#!/usr/bin/env python3
"""B1780 / xSxLabs 1.7.8 v11: correct terrain, compact head pointer,
functional mining speed slot, cleaner mechanical miner, separate HUD editor.
Applied AFTER B1765. Client rendering never scans terrain or loads chunks.
"""
import json,os,re,struct,zlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1780_ANCHOR",rel,old[:110],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def emit(rel,content):
 p=J/rel
 assert not p.exists(),("B1780_DUPLICATE",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(content,encoding="utf-8")

# Compact skin pointer: a 6px real skin face and an 8px white yaw arrow,
# no giant white block obscuring the central terrain.
m=J/"client/V178MapMarkers.java"
s=m.read_text(encoding="utf-8")
head="  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){"
assert s.count(head)==1 and "B1775_WHITE_HEAD_POINTER" in s
a=s.index(head)
b=s.index("\n  }\n}",a)
new=r'''  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
   // B1765_DIRECTION_ARROW / B1775_WHITE_HEAD_POINTER / B1780_COMPACT_SKIN_ARROW
   double angle=Math.toRadians(yaw);
   double dx=-Math.sin(angle),dy=Math.cos(angle),ax=-dy,ay=dx;
   for(int t=5;t<=9;t++){
    int width=t<=6?2:t<=8?1:0;
    for(int w=-width;w<=width;w++){
     int px=x+(int)Math.round(dx*t+ax*w);
     int py=y+(int)Math.round(dy*t+ay*w);
     g.fill(px-1,py-1,px+2,py+2,0xff091923);
    }
   }
   for(int t=5;t<=9;t++){
    int width=t<=6?2:t<=8?1:0;
    for(int w=-width;w<=width;w++){
     int px=x+(int)Math.round(dx*t+ax*w);
     int py=y+(int)Math.round(dy*t+ay*w);
     g.fill(px,py,px+1,py+1,0xffffffff);
    }
   }
   g.fill(x-4,y-4,x+4,y+4,0xff091923);
   var mc=net.minecraft.client.Minecraft.getInstance();
   if(mc.player==null){g.fill(x-3,y-3,x+3,y+3,0xffffffff);return;}
   net.minecraft.client.gui.components.PlayerFaceExtractor.extractRenderState(
      g,mc.player.getSkin(),x-3,y-3,6);
  }'''
s=s[:a]+new+s[b+4:]
m.write_text(s,encoding="utf-8")

# WORLD_SURFACE returns flower/grass tips in a snowy biome. A map should
# visualize the exposed ground, not speckle the biome with decorative plants.
# Keep snow layers, fluids, leaves, structures and ALL solid modded blocks.
patch("client/V178TerrainMap.java",
'''   var state=world.getBlockState(block);''',
'''    var state=world.getBlockState(block);
    int vegetation=0;
    while(vegetation<4&&y>world.getMinY()
      &&(state.is(net.minecraft.world.level.block.Blocks.SHORT_GRASS)
        ||state.is(net.minecraft.world.level.block.Blocks.TALL_GRASS)
        ||state.is(net.minecraft.world.level.block.Blocks.FERN)
        ||state.is(net.minecraft.world.level.block.Blocks.LARGE_FERN)
        ||state.is(net.minecraft.world.level.block.Blocks.DEAD_BUSH)
        ||state.is(net.minecraft.world.level.block.Blocks.DANDELION)
        ||state.is(net.minecraft.world.level.block.Blocks.POPPY))){
     y--;vegetation++;block=new BlockPos(wx,y,wz);
     state=world.getBlockState(block);
    }''')
# Source refresh is bounded to client ticks; center tiles refresh twice as
# quickly when a player uncovers dirt or mines snow.
patch("client/V178TerrainMap.java",
'''if(refreshTick%8L==0L)refreshSurface(world,cx,cz);''',
'''if(refreshTick%4L==0L)refreshSurface(world,cx,cz);''')

# Registry reference is authoritative, not a substring guess.
patch("mining/V178MiningBuilderBE.java",
'''   var key=net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem());
   return key!=null&&"obsidiannetwork".equals(key.getNamespace())
     &&key.getPath().contains("speed_upgrade");''',
'''    return stack.is(dev.obsidiannetwork.ObsidianNetwork.SPEED_UPGRADE.get());''')
# Native shift-click support for the ONE speed slot. Chest indices are
# 0..26 machine, 27..62 actual player inventory, with card slot 0 untouched.
patch("mining/V178MiningBuilderMenu.java",
'''  // No implicit rearrangement of BE card or 26 fake slots. Manual drag/drop
  // through native Slot 0 supports insert and extraction without item dupes.
  return ItemStack.EMPTY;''',
'''  if(slot<0||slot>=slots.size()||!stillValid(player))return ItemStack.EMPTY;
  if(slot==0||(slot>1&&slot<27))return ItemStack.EMPTY;
  Slot source=slots.get(slot);
  if(!source.hasItem())return ItemStack.EMPTY;
  ItemStack held=source.getItem();
  ItemStack original=held.copy();
  if(slot==1){
   if(!moveItemStackTo(held,27,63,true))return ItemStack.EMPTY;
  }else if(slot>=27&&slot<63&&V178MiningBuilderBE.isSpeedUpgrade(held)){
   if(!moveItemStackTo(held,1,2,false))return ItemStack.EMPTY;
  }else return ItemStack.EMPTY;
  if(held.isEmpty())source.setByPlayer(ItemStack.EMPTY);
  else source.setChanged();
  return original;''')

# Per-client, per-layout, normalized coordinates for arbitrary resolutions.
# No file IO in game HUD drawing; saves only after edit actions.
emit("client/V178HudPlacement.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import java.nio.file.*;
import java.util.Properties;

/** B1780 user HUD placement, saved on edit, no world reads or render IO. */
public final class V178HudPlacement{
 private V178HudPlacement(){}
 private static boolean loaded;
 private static int mapX=-1,mapY=-1,infoX=-1,infoY=-1,infoSize=100;
 private static Path file(){
  return Minecraft.getInstance().gameDirectory.toPath()
    .resolve("config/xsxlabs-v178-hud-placement.properties");
 }
 private static int read(Properties p,String key,int fallback){
  try{return Integer.parseInt(p.getProperty(key,Integer.toString(fallback)));}
  catch(NumberFormatException e){return fallback;}
 }
 private static void ensure(){
  if(loaded)return;
  loaded=true;
  Properties p=new Properties();
  try{if(Files.isRegularFile(file()))try(var in=Files.newInputStream(file())){p.load(in);}}
  catch(Exception ignored){}
  mapX=clamp(read(p,"mapX",-1),-1,10000);
  mapY=clamp(read(p,"mapY",-1),-1,10000);
  infoX=clamp(read(p,"infoX",-1),-1,10000);
  infoY=clamp(read(p,"infoY",-1),-1,10000);
  infoSize=clamp(read(p,"infoSize",100),60,200);
 }
 private static int clamp(int n,int min,int max){return Math.max(min,Math.min(max,n));}
 private static void save(){
  Properties p=new Properties();
  p.setProperty("mapX",Integer.toString(mapX));
  p.setProperty("mapY",Integer.toString(mapY));
  p.setProperty("infoX",Integer.toString(infoX));
  p.setProperty("infoY",Integer.toString(infoY));
  p.setProperty("infoSize",Integer.toString(infoSize));
  try{
   Files.createDirectories(file().getParent());
   try(var out=Files.newOutputStream(file())){p.store(out,"xSxLabs HUD editor");}
  }catch(Exception ignored){}
 }
 private static int resolve(int saved,int fallback,int screen,int extent){
  if(saved<0)return clamp(fallback,0,Math.max(0,screen-extent));
  return clamp((int)((long)saved*Math.max(0,screen-extent)/10000),
               0,Math.max(0,screen-extent));
 }
 private static int norm(int pos,int screen,int extent){
  int max=Math.max(1,screen-extent);
  return clamp((int)((long)clamp(pos,0,max)*10000/max),0,10000);
 }
 public static int mapX(int fallback,int width,int extent){
  ensure();return resolve(mapX,fallback,width,extent);
 }
 public static int mapY(int fallback,int height,int extent){
  ensure();return resolve(mapY,fallback,height,extent);
 }
 public static int infoX(int fallback,int width){
  ensure();return resolve(infoX,fallback,width,infoWidth());
 }
 public static int infoY(int fallback,int height,int extent){
  ensure();return resolve(infoY,fallback,height,extent);
 }
 public static float infoScale(){ensure();return infoSize/100f;}
 public static int infoWidth(){return Math.round(195f*infoScale());}
 public static void setMap(int x,int y,int width,int height,int w,int h){
  ensure();mapX=norm(x,width,w);mapY=norm(y,height,h);save();
 }
 public static void setInfo(int x,int y,int width,int height,int h){
  ensure();infoX=norm(x,width,infoWidth());infoY=norm(y,height,h);save();
 }
 public static void changeInfoSize(int delta){
  ensure();infoSize=clamp(infoSize+delta,60,200);save();
 }
 public static void reset(){
  ensure();mapX=mapY=infoX=infoY=-1;infoSize=100;save();
 }
}''')

# Independent map and informational rows. Preserve legacy corner fallback
# until a user drags a component in the editor.
client=J/"client/V178ClaimsClient.java"
s=client.read_text(encoding="utf-8")
target="if(miniCorner>=2)oy+=infoRows*lineHeight;"
assert s.count(target)==1,("B1780_HUD_Y",s.count(target))
s=s.replace(target,target+'''
    ox=V178HudPlacement.mapX(ox,mc.getWindow().getGuiScaledWidth(),miniWidth);
    oy=V178HudPlacement.mapY(oy,mc.getWindow().getGuiScaledHeight(),7*step+22);''',1)
target="int lineHeight=Math.max(9,Math.round(step*.44f));"
assert s.count(target)==1,("B1780_LINE_HEIGHT",s.count(target))
s=s.replace(target,"int lineHeight=Math.max(9,Math.round(11f*V178HudPlacement.infoScale()));",1)
target="int infoY=miniCorner>=2?oy-infoRows*lineHeight+5:oy+7*step+20;"
assert s.count(target)==1,("B1780_INFO_Y",s.count(target))
s=s.replace(target,'''int infoY=V178HudPlacement.infoY(
      miniCorner>=2?oy-infoRows*lineHeight+5:oy+7*step+20,
      mc.getWindow().getGuiScaledHeight(),infoRows*lineHeight+8);''',1)
assert s.count("ox+4,infoY")>=2,("B1780_INFO_X",s.count("ox+4,infoY"))
s=s.replace("ox+4,infoY","V178HudPlacement.infoX(ox+4,mc.getWindow().getGuiScaledWidth()),infoY")
client.write_text(s,encoding="utf-8")
patch("client/V178MapInfo.java",
'''   float scale=Math.max(.65f,Math.min(1.6f,V178MiniPreferences.step()/24.0f));
   scale=Math.min(scale,Math.max(.35f,
       (7f*V178MiniPreferences.step()-8f)/Math.max(1,mc.font.width(value))));''',
'''   float scale=V178HudPlacement.infoScale();''')

emit("client/V178HudEditorScreen.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;

/** B1780 interactive independent map/info HUD placement and scaling. */
public final class V178HudEditorScreen extends Screen{
 private final Screen previous;
 private int mapX,mapY,infoX,infoY,drag,grabX,grabY;
 private int mapW(){return 7*V178MiniPreferences.step()+7;}
 private int mapH(){return 7*V178MiniPreferences.step()+22;}
 private int infoW(){return V178HudPlacement.infoWidth();}
 private int infoH(){return Math.max(40,Math.round(50*V178HudPlacement.infoScale()));}
 public V178HudEditorScreen(Screen prev){
  super(Component.literal("xSxLabs HUD Editor"));previous=prev;
 }
 @Override protected void init(){
  int mw=mapW(),mh=mapH();
  mapX=V178HudPlacement.mapX(Math.max(0,width-mw-9),width,mw);
  mapY=V178HudPlacement.mapY(9,height,mh);
  infoX=V178HudPlacement.infoX(mapX,width);
  infoY=V178HudPlacement.infoY(mapY+mh+4,height,infoH());
  addRenderableWidget(Button.builder(Component.literal("Save / Done"),b->onClose())
      .bounds(width/2-103,height-29,98,20).build());
  addRenderableWidget(Button.builder(Component.literal("Reset HUD"),b->{
    V178HudPlacement.reset();
    V178MiniPreferences.adjustSize(24-V178MiniPreferences.step());
    rebuildWidgets();
  }).bounds(width/2+5,height-29,98,20).build());
 }
 private static int clamp(int n,int min,int max){
  return Math.max(min,Math.min(max,n));
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  g.fill(0,0,width,height,0x8a09131f);
  int mw=mapW(),mh=mapH(),iw=infoW(),ih=infoH();
  g.fill(mapX,mapY,mapX+mw,mapY+mh,0xaa192e40);
  g.outline(mapX,mapY,mw,mh,0xff56def5);
  int centerX=mapX+mw/2,centerY=mapY+mh/2;
  int radius=Math.min(mw,mh)/2-9;
  g.fill(centerX-radius,centerY-radius,centerX+radius,centerY+radius,0xff365166);
  g.text(font,"MINIMAP",mapX+5,mapY+5,0xffb5f2fc);
  g.fill(centerX-2,centerY-2,centerX+3,centerY+3,0xfff5f8fa);
  g.fill(infoX,infoY,infoX+iw,infoY+ih,0xaa13293a);
  g.outline(infoX,infoY,iw,ih,0xffbf83f7);
  float scale=V178HudPlacement.infoScale();
  g.pose().pushMatrix();
  g.pose().translate(infoX+6,infoY+5);
  g.pose().scale(scale,scale);
  g.text(font,"XYZ  128  70  -240",0,0,0xfff7efff);
  g.text(font,"Biome: Windswept Hills",0,11,0xfff7efff);
  g.text(font,"Day: 72",0,22,0xfff7efff);
  g.pose().popMatrix();
  g.text(font,"Drag the map and the information panel separately",
       width/2-150,17,0xffe5f8fc);
  g.text(font,"Mouse wheel over either panel: resize that panel",
       width/2-150,31,0xffb7d9ec);
 }
 @Override public boolean mouseClicked(MouseButtonEvent e,boolean dbl){
  if(super.mouseClicked(e,dbl))return true;
  if(e.button()!=0)return false;
  int x=(int)e.x(),y=(int)e.y();
  if(x>=infoX&&x<infoX+infoW()&&y>=infoY&&y<infoY+infoH()){
    drag=2;grabX=x-infoX;grabY=y-infoY;return true;
  }
  if(x>=mapX&&x<mapX+mapW()&&y>=mapY&&y<mapY+mapH()){
    drag=1;grabX=x-mapX;grabY=y-mapY;return true;
  }
  return false;
 }
 @Override public boolean mouseDragged(MouseButtonEvent e,double dx,double dy){
  if(drag==0)return super.mouseDragged(e,dx,dy);
  if(drag==1){
   mapX=clamp((int)e.x()-grabX,0,Math.max(0,width-mapW()));
   mapY=clamp((int)e.y()-grabY,0,Math.max(0,height-mapH()));
  }else{
   infoX=clamp((int)e.x()-grabX,0,Math.max(0,width-infoW()));
   infoY=clamp((int)e.y()-grabY,0,Math.max(0,height-infoH()));
  }
  return true;
 }
 @Override public boolean mouseReleased(MouseButtonEvent e){
  if(drag==0)return super.mouseReleased(e);
  if(drag==1)V178HudPlacement.setMap(mapX,mapY,width,height,mapW(),mapH());
  else V178HudPlacement.setInfo(infoX,infoY,width,height,infoH());
  drag=0;return true;
 }
 @Override public boolean mouseScrolled(double x,double y,double horizontal,double vertical){
  int delta=vertical>0?2:vertical<0?-2:0;
  if(delta==0)return super.mouseScrolled(x,y,horizontal,vertical);
  if(x>=mapX&&x<mapX+mapW()&&y>=mapY&&y<mapY+mapH()){
   V178MiniPreferences.adjustSize(delta);
   mapX=clamp(mapX,0,Math.max(0,width-mapW()));
   mapY=clamp(mapY,0,Math.max(0,height-mapH()));
   V178HudPlacement.setMap(mapX,mapY,width,height,mapW(),mapH());return true;
  }
  if(x>=infoX&&x<infoX+infoW()&&y>=infoY&&y<infoY+infoH()){
   V178HudPlacement.changeInfoSize(delta*5);
   infoX=clamp(infoX,0,Math.max(0,width-infoW()));
   infoY=clamp(infoY,0,Math.max(0,height-infoH()));
   V178HudPlacement.setInfo(infoX,infoY,width,height,infoH());return true;
  }
  return super.mouseScrolled(x,y,horizontal,vertical);
 }
 @Override public void onClose(){
  if(drag==1)V178HudPlacement.setMap(mapX,mapY,width,height,mapW(),mapH());
  if(drag==2)V178HudPlacement.setInfo(infoX,infoY,width,height,infoH());
  Minecraft.getInstance().setScreen(previous);
 }
 @Override public boolean isPauseScreen(){return false;}
}''')
settings=J/"client/V178MapSettingsScreen.java"
src=settings.read_text(encoding="utf-8")
# Split the existing full-width Back row into two guaranteed non-overlapping
# buttons and keep the same page-switching and all existing options.
match=re.search(r'(?m)^  addRenderableWidget\(Button\.builder\(Component\.literal\("Back to Map"\),\s*\n\s*b->onClose\(\)\)\.bounds\(left,top\+155,2\*w\+6,20\)\.build\(\);',src)
assert match,("B1780_SETTINGS_NAV","back button layout changed")
src=src[:match.start()]+'''  addRenderableWidget(Button.builder(Component.literal("HUD EDITOR"),
       b->Minecraft.getInstance().setScreen(new V178HudEditorScreen(this)))
       .bounds(left,top+155,w,20).build());
  addRenderableWidget(Button.builder(Component.literal("Back to Map"),
       b->onClose()).bounds(left+w+6,top+155,w,20).build());'''+src[match.end():]
settings.write_text(src,encoding="utf-8")

# Original futuristic mining machine: fewer readable armored pieces, a large
# forward cutter, two obvious power modules and a simple top status display.
# 100% original procedural art; no external textures or copied mod assets.
model=R/"models/block/mining_builder.json"
body=json.loads(model.read_text(encoding="utf-8"))
parts=[]
def box(lo,hi,texture):
 assert all(0<=x<=16 for x in (*lo,*hi))
 assert all(x<y for x,y in zip(lo,hi))
 parts.append({"from":list(lo),"to":list(hi),
  "faces":{face:{"texture":"#"+texture}
   for face in ("north","south","east","west","up","down")}})
box((1,0,1),(15,2,15),"hydraulic")           # foot
box((2,2,2),(14,12,15),"shell")               # coherent chassis
box((3,11,3),(13,14,14),"panel")              # broad top armour
box((4,14,5),(12,15,13),"trim")               # top access
box((5,15,6),(11,16,12),"display")            # status screen
for side in (0,14):
 box((side,3,4),(side+2,12,13),"panel")       # power bay mounts
 box((side+.3,5,6),(side+1.7,10,11),"core") # bright power tubes
 box((side,3,3),(side+2,4,14),"trim")
 box((side,11,3),(side+2,12,14),"trim")
box((3,3,1),(13,11,4),"hydraulic")            # front drill housing
box((4,4,.6),(12,10,2.5),"trim")             # front guard
box((5,5,.25),(11,9,1.5),"blade")            # bit outer
box((6,5.5,0),(10,8.5,1.1),"hydraulic")     # bit inner
box((7,6.2,0),(9,7.8,.6),"core")            # cutting eye
for x in (3,11):
 box((x,4,0),(x+2,5,4),"blade")               # teeth
 box((x,9,0),(x+2,10,4),"blade")
box((6,3,0),(10,4,4),"blade")                 # lower guard
box((6,10,0),(10,11,4),"blade")               # upper guard
box((4,4,14),(12,11,16),"vent")              # rear output
box((6,5,15.3),(10,9.5,16),"display")
body["elements"]=parts
body["ambientocclusion"]=True
assert 20<=len(parts)<=40,len(parts)
model.write_text(json.dumps(body,indent=2)+"\n",encoding="utf-8")

# Clean 16px materials: low-noise deliberate shapes, no checkerboard overload.
SIZE=16
palette={
 "shell":(38,35,55),"panel":(36,50,70),"trim":(99,48,148),
 "core":(26,170,199),"front":(31,47,68),"vent":(20,27,42),
 "sensor":(63,208,230),"display":(9,56,80),"blade":(163,191,204),
 "warning":(173,108,40),"hydraulic":(85,110,129)}
def pixel(kind,x,y):
 r,g,b=palette[kind]
 if kind=="core":
  if x in (0,15) or y in (0,15):r,g,b=24,42,61
  elif 3<=x<=12 and 3<=y<=12:r,g,b=64,213,226
 elif kind=="display":
  if 3<=x<=12 and 6<=y<=9:r,g,b=58,222,240
 elif kind=="vent":
  if y%4==0:r,g,b=55,82,99
 elif kind=="blade":
  if (x+y)%8==0:r,g,b=218,237,243
 elif kind=="trim":
  if x in (2,13) or y in (2,13):r,g,b=137,77,184
 elif kind in ("shell","panel"):
  if x in (2,13) or y in (2,13):r,g,b=[min(255,c+12) for c in (r,g,b)]
 elif kind=="hydraulic":
  if x in (4,11):r,g,b=126,151,169
 if x in (0,15) or y in (0,15):
  r,g,b=[max(0,int(v*.68)) for v in (r,g,b)]
 return bytes((r,g,b,255))
def chunk(tag,data):
 return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
for kind in palette:
 raw=bytearray()
 for y in range(SIZE):
  raw.append(0)
  for x in range(SIZE):raw.extend(pixel(kind,x,y))
 png=(b"\x89PNG\r\n\x1a\n"
   +chunk(b"IHDR",struct.pack(">IIBBBBB",SIZE,SIZE,8,6,0,0,0))
   +chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b""))
 (R/"textures/block"/("mining_builder_"+kind+".png")).write_bytes(png)

for rel,token in {
 "client/V178MapMarkers.java":"B1780_COMPACT_SKIN_ARROW",
 "client/V178HudEditorScreen.java":"mouseDragged(MouseButtonEvent",
 "client/V178HudPlacement.java":"setInfo(int x,int y",
 "client/V178ClaimsClient.java":"V178HudPlacement.infoX(",
 "client/V178TerrainMap.java":"vegetation<4",
 "mining/V178MiningBuilderMenu.java":"moveItemStackTo(held,1,2,false)",
 "mining/V178MiningBuilderBE.java":"ObsidianNetwork.SPEED_UPGRADE.get()",
}.items():assert token in (J/rel).read_text(encoding="utf-8"),rel
print("B1780_V11_COMPACT_MARKER_TERRAIN_MINER_SPEED_HUD_EDITOR_VISUALS_PASS")
