#!/usr/bin/env python3
"""B1730: detailed, GPU-cached circular minimap, fully adjustable controls
and per-player customizable Action Wheel. Runs after B1725.
No extra world/terrain reads during HUD rendering and no server packets.
"""
import os,re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def update(rel, transform):
    p=J/rel
    assert p.is_file(),("B1730_MISSING",rel)
    old=p.read_text(encoding="utf-8")
    new=transform(old)
    assert new!=old,("B1730_UNCHANGED",rel)
    p.write_text(new,encoding="utf-8")
def replace(s,a,b,number=1):
    assert s.count(a)==number,("B1730_ANCHOR_DRIFT",a[:140],s.count(a))
    return s.replace(a,b,number)
def regex(s,pattern,repl):
    out,n=re.subn(pattern,repl,s,flags=re.S)
    assert n==1,("B1730_REGEX_DRIFT",pattern[:100],n)
    return out
def emit(rel,s):
    p=J/rel
    assert not p.exists(),("B1730_DUPLICATE",rel)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding="utf-8")

# Personalization is independent of resource packs and never changes ticks.
def prefs(s):
    s=replace(s,"private static int size=1,corner=-1,zoom=0,mobRange=2;",
        "private static int size=1,corner=-1,zoom=0,mobRange=2,customStep=24,fineZoom=100;")
    s=replace(s,'   zoom=Integer.parseInt(p.getProperty("zoom","0"));',
        '''   zoom=Integer.parseInt(p.getProperty("zoom","0"));
   customStep=Integer.parseInt(p.getProperty("customStep","24"));
   fineZoom=Integer.parseInt(p.getProperty("fineZoom","100"));''')
    s=replace(s,'   if(mobRange<0||mobRange>3)mobRange=2;',
        '''   if(mobRange<0||mobRange>3)mobRange=2;
   customStep=Math.max(12,Math.min(48,customStep));
   fineZoom=Math.max(100,Math.min(200,fineZoom));''')
    s=replace(s,'    p.setProperty("zoom",Integer.toString(zoom));',
        '''    p.setProperty("zoom",Integer.toString(zoom));
    p.setProperty("customStep",Integer.toString(customStep));
    p.setProperty("fineZoom",Integer.toString(fineZoom));''')
    # Preserve legacy size cycling and existing old settings contracts.
    s=replace(s,'public static int step(){ensure();return switch(size){case 0->12;case 2->20;default->16;};}',
        '''public static int step(){ensure();return customStep;}
 public static void adjustSize(int delta){ensure();customStep=Math.max(12,Math.min(48,customStep+delta));save();}
 public static void adjustFineZoom(int delta){ensure();fineZoom=Math.max(100,Math.min(200,fineZoom+delta));save();}
 public static int cropPixels(){ensure();return Math.max(16,
       visibleChunks()*16*100/fineZoom);}
 public static int markerStep(int tile){ensure();return Math.max(1,7*tile*16/cropPixels());}
 public static int viewPixelSize(){return 7*step();}
 public static String detailedZoomLabel(){return String.format(java.util.Locale.ROOT,
      "%.2fx",7.0*16/cropPixels());}''')
    s=replace(s,'public static String sizeLabel(){ensure();return switch(size){case 0->"SMALL";case 2->"LARGE";default->"NORMAL";};}',
      '''public static String sizeLabel(){return viewPixelSize()+" px";}''')
    s=replace(s,'public static void cycleSize(){ensure();size=(size+1)%3;save();}',
      '''public static void cycleSize(){ensure();size=(size+1)%3;
  customStep=switch(size){case 0->16;case 2->36;default->24;};save();}''')
    # Old discrete zoom buttons kept, fine controls add precise 10% steps.
    return s
update("client/V178MiniPreferences.java",prefs)

# More legible, distinct materials; exactly the same one surface lookup per
# world column already performed by 16x16 client tick sampling. Cached colors
# drive both minimap and world map. Modded terrain retains Minecraft map colors.
def detail(s):
    # Recolor already explored chunks once when loaded in this session.
    # Preserve old cached imagery until each chunk is refreshed at the
    # existing bounded sampler rate (not during GPU or GUI rendering).
    s=replace(s,''' private static int atlasRevision;''',
       ''' private static int atlasRevision;
 private static final Map<String,Set<Long>> RECOLORED=new HashMap<>();''')
    s=replace(s,'''  if(map.containsKey(key)||!world.hasChunk(cx,cz))return;''',
       '''  var refreshed=RECOLORED.computeIfAbsent(dim,k->new HashSet<>());
  if(!world.hasChunk(cx,cz)||(map.containsKey(key)&&refreshed.contains(key)))return;''')
    s=replace(s,'''  map.put(key,colors);dirty=true;''',
       '''  map.put(key,colors);dirty=true;
  refreshed.add(key);''')
    s=replace(s,'''  resetAtlas();atlasRevision=0;''',
       '''  resetAtlas();atlasRevision=0;RECOLORED.clear();''',number=2)
    s=replace(s,
       '   int color=world.getBlockState(block).getMapColor(world,block).col;',
       '''   var state=world.getBlockState(block);
   int color=state.getMapColor(world,block).col;
   if(state.getFluidState().is(net.minecraft.tags.FluidTags.WATER))
    color=0x276fba;
   else if(state.getFluidState().is(net.minecraft.tags.FluidTags.LAVA))
    color=0xf47725;
   else if(state.is(net.minecraft.world.level.block.Blocks.GRASS_BLOCK))
    color=0x57964c;
   else if(state.is(net.minecraft.world.level.block.Blocks.DIRT_PATH))
    color=0xa69770;
   else if(state.is(net.minecraft.world.level.block.Blocks.PODZOL))
    color=0x756047;
   else if(state.is(net.minecraft.world.level.block.Blocks.STONE))
    color=0x909298;
   else if(state.is(net.minecraft.world.level.block.Blocks.COBBLESTONE))
    color=0x83868b;
   else if(state.is(net.minecraft.world.level.block.Blocks.SAND))
    color=0xe6d39b;
   else if(state.is(net.minecraft.world.level.block.Blocks.RED_SAND))
    color=0xb87951;
   else if(state.is(net.minecraft.world.level.block.Blocks.SNOW)
        ||state.is(net.minecraft.world.level.block.Blocks.SNOW_BLOCK))
    color=0xeceff1;
   else if(state.is(net.minecraft.world.level.block.Blocks.ICE))
    color=0xb8d9e5;
   else if(state.is(net.minecraft.world.level.block.Blocks.SPRUCE_LEAVES)
        ||state.is(net.minecraft.world.level.block.Blocks.DARK_OAK_LEAVES))
    color=0x356c3e;
   else if(state.is(net.minecraft.world.level.block.Blocks.OAK_LEAVES)
        ||state.is(net.minecraft.world.level.block.Blocks.BIRCH_LEAVES))
    color=0x51934a;''')
    s=replace(s,
       '''    if(y>world.getSeaLevel()+15)shade*=.985;''',
       '''    if(y>world.getSeaLevel()+15)shade*=.985;
    // Stable, subtle ground micro-shading; never random per frame.
    int grain=(wx*73428767 ^ wz*9123671);
    shade*=1.0+((grain>>>7)&7)*.006-0.021;''')
    # GPU atlas mask must be computed against the *cropped viewport*, not
    # the old unzoomed atlas. This also bakes a lightweight round border into
    # the ONE uploaded texture, instead of painting hundreds of HUD squares.
    s=replace(s,'''  boolean round;
  long lastUpload=Long.MIN_VALUE;''',
        '''  boolean round;
  int cropVersion;
  long lastUpload=Long.MIN_VALUE;''')
    s=replace(s,'''   cx=Integer.MIN_VALUE;revision=Integer.MIN_VALUE;
   lastUpload=Long.MIN_VALUE;dimension="";''',
        '''   cx=Integer.MIN_VALUE;revision=Integer.MIN_VALUE;
   cropVersion=0;lastUpload=Long.MIN_VALUE;dimension="";''')
    s=replace(s,'''   if(texture!=null&&cx==centerX&&cz==centerZ&&revision==atlasRevision
      &&round==circle)return;''',
        '''   int crop=diameter==7?V178MiniPreferences.cropPixels():side;
   if(texture!=null&&cx==centerX&&cz==centerZ&&revision==atlasRevision
      &&round==circle&&cropVersion==crop)return;''')
    old='''   int radius=side/2;
   long radius2=(long)(radius-1)*(radius-1);'''
    s=replace(s,old,'''   double ringRadius=(crop-1)*.5;
   double innerRadius=Math.max(0,ringRadius-1.2);''')
    s=replace(s,'''     if(circle){
      long xx2=(long)(2*xx+1-side),yy2=(long)(2*yy+1-side);
      if(xx2*xx2+yy2*yy2>radius2*4)color=0;
     }''',
        '''     if(circle){
      double rx=xx+.5-side*.5,rz=yy+.5-side*.5;
      double distance2=rx*rx+rz*rz;
      if(distance2>ringRadius*ringRadius)color=0;
      else if(distance2>=innerRadius*innerRadius)color=0xffd7e5e9;
     }''')
    s=replace(s,'''   round=circle;lastUpload=tick;''',
        '''   round=circle;cropVersion=crop;lastUpload=tick;''')
    s=replace(s,'''   int source=diameter==7 ? V178MiniPreferences.visibleChunks()*RES : side;''',
        '''   int source=diameter==7 ? V178MiniPreferences.cropPixels() : side;''')
    # If zoom changes, texture refreshes on the regular 4-tick throttle.
    return s
update("client/V178TerrainMap.java",detail)

# Player = strong circular location with a directional triangle, preserving
# player-facing orientation. No textures, extra entities or world reads.
emit("client/V178MapMarkers.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.gui.GuiGraphicsExtractor;

public final class V178MapMarkers {
 private V178MapMarkers(){}
 public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
  // Dark outline, bright circular ring, legible from 100-300 px minimaps.
  g.fill(x-2,y-4,x+3,y-3,0xff061a25);
  g.fill(x-4,y-2,x-3,y+3,0xff061a25);
  g.fill(x+3,y-2,x+4,y+3,0xff061a25);
  g.fill(x-2,y+3,x+3,y+4,0xff061a25);
  g.fill(x-2,y-3,x+3,y-2,0xfff7f8fb);
  g.fill(x-3,y-2,x-2,y+3,0xfff7f8fb);
  g.fill(x+2,y-2,x+3,y+3,0xfff7f8fb);
  g.fill(x-2,y+2,x+3,y+3,0xfff7f8fb);
  g.fill(x-1,y-1,x+2,y+2,0xff22d4e9);
  double angle=Math.toRadians(yaw);
  double dx=-Math.sin(angle),dy=Math.cos(angle);
  int tipX=x+(int)Math.round(dx*7),tipY=y+(int)Math.round(dy*7);
  // 3px triangular arrowhead, not an unrelated off-center square.
  for(int step=0;step<3;step++){
   int px=tipX-(int)Math.round(dx*step);
   int py=tipY-(int)Math.round(dy*step);
   int side=step==0?0:step==1?1:2;
   for(int i=-side;i<=side;i++){
    int sx=px+(int)Math.round(-dy*i),sy=py+(int)Math.round(dx*i);
    g.fill(sx,sy,sx+1,sy+1,0xff091a27);
   }
  }
  g.fill(tipX,tipY,tipX+1,tipY+1,0xffffffff);
 }
}
''')

def mini(s):
    # Replace the obsolete chunk-coordinate title with exact live block XYZ.
    s=regex(s,r'g\.text\(mc\.font,showCoordinates\?.*?,ox\+3,oy\+2,0xffb2ecfa\);',
        '''g.text(mc.font,option("coords")?
     "X: "+mc.player.blockPosition().getX()+" Y: "+mc.player.blockPosition().getY()+
     " Z: "+mc.player.blockPosition().getZ():"xSxLabs MAP",
     ox+3,oy+2,0xffb2ecfa);''')
    # Keep original B1716 contract (markerStep=7*step/view) in comments for
    # debugging; actual projection is full fine-zoom-aware world-block scale.
    s=replace(s,"int markerStep=7*step/view;",
       '''int markerStep=V178MiniPreferences.markerStep(step);
  // Legacy: int markerStep=7*step/view;''')
    # Existing viewport chunk positions are clamped to visible square,
    # necessary at fine zoom when the atlas is cropped further.
    s=replace(s,
       '''     if(!V178MiniPreferences.visible(dx,dz))continue;''',
       '''     if(!V178MiniPreferences.visible(dx,dz))continue;''') if '''     if(!V178MiniPreferences.visible(dx,dz))continue;''' in s else s
    s=replace(s,
       '''     int x=ox+4+(dx+radius)*markerStep,y=oy+15+(dz+radius)*markerStep;''',
       '''     int x=ox+4+7*step/2+dx*markerStep-markerStep/2;
     int y=oy+15+7*step/2+dz*markerStep-markerStep/2;
     if(x>=ox+4+7*step||y>=oy+15+7*step
        ||x+markerStep<=ox+4||y+markerStep<=oy+15)continue;''')
    # The minimap's existing claim overlay toggle remains functional.
    # Only the full-screen claim mode receives the explicit chunk grid.
    s=replace(s,
      '''if(drawClaims)V178TerrainMap.drawClaim(g,x,y,markerStep,''',
      '''if(drawClaims)V178TerrainMap.drawClaim(g,x,y,markerStep,''')
    s=replace(s,
      '''     int px=ox+4+radius*markerStep+
         Math.floorMod(mc.player.blockPosition().getX(),16)*markerStep/16;
     int py=oy+15+radius*markerStep+
         Math.floorMod(mc.player.blockPosition().getZ(),16)*markerStep/16;''',
      '''     int px=ox+4+7*step/2+
         (Math.floorMod(mc.player.blockPosition().getX(),16)-8)*markerStep/16;
     int py=oy+15+7*step/2+
         (Math.floorMod(mc.player.blockPosition().getZ(),16)-8)*markerStep/16;''')
    s=regex(s,
       r'g\.fill\(px-3,py-3,px\+4,py\+4,0xff[0-9a-f]+\);.*?g\.fill\(hx-1,hz-1,hx\+2,hz\+2,0xffffffff\);',
       'V178MapMarkers.player(g,px,py,mc.player.getYRot());')
    # GPU circular texture already contains a light rim; remove opaque square.
    s=replace(s,
       '''V178UiTheme.miniFrame(g,ox-3,oy-4,miniWidth+3,miniHeight+8);''',
       '''// Circular border is baked into the cached GPU texture; no box frame.''')
    # Compass labels are cheap constant-screen overlays, not terrain samples.
    s=replace(s,'''    if(option("waypoints"))V178Waypoints.drawMini''',
       '''    if(V178MiniPreferences.circle()){
     int mid=7*step/2;
     g.text(mc.font,"N",ox+4+mid-2,oy+17,0xfff4f8fb);
     g.text(mc.font,"S",ox+4+mid-2,oy+15+7*step-11,0xfff4f8fb);
     g.text(mc.font,"W",ox+6,oy+15+mid-4,0xfff4f8fb);
     g.text(mc.font,"E",ox+4+7*step-10,oy+15+mid-4,0xfff4f8fb);
    }
    if(option("waypoints"))V178Waypoints.drawMini''')
    # Keep other text rows and settings fully intact.
    return s
update("client/V178ClaimsClient.java",mini)

def mobs(s):
    s=replace(s,'''   int tile=7*step/(2*r+1);''',
       '''   int tile=V178MiniPreferences.markerStep(step);''')
    s=replace(s,
       '''   int x=left+(dx+r)*tile+Math.floorMod(m.x(),16)*tile/16;
   int y=top+(dz+r)*tile+Math.floorMod(m.z(),16)*tile/16;''',
       '''   int x=left+7*step/2+(dx*16+Math.floorMod(m.x(),16)-8)*tile/16;
   int y=top+7*step/2+(dz*16+Math.floorMod(m.z(),16)-8)*tile/16;
   if(x<left||y<top||x>=left+7*step||y>=top+7*step)continue;''')
    s=s.replace('g.fill(x-1,y-1,x+2,y+2,m.hostile()?0xffff5e63:0xffffff80);',
      'g.fill(x,y,x+2,y+2,m.hostile()?0xfff76368:0xffd3e6a3);')
    return s
update("client/V178MapMobCache.java",mobs)

def waypoints(s):
    s=replace(s,'''   int tile=7*step/(2*r+1);''',
       '''   int tile=V178MiniPreferences.markerStep(step);''')
    s=replace(s,
       '''   int x=ox+(dx+r)*tile+tile/2,y=oy+(dz+r)*tile+tile/2;''',
       '''   int x=ox+7*step/2+(dx*16)*tile/16;
   int y=oy+7*step/2+(dz*16)*tile/16;
   if(x<ox||y<oy||x>=ox+7*step||y>=oy+7*step)continue;''')
    return s
update("client/V178Waypoints.java",waypoints)

def map_screen(s):
    s=regex(s,
       r'g\.fill\(px-3,py-3,px\+4,py\+4,0xff[0-9a-f]+\);.*?g\.fill\(hx-1,hz-1,hx\+2,hz\+2,0xffffffff\);',
       'V178MapMarkers.player(g,px,py,p.getYRot());')
    # Terrain without grid in World Map mode, explicit grid ONLY in claims.
    s=replace(s,'if(!grid||!showClaims)continue;',
       '''if(!showClaims)continue;''')
    s=replace(s,'  // Local position pointer (does not imply a chunk is loaded).',
       '''  // One lightweight 16x16 chunk line grid, ONLY when claiming.
  // No per-cell world lookup and fewer GUI calls than per-cell outlines.
  if(claiming&&grid&&tile>=5){
   for(int v=0;v<=DIAMETER;v++){
    int xx=x0+v*tile,yy=y0+v*tile;
    g.fill(xx,y0,xx+1,y0+w,0x5588b9c5);
    g.fill(x0,yy,x0+w,yy+1,0x5588b9c5);
   }
  }
  // Local position pointer (does not imply a chunk is loaded).''')
    # English map actions. Keep 1-to-1 layout widths and navigation callbacks.
    labels={"Weltkarte":"World Map","Zentrieren":"Center","Mini AN/AUS":"Mini ON/OFF",
            "+ Wegpunkt":"+ Waypoint","Wegpunkte":"Waypoints","Team (alt)":"Legacy Team",
            "Minimap-Optionen":"Map Settings","Hilfe":"Help"}
    for a,b in labels.items():
        key='nav("'+a+'"'
        if key in s:s=s.replace(key,'nav("'+b+'"',1)
    return s
update("client/V178ClaimsMapScreen.java",map_screen)

def settings(s):
    mapping={"Minimap anzeigen":"Show Minimap","Gelaende":"Terrain",
       "Spielermarker":"Player Marker","Claims anzeigen":"Claim Borders",
       "Chunkloading":"Loaded Chunks","Wegpunkte":"Waypoints",
       "XYZ-Koordinaten":"XYZ Coordinates","Chunk-Koordinaten":"Chunk Coordinates",
       "Spieltag":"Game Day","Welt-Gelaende":"World Terrain",
       "Welt-Claims":"World Claims","Welt-Wegpunkte":"World Waypoints",
       "Welt-Spieler":"World Player","ANZEIGEN":"DISPLAY","WELTKARTE":"WORLD MAP",
       "Minimap-Einstellungen":"Minimap Settings","Form: ":"Shape: ",
       "Groesse: ":"Size: ","Zurueck zur Karte":"Back to Map",
       "Nur Feinde: ":"Hostile Only: ","Mob-Reichweite: ":"Mob Range: ",
       "Einstellungen werden automatisch gespeichert":"Changes are saved automatically",
       "AN":"ON","AUS":"OFF"}
    # Apply exact label strings to avoid altering key identifiers (e.g. map_terrain).
    for a,b in mapping.items():
        s=s.replace('"'+a+'"','"'+b+'"')
    for a,b in [('"Form: "','"Shape: "'),('"Groesse: "','"Size: "'),
                ('"Nur Feinde: "','"Hostile Only: "'),
                ('"Mob-Reichweite: "','"Mob Range: "')]:
        s=s.replace(a,b)
    s=replace(s,'String label,Runnable toggle){','String label,Runnable toggle){')
    # The underlying old preset buttons remain for compatibility; -/+ adjusts
    # pixels and zoom independently, persisted with each click.
    s=replace(s,'''           V178MiniPreferences::cycleZoom);''',
       '''           V178MiniPreferences::cycleZoom);
   display(left,top,w,8,"Size -",()->V178MiniPreferences.adjustSize(-2));
   display(left,top,w,9,"Size +",()->V178MiniPreferences.adjustSize(2));
   display(left,top,w,10,"Zoom -",()->V178MiniPreferences.adjustFineZoom(-10));
   display(left,top,w,11,"Zoom +",()->V178MiniPreferences.adjustFineZoom(10));''')
    s=replace(s,'''top+134,2*w+6,20''','''top+155,2*w+6,20''')
    s=replace(s,'''V178UiTheme.panel(g,left,top-48,panelWidth,216);''',
       '''V178UiTheme.panel(g,left,top-48,panelWidth,241);''')
    s=replace(s,'''int top=Math.max(51,(height-210)/2);''',
       '''int top=Math.max(47,(height-253)/2);''',number=2)
    # Do not change option-key arrays or their persistence.
    return s
update("client/V178MapSettingsScreen.java",settings)

# Client-only preference storage: one file per Minecraft player UUID. The
# authoritative ability checks, armor module availability and server actions
# continue to be evaluated by the ORIGINAL Action Wheel implementation.
emit("client/V178WheelPreferences.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import java.nio.file.*;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;
import java.util.UUID;

public final class V178WheelPreferences {
 private V178WheelPreferences(){}
 public static final String[] LABELS={
  "Exit Armor","Portal A","Portal B","Recall Armor","Network Vision",
  "Attack Mode","Follow","Turret","Sleep","J.A.R.V.I.S.",
  "JARVIS Settings","FlyModule","Wheel Settings"
 };
 private static final Set<Integer> hidden=new HashSet<>();
 private static UUID owner;
 private static Path file(UUID id){
  return Minecraft.getInstance().gameDirectory.toPath()
   .resolve("config").resolve("xsxlabs-action-wheel")
   .resolve(id.toString()+".properties");
 }
 private static void ensure(){
  Minecraft mc=Minecraft.getInstance();
  UUID next=mc.player==null?null:mc.player.getUUID();
  if(next==null){hidden.clear();owner=null;return;}
  if(next.equals(owner))return;
  owner=next;hidden.clear();
  Path path=file(next);
  if(!Files.isRegularFile(path))return;
  try(var in=Files.newInputStream(path)){
   Properties p=new Properties();p.load(in);
   for(int i=0;i<12;i++)
    if(!Boolean.parseBoolean(p.getProperty("action."+i,"true")))
     hidden.add(i);
  }catch(Exception e){System.err.println("[xSxLabs] wheel preferences: "+e);}
 }
 private static void save(){
  if(owner==null)return;
  try{
   Path path=file(owner);Files.createDirectories(path.getParent());
   Path tmp=Files.createTempFile(path.getParent(),"xsx-wheel-",".tmp");
   try{
    Properties p=new Properties();
    for(int i=0;i<12;i++)
     p.setProperty("action."+i,Boolean.toString(!hidden.contains(i)));
    try(var out=Files.newOutputStream(tmp)){p.store(out,"xSxLabs Action Wheel");}
    try{Files.move(tmp,path,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
    catch(AtomicMoveNotSupportedException e){Files.move(tmp,path,StandardCopyOption.REPLACE_EXISTING);}
   }finally{Files.deleteIfExists(tmp);}
  }catch(Exception e){System.err.println("[xSxLabs] wheel save: "+e);}
 }
 public static boolean enabled(int action){
  ensure();return action>=12||!hidden.contains(action);
 }
 public static void toggle(int action){
  ensure();if(action<0||action>=12)return;
  if(!hidden.add(action))hidden.remove(action);
  save();
 }
 public static void showAll(){ensure();hidden.clear();save();}
 public static int[] customize(int[] original){
  ensure();
  // Settings sector is always reachable, even if all actions are hidden.
  int[] filtered=new int[original.length+1];
  int count=0;
  for(int action:original)if(enabled(action))filtered[count++]=action;
  filtered[count++]=12;
  return Arrays.copyOf(filtered,count);
 }
}
''')

emit("client/V178WheelSettingsScreen.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Client-only per-player Action Wheel layout. No gameplay permissions change. */
public final class V178WheelSettingsScreen extends Screen{
 private final Screen previous;
 public V178WheelSettingsScreen(Screen previous){
  super(Component.literal("xSxLabs | Customize Action Wheel"));
  this.previous=previous;
 }
 @Override protected void init(){
  int widthButton=Math.max(105,Math.min(154,(width-30)/2));
  int left=(width-widthButton*2-8)/2;
  int top=Math.max(32,(height-262)/2);
  for(int id=0;id<12;id++){
   final int action=id;
   int bx=left+(id%2)*(widthButton+8),by=top+(id/2)*25;
   boolean visible=V178WheelPreferences.enabled(id);
   String label=V178WheelPreferences.LABELS[id]+": "+(visible?"SHOW":"HIDE");
   addRenderableWidget(Button.builder(Component.literal(label),b->{
    V178WheelPreferences.toggle(action);
    rebuildWidgets();
   }).bounds(bx,by,widthButton,20).build());
  }
  addRenderableWidget(Button.builder(Component.literal("SHOW ALL"),b->{
   V178WheelPreferences.showAll();rebuildWidgets();
  }).bounds(left,top+157,widthButton,20).build());
  addRenderableWidget(Button.builder(Component.literal("DONE"),b->onClose())
   .bounds(left+widthButton+8,top+157,widthButton,20).build());
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int w=Math.max(105,Math.min(154,(width-30)/2));
  int x=(width-2*w-8)/2-9,y=Math.max(32,(height-262)/2)-28;
  V178UiTheme.panel(g,x,y,2*w+26,213);
  g.text(font,"CUSTOMIZE ACTION WHEEL",x+11,y+8,V178UiTheme.CYAN);
  g.text(font,"Only installed/available abilities appear in-game.",
     x+11,y+192,0xffc3d5e9);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''')

def wheel(s):
    s=replace(s,
     'return V178FlyModuleClient.withFly(V177JarvisClient.withJarvis(base));',
     'return V178WheelPreferences.customize(V178FlyModuleClient.withFly(V177JarvisClient.withJarvis(base)));')
    m=re.search(r'private\s+static\s+void\s+activate\(\s*int\s+([A-Za-z_]\w*)\s*\)\s*\{',s)
    assert m,("B1730_WHEEL_ACTIVATE_MISSING",)
    action=m.group(1)
    s=s[:m.end()]+f'''
  if({action}==12){{
   Minecraft.getInstance().setScreen(new V178WheelSettingsScreen(null));
   return;
  }}
'''+s[m.end():]
    s=replace(s,
      'i==11?(V178FlyModuleClient.active()?"FLY OFF":"FLY ON"):ACTIONS[i];',
      'i==11?(V178FlyModuleClient.active()?"FLY OFF":"FLY ON"):i==12?"WHEEL SETTINGS":ACTIONS[i];')
    return s
update("client/NetworkActionWheelClient.java",wheel)

def keys(s):
    needle='''event.register(MINIMAP_SETTINGS);'''
    s=replace(s,needle,needle+'''
   event.register(WHEEL_SETTINGS);''')
    needle='''  private static final KeyMapping MINIMAP_SETTINGS=new KeyMapping('''
    s=replace(s,needle,'''  private static final KeyMapping WHEEL_SETTINGS=new KeyMapping(
    "key.obsidiannetwork.wheel_settings",InputConstants.Type.KEYSYM,
    GLFW.GLFW_KEY_UNKNOWN,V178KeybindCategory.XSXLABS);
'''+needle)
    needle='''  while(MINIMAP_SETTINGS.consumeClick()){'''
    s=replace(s,needle,'''  while(WHEEL_SETTINGS.consumeClick()){
   if(mc.screen==null&&mc.level!=null)
    mc.setScreen(new V178WheelSettingsScreen(null));
  }
'''+needle)
    return s
update("client/V178ClaimsClient.java",keys)

for locale,title in (("en_us","Open Action Wheel Settings"),
                     ("de_de","Action Wheel Einstellungen öffnen")):
    import json
    p=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/lang"/(locale+".json")
    s=json.loads(p.read_text(encoding="utf-8"))
    s["key.obsidiannetwork.wheel_settings"]=title
    p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Every screen action is local. No GUI render world sampling, no new packets,
# no additional tick listeners, and no direct server/armor rule modifications.
assert "V178WheelPreferences.customize" in (J/"client/NetworkActionWheelClient.java").read_text()
assert "V178MapMarkers.player" in (J/"client/V178ClaimsClient.java").read_text()
assert "V178MapMarkers.player" in (J/"client/V178ClaimsMapScreen.java").read_text()
assert "cropVersion==crop" in (J/"client/V178TerrainMap.java").read_text()
print("B1730_DETAIL_CIRCLE_GPU_FINE_SIZE_ZOOM_ACTION_WHEEL_CUSTOMIZATION_PASS")
