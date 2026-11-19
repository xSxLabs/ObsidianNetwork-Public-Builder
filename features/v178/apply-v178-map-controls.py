#!/usr/bin/env python3
"""B1666 Xaero-inspired map readability, map shape/scale/position and FPS-bounded mobs.
No assets, Java or source code from FTB/Xaero. Existing claim protocol unchanged.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf8")
 assert s.count(old)==1,("B1666_MAP_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf8")
def emit(rel,text):
 p=J/rel;assert not p.exists(),("B1666_MAP_DUPLICATE",rel)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf8")

# Raise visual resolution from 4x4 to 8x8, retain the old explored-map file
# format and resample it rather than discarding user exploration history.
patch("client/V178TerrainMap.java","public static final int RES=4;","public static final int RES=8;")
patch("client/V178TerrainMap.java",
'''    int wx=(cx<<4)+x*4+2,wz=(cz<<4)+z*4+2;''',
'''    int wx=(cx<<4)+x*2+1,wz=(cz<<4)+z*2+1;''')
patch("client/V178TerrainMap.java",
'''    // Match ordinary Minecraft map shading without constructing MapItemSavedData.
    double shade=1.0+((y&7)-3)*.024;''',
'''    // Directional slope shading, avoiding the harsh height-bit color bands.
    int east=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx+1,wz)-1;
    int south=world.getHeight(Heightmap.Types.WORLD_SURFACE,wx,wz+1)-1;
    double shade=Math.max(.69,Math.min(1.11,.97+(y-east)*.045+(y-south)*.045));''')
patch("client/V178TerrainMap.java",
'''  // Scan a radius of 5 (121 chunks) across 121 client ticks.
  int index=roundRobin++%121;
  sample(world,cx+(index%11)-5,cz+(index/11)-5);''',
'''  // Explore the ENTIRE visible 25x25 viewport, never loading absent chunks.
  // Bounded at three chunks per tick including the focus, never in render.
  for(int n=0;n<2;n++){
   int index=roundRobin++%625;
   sample(world,cx+(index%25)-12,cz+(index/25)-12);
  }''')
patch("client/V178TerrainMap.java",
'''     out.writeInt(0x58535838);out.writeInt(data.size());''',
'''     out.writeInt(0x58535839);out.writeInt(data.size());''')
patch("client/V178TerrainMap.java",
'''    if(in.readInt()!=0x58535838)return;
    int count=in.readInt();''',
'''    int format=in.readInt();
    if(format!=0x58535838&&format!=0x58535839)return;
    int count=in.readInt();''')
patch("client/V178TerrainMap.java",
'''     int[] pixels=new int[RES*RES];
     for(int j=0;j<pixels.length;j++)pixels[j]=in.readInt();
     found.put(pos,pixels);''',
'''     int[] pixels=new int[RES*RES];
     if(format==0x58535838){
      for(int y=0;y<4;y++)for(int x=0;x<4;x++){
       int color=in.readInt();
       for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++)
        pixels[(y*2+dy)*RES+x*2+dx]=color;
      }
      dirty=true; // on next bounded save, upgrade the old data in-place
     }else for(int j=0;j<pixels.length;j++)pixels[j]=in.readInt();
     found.put(pos,pixels);''')

emit("client/V178MiniPreferences.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import java.nio.file.*;
import java.util.Properties;

/** Pure client UI display choices. No world/simulation/network changes. */
public final class V178MiniPreferences{
 private V178MiniPreferences(){}
 private static boolean loaded,circle=true,mobs=true,hostileOnly=false;
 private static int size=1,corner=-1;
 private static Path path(){
  return Minecraft.getInstance().gameDirectory.toPath().resolve("config")
      .resolve("xsxlabs-worldmap").resolve("minimap-display.properties");
 }
 private static void ensure(){
  if(loaded)return;loaded=true;
  if(!Files.isRegularFile(path()))return;
  try(var in=Files.newInputStream(path())){
   var p=new Properties();p.load(in);
   circle=Boolean.parseBoolean(p.getProperty("circle","true"));
   mobs=Boolean.parseBoolean(p.getProperty("mobs","true"));
   hostileOnly=Boolean.parseBoolean(p.getProperty("hostileOnly","false"));
   size=Integer.parseInt(p.getProperty("size","1"));
   corner=Integer.parseInt(p.getProperty("corner","-1"));
   if(size<0||size>2)size=1;
   if(corner< -1||corner>3)corner=-1;
  }catch(Exception ex){System.err.println("[xSxLabs] minimap visual prefs: "+ex);}
 }
 private static void save(){
  try{
   Path target=path();Files.createDirectories(target.getParent());
   Path tmp=Files.createTempFile(target.getParent(),"xsx-mini-",".tmp");
   try{
    var p=new Properties();
    p.setProperty("circle",Boolean.toString(circle));
    p.setProperty("mobs",Boolean.toString(mobs));
    p.setProperty("hostileOnly",Boolean.toString(hostileOnly));
    p.setProperty("size",Integer.toString(size));
    p.setProperty("corner",Integer.toString(corner));
    try(var out=Files.newOutputStream(tmp)){p.store(out,"xSxLabs minimap visual settings");}
    try{Files.move(tmp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
    catch(AtomicMoveNotSupportedException ex){Files.move(tmp,target,StandardCopyOption.REPLACE_EXISTING);}
   }finally{Files.deleteIfExists(tmp);}
  }catch(Exception ex){System.err.println("[xSxLabs] minimap visual prefs save: "+ex);}
 }
 public static boolean circle(){ensure();return circle;}
 public static boolean mobs(){ensure();return mobs;}
 public static boolean hostileOnly(){ensure();return hostileOnly;}
 public static int step(){ensure();return switch(size){case 0->10;case 2->16;default->12;};}
 public static int corner(){ensure();return corner;}
 public static String shapeLabel(){return circle()?"ROUND":"SQUARE";}
 public static String sizeLabel(){ensure();return switch(size){case 0->"SMALL";case 2->"LARGE";default->"NORMAL";};}
 public static String positionLabel(){ensure();return switch(corner){
  case 0->"TOP LEFT";case 1->"TOP RIGHT";case 2->"BOTTOM LEFT";
  case 3->"BOTTOM RIGHT";default->"AUTO";};}
 public static void toggleShape(){ensure();circle=!circle;save();}
 public static void toggleMobs(){ensure();mobs=!mobs;save();}
 public static void toggleHostileOnly(){ensure();hostileOnly=!hostileOnly;save();}
 public static void cycleSize(){ensure();size=(size+1)%3;save();}
 public static void cycleCorner(){ensure();corner=corner>=3?-1:corner+1;save();}
 /** Four tiles at the corners are omitted to yield a clean, round/octagonal mask. */
 public static boolean visible(int dx,int dz){
  return !circle()||dx*dx+dz*dz<=10;
 }
}
''')
emit("client/V178MapMobCache.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import java.util.ArrayList;
import java.util.List;

/** Client-side radar: bounded 10-tick sample, <=48 live markers, no packets. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178MapMobCache{
 private V178MapMobCache(){}
 private record Mark(int x,int z,boolean hostile){}
 private static List<Mark> marks=List.of();
 private static long lastTick=Long.MIN_VALUE;
 @SubscribeEvent public static void tick(ClientTickEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null){marks=List.of();lastTick=Long.MIN_VALUE;return;}
  if(!V178MiniPreferences.mobs()){marks=List.of();return;}
  long time=mc.level.getGameTime();
  if(lastTick!=Long.MIN_VALUE&&time>=lastTick&&time-lastTick<10)return;
  lastTick=time;
  var out=new ArrayList<Mark>(48);
  for(var e:mc.level.getEntities(mc.player,mc.player.getBoundingBox().inflate(96),
          target->target instanceof Mob)){
   if(out.size()>=48)break;
   if(!(e instanceof Mob))continue;
   boolean hostile=e instanceof Enemy;
   if(V178MiniPreferences.hostileOnly()&&!hostile)continue;
   out.add(new Mark(e.blockPosition().getX(),e.blockPosition().getZ(),hostile));
  }
  marks=List.copyOf(out);
 }
 public static void drawMini(GuiGraphicsExtractor g,int left,int top,int cx,int cz,int step){
  if(!V178MiniPreferences.mobs())return;
  for(Mark m:marks){
   int dx=(m.x()>>4)-cx,dz=(m.z()>>4)-cz;
   if(dx< -3||dx>3||dz< -3||dz>3||!V178MiniPreferences.visible(dx,dz))continue;
   int x=left+(dx+3)*step+Math.floorMod(m.x(),16)*step/16;
   int y=top+(dz+3)*step+Math.floorMod(m.z(),16)*step/16;
   g.fill(x-1,y-1,x+2,y+2,m.hostile()?0xffff5e63:0xffffff80);
  }
 }
 public static void drawWorld(GuiGraphicsExtractor g,int x0,int y0,
                              int cx,int cz,int tile,int diameter){
  if(!V178MiniPreferences.mobs())return;
  int half=diameter/2;
  for(Mark m:marks){
   int dx=(m.x()>>4)-cx,dz=(m.z()>>4)-cz;
   if(dx< -half||dx>half||dz< -half||dz>half)continue;
   int x=x0+(dx+half)*tile+Math.floorMod(m.x(),16)*tile/16;
   int y=y0+(dz+half)*tile+Math.floorMod(m.z(),16)*tile/16;
   g.fill(x-1,y-1,x+2,y+2,m.hostile()?0xffff5e63:0xffffff80);
  }
 }
}
''')
# Minimap: force the same vertical/horizontal tile step, variable size and
# respect an explicitly chosen corner (Auto continues to avoid JARVIS).
patch("client/V178ClaimsClient.java",
'''  int miniHeight=97+infoRows*10,miniCorner=1;''',
'''  int step=V178MiniPreferences.step();
  int miniWidth=7*step+7,miniHeight=7*step+20+infoRows*10,miniCorner=1;''')
patch("client/V178ClaimsClient.java",
'''  int ox=V178HudLayout.x(miniCorner,mc.getWindow().getGuiScaledWidth(),91);
  int oy=V178HudLayout.y(miniCorner,mc.getWindow().getGuiScaledHeight(),miniHeight);''',
'''  if(V178MiniPreferences.corner()>=0)miniCorner=V178MiniPreferences.corner();
  int ox=V178HudLayout.x(miniCorner,mc.getWindow().getGuiScaledWidth(),miniWidth);
  int oy=V178HudLayout.y(miniCorner,mc.getWindow().getGuiScaledHeight(),miniHeight);''')
patch("client/V178ClaimsClient.java",
'''   V178UiTheme.miniFrame(g,ox-3,oy-4,94,miniHeight+8);''',
'''   V178UiTheme.miniFrame(g,ox-3,oy-4,miniWidth+3,miniHeight+8);''')
patch("client/V178ClaimsClient.java",
'''     int x=ox+4+(dx+3)*12,y=oy+15+(dz+3)*11;
     int state=Byte.toUnsignedInt(state(last,cx+dx,cz+dz));''',
'''     if(!V178MiniPreferences.visible(dx,dz))continue;
     int x=ox+4+(dx+3)*step,y=oy+15+(dz+3)*step;
     int state=Byte.toUnsignedInt(state(last,cx+dx,cz+dz));''')
patch("client/V178ClaimsClient.java",
'''     if(drawTerrain)V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,11);
     else g.fill(x,y,x+11,y+11,0xff1c2530);
     if(drawClaims)V178TerrainMap.drawClaim(g,x,y,11,''',
'''     if(drawTerrain)V178TerrainMap.draw(mc.level,g,cx+dx,cz+dz,x,y,step-1);
     else g.fill(x,y,x+step-1,y+step-1,0xff1c2530);
     if(drawClaims)V178TerrainMap.drawClaim(g,x,y,step-1,''')
patch("client/V178ClaimsClient.java",
'''      g.fill(x+7,y+8,x+10,y+10,0xff66ee71);''',
'''      g.fill(x+step-4,y+step-4,x+step-1,y+step-1,0xff66ee71);''')
patch("client/V178ClaimsClient.java",
'''    if(option("waypoints"))V178Waypoints.drawMini(mc.level,g,cx,cz,ox+4,oy+15);
    if(option("player"))g.fill(ox+43,oy+45,ox+48,oy+50,0xffffffff);''',
'''    if(option("waypoints"))V178Waypoints.drawMini(mc.level,g,cx,cz,ox+4,oy+15,step);
    V178MapMobCache.drawMini(g,ox+4,oy+15,cx,cz,step);
    if(option("player")){
     int px=ox+4+3*step+Math.floorMod(mc.player.blockPosition().getX(),16)*step/16;
     int py=oy+15+3*step+Math.floorMod(mc.player.blockPosition().getZ(),16)*step/16;
     g.fill(px-3,py-3,px+4,py+4,0xff07232b);
     g.fill(px-2,py-2,px+3,py+3,0xfffdf4b2);
     g.fill(px,py-4,px+1,py+1,0xffffffff);
    }''')
patch("client/V178ClaimsClient.java",
'''    int infoY=oy+99;''',
'''    int infoY=oy+7*step+22;''')
patch("client/V178Waypoints.java",
'''                              int cx,int cz,int ox,int oy){''',
'''                              int cx,int cz,int ox,int oy,int step){''')
patch("client/V178Waypoints.java",
'''   int x=ox+(dx+3)*12+5,y=oy+(dz+3)*11+5;''',
'''   if(!V178MiniPreferences.visible(dx,dz))continue;
   int x=ox+(dx+3)*step+step/2,y=oy+(dz+3)*step+step/2;''')

# Full-screen player marker at exact block coordinate, not coarse chunk center.
patch("client/V178ClaimsMapScreen.java",
'''     int px=x0+dx*tile+tile/2,py=y0+dz*tile+tile/2;
     g.fill(px-2,py-2,px+3,py+3,0xfffceca8);''',
'''     int px=x0+dx*tile+Math.floorMod(p.blockPosition().getX(),16)*tile/16;
     int py=y0+dz*tile+Math.floorMod(p.blockPosition().getZ(),16)*tile/16;
     g.fill(px-3,py-3,px+4,py+4,0xff092a36);
     g.fill(px-2,py-2,px+3,py+3,0xfffdf4af);
     g.fill(px,py-4,px+1,py+1,0xffffffff);''')
# Draw entities after the map layer, before waypoint icons and location marker.
patch("client/V178ClaimsMapScreen.java",
'''  if(V178ClaimsClient.option("map_waypoints"))
     V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile,DIAMETER);''',
'''  V178MapMobCache.drawWorld(g,x0,y0,cx,cz,tile,DIAMETER);
  if(V178ClaimsClient.option("map_waypoints"))
     V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile,DIAMETER);''')

# Expand settings inside the existing xSxLabs panel, keep the original toggles.
patch("client/V178MapSettingsScreen.java",
'''   addRenderableWidget(Button.builder(Component.literal("Back to Map"),button->onClose())
       .bounds(width/2-75,y+162,150,20).build());''',
'''   addRenderableWidget(Button.builder(Component.literal("Shape: "+V178MiniPreferences.shapeLabel()),b->{
      V178MiniPreferences.toggleShape();rebuildWidgets();
     }).bounds(left,y+163,152,20).build());
   addRenderableWidget(Button.builder(Component.literal("Size: "+V178MiniPreferences.sizeLabel()),b->{
      V178MiniPreferences.cycleSize();rebuildWidgets();
     }).bounds(left+158,y+163,152,20).build());
   addRenderableWidget(Button.builder(Component.literal("Position: "+V178MiniPreferences.positionLabel()),b->{
      V178MiniPreferences.cycleCorner();rebuildWidgets();
     }).bounds(left,y+185,152,20).build());
   addRenderableWidget(Button.builder(Component.literal("Show Mobs: "+(V178MiniPreferences.mobs()?"ON":"OFF")),b->{
      V178MiniPreferences.toggleMobs();rebuildWidgets();
     }).bounds(left+158,y+185,152,20).build());
   addRenderableWidget(Button.builder(Component.literal("Hostile Only: "+(V178MiniPreferences.hostileOnly()?"ON":"OFF")),b->{
      V178MiniPreferences.toggleHostileOnly();rebuildWidgets();
     }).bounds(left,y+207,152,20).build());
   addRenderableWidget(Button.builder(Component.literal("Back to Map"),button->onClose())
       .bounds(left+158,y+207,152,20).build());''')
patch("client/V178MapSettingsScreen.java",
'''  V178UiTheme.panel(g,width/2-164,Math.max(7,height/2-128),328,232);''',
'''  V178UiTheme.panel(g,width/2-164,Math.max(7,height/2-128),328,284);''')

for rel in ("client/V178TerrainMap.java","client/V178ClaimsClient.java",
            "client/V178MapSettingsScreen.java"):
 assert "V178MiniPreferences" in (J/rel).read_text(),("B1666_MAP_MISSING",rel)
print("B1666_XAERO_INSPIRED_8X8_MAP_PLAYER_MOBS_SHAPE_SIZE_CORNER_LEGACY_CACHE_PASS")
