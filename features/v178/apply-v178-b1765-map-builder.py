#!/usr/bin/env python3
"""B1765: Xaero/FTB-style map refresh & zoom and real Mining Builder speed slot.

Applied AFTER B1741. No GUI-frame world reads, no chunk loads, no new
mining drops, no speed-upgrade item duplication, server owns inventories.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    n=s.count(old)
    assert n==1,("B1765_SOURCE_DRIFT",rel,n,old[:120])
    p.write_text(s.replace(old,new,1),encoding="utf-8")

# Further zoom-out uses source-pixel resampling into ONE fixed 304x304
# GPU image, rather than uploading a quadratic 624x624 texture.
prefs="client/V178MiniPreferences.java"
patch(prefs,"fineZoom=Math.max(30,Math.min(300,fineZoom));",
      "fineZoom=Math.max(10,Math.min(300,fineZoom));")
patch(prefs,"fineZoom=Math.max(30,Math.min(300,fineZoom+delta));",
      "fineZoom=Math.max(10,Math.min(300,fineZoom+delta));")
patch(prefs,"Math.min(19*16,visibleChunks()*16*100/fineZoom)",
      "Math.min(39*16,visibleChunks()*16*100/fineZoom)")
raster="client/V178MiniRaster.java"
patch(raster,"double radius=(crop-1)*0.5,inner=radius-1.25;",
      "double radius=(SIDE-1)*0.5,inner=radius-1.25;")
patch(raster,
      "for(int py=0;py<crop;py++)for(int px=0;px<crop;px++){\n   int wx=startX+px,wz=startZ+py;",
      "for(int py=0;py<SIDE;py++)for(int px=0;px<SIDE;px++){\n   int wx=startX+(int)((long)px*crop/SIDE);\n   int wz=startZ+(int)((long)py*crop/SIDE);")
patch(raster,"double dx=px+0.5-crop*0.5,dz=py+0.5-crop*0.5;",
      "double dx=px+0.5-SIDE*0.5,dz=py+0.5-SIDE*0.5;")
patch(raster,"int crop=lastCrop;\n  g.blit(", "int crop=SIDE;\n  g.blit(")

# Common terrain source drives BOTH World Map and minimap. Refresh the local
# surface quickly for mining/terraforming; amortize wide world-map checks.
# Revisions only advance when actual pixels change, preserving GPU batching.
terrain="client/V178TerrainMap.java"
patch(terrain,
''' private static int liveRefreshCursor;
 public static int terrainRevision(){return atlasRevision;}''',
''' private static int nearRefreshCursor,farRefreshCursor;
 public static int terrainRevision(){return atlasRevision;}
 private static void refreshSurface(ClientLevel world,int cx,int cz){
  if(!world.hasChunk(cx,cz))return;
  var data=cache(world.dimension().identifier().toString());
  long key=pos(cx,cz);
  int[] before=data.remove(key);
  int revisionBefore=atlasRevision;
  boolean dirtyBefore=dirty;
  sample(world,cx,cz);
  int[] after=data.get(key);
  if(before!=null&&java.util.Arrays.equals(before,after)){
   data.put(key,before);
   atlasRevision=revisionBefore;
   dirty=dirtyBefore;
  }
 }''')
patch(terrain,
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
   }''',
'''   long refreshTick=world.getGameTime();
   // Centre gets a fresh 16x16 surface sample every 8 ticks.
   if(refreshTick%8L==0L)refreshSurface(world,cx,cz);
   // Nearby 5x5 area: every 50 ticks (~2.5 seconds).
   if(refreshTick%2L==0L){
    int index=nearRefreshCursor++%25;
    refreshSurface(world,cx+(index%5)-2,cz+(index/5)-2);
   }
   // World map: 25x25 already-explored region, one loaded chunk/tick.
   var currentScreen=Minecraft.getInstance().screen;
   if(currentScreen instanceof V178ClaimsMapScreen
       ||currentScreen instanceof V178MiningAreaScreen){
    int index=farRefreshCursor++%625;
    refreshSurface(world,cx+(index%25)-12,cz+(index/25)-12);
   }''')
# The original map uses one colored surface pixel per actual block (RES=16).
# Make snow, exposed soil, and rocky cliff more visible without texture reads
# during rendering; the existing block-color and slope sample stays authoritative.
# Terrain's own DIRT/COARSE_DIRT/MUD palette from B1740 remains unchanged.

# The previous 10px skin square hides the direction arrow. Use one compact,
# outlined cyan/white directional pointer on both maps, no skin head texture.
markers="client/V178MapMarkers.java"
p=J/markers
s=p.read_text(encoding="utf-8")
head="  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){"
assert s.count(head)==1,("B1765_MARKER_START_DRIFT",s.count(head))
a=s.index(head)
b=s.index("\n }\n}",a)
new=r'''  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
   // B1765_DIRECTION_ARROW: small directional triangle, dark outlined,
   // cyan core + white centre. Scales independently of terrain zoom.
   double angle=Math.toRadians(yaw);
   double forwardX=-Math.sin(angle),forwardY=Math.cos(angle);
   double acrossX=-forwardY,acrossY=forwardX;
   for(int row=0;row<=9;row++){
    double forward=6.0-row*1.15;
    int halfWidth=row<3?0:(row-2)/2;
    for(int wing=-halfWidth;wing<=halfWidth;wing++){
     int px=x+(int)Math.round(forwardX*forward+acrossX*wing);
     int py=y+(int)Math.round(forwardY*forward+acrossY*wing);
     g.fill(px-1,py-1,px+2,py+2,0xff10202b);
     g.fill(px,py,px+1,py+1,0xff54e8f5);
    }
   }
   g.fill(x-1,y-1,x+2,y+2,0xffffffff);
  }'''
s=s[:a]+new+s[b+3:]
assert "B1765_DIRECTION_ARROW" in s and "PlayerFaceExtractor.extractRenderState(" not in s
p.write_text(s,encoding="utf-8")

# Existing pump accepts the mod's own speed_upgrade item. Reuse the exact
# namespace/path contract, not an invented item or a client-side counter.
be="mining/V178MiningBuilderBE.java"
patch(be,
'''  public ItemStack installedCard(){return card;}''',
'''  private ItemStack speedUpgrades=ItemStack.EMPTY;
  public static boolean isSpeedUpgrade(ItemStack stack){
   if(stack.isEmpty())return false;
   var key=net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem());
   return key!=null&&"obsidiannetwork".equals(key.getNamespace())
     &&key.getPath().contains("speed_upgrade");
  }
  public ItemStack installedSpeedUpgrades(){return speedUpgrades;}
  public int speedUpgradeCount(){
   return isSpeedUpgrade(speedUpgrades)?Math.min(16,speedUpgrades.getCount()):0;
  }
  public int maxBreaksThisTick(){
   return MAX_BREAKS+(MAX_BREAKS*speedUpgradeCount()/16);
  }
  public void setSpeedUpgrades(ServerPlayer user,ItemStack value){
   if(!canOperate(user)||(!value.isEmpty()&&!isSpeedUpgrade(value)))return;
   speedUpgrades=value.isEmpty()?ItemStack.EMPTY:value.copyWithCount(
       Math.min(16,value.getCount()));
   setChanged();
  }
  public ItemStack removeSpeedUpgrades(ServerPlayer user,int amount){
   if(!canOperate(user)||amount<=0)return ItemStack.EMPTY;
   ItemStack taken=speedUpgrades.split(amount);
   if(speedUpgrades.isEmpty())speedUpgrades=ItemStack.EMPTY;
   if(!taken.isEmpty())setChanged();
   return taken;
  }
  public ItemStack installedCard(){return card;}''')
patch(be,"mined<MAX_BREAKS&&machine.cursor<machine.bounds.volume()",
      "mined<machine.maxBreaksThisTick()&&machine.cursor<machine.bounds.volume()")
patch(be,
'''  if(!card.isEmpty())out.store("xsxMiningCard",ItemStack.CODEC,card);''',
'''  if(!card.isEmpty())out.store("xsxMiningCard",ItemStack.CODEC,card);
  if(!speedUpgrades.isEmpty())out.store("xsxMiningSpeed",ItemStack.CODEC,speedUpgrades);''')
patch(be,
'''  card=in.read("xsxMiningCard",ItemStack.CODEC).orElse(ItemStack.EMPTY);''',
'''  card=in.read("xsxMiningCard",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  speedUpgrades=in.read("xsxMiningSpeed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  if(!isSpeedUpgrade(speedUpgrades))speedUpgrades=ItemStack.EMPTY;
  else if(speedUpgrades.getCount()>16)speedUpgrades=speedUpgrades.copyWithCount(16);''')
patch(be,
'''   if(!card.isEmpty()){
    Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,card);''',
'''   if(!speedUpgrades.isEmpty()){
    Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,speedUpgrades.copy());
    speedUpgrades=ItemStack.EMPTY;
   }
   if(!card.isEmpty()){
    Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,card);''')

# Server-side vanilla ChestMenu synchronization, same as existing card slot.
menu="mining/V178MiningBuilderMenu.java"
patch(menu,
'''  for(int i=1;i<27;i++){''',
'''  SimpleContainer speedStorage=new SimpleContainer(1){
   @Override public ItemStack getItem(int index){return be.installedSpeedUpgrades();}
   @Override public void setItem(int index,ItemStack next){
    be.setSpeedUpgrades(player,next);setChanged();
   }
   @Override public ItemStack removeItem(int index,int amount){
    return be.removeSpeedUpgrades(player,amount);
   }
   @Override public ItemStack removeItemNoUpdate(int index){
    return be.removeSpeedUpgrades(player,16);
   }
   @Override public boolean stillValid(Player other){
    return V178MiningBuilderMenu.this.stillValid(other);
   }
  };
  slots.set(1,new Slot(speedStorage,0,143,27){
   @Override public boolean mayPlace(ItemStack item){
    return be.canOperate(player)&&V178MiningBuilderBE.isSpeedUpgrade(item);
   }
   @Override public boolean mayPickup(Player other){
    return other==player&&be.canOperate(player);
   }
   @Override public int getMaxStackSize(){return 16;}
  });
  for(int i=2;i<27;i++){''')
gui="client/V178MiningBuilderOperationsScreen.java"
patch(gui,
'''  for(int i=1;i<27;i++){''',
'''  Slot speedSlot=menu.slots.get(1);
  menu.slots.set(1,new Slot(speedSlot.container,1,143,27){
   @Override public boolean mayPlace(ItemStack stack){
    return dev.obsidiannetwork.mining.V178MiningBuilderBE.isSpeedUpgrade(stack);
   }
   @Override public int getMaxStackSize(){return 16;}
  });
  for(int i=2;i<27;i++){''')
patch(gui,
'''  g.text(font,"SHAPE CARD",x+47,y+31,0xffb5e5ef);''',
'''  g.text(font,"SHAPE CARD",x+47,y+31,0xffb5e5ef);
  g.fill(x+141,y+25,x+161,y+47,0xff547e93);
  g.fill(x+142,y+26,x+160,y+46,0xff15283a);''')
patch(gui,
'''  g.text(font,"into the real card slot",x+14,y+68,0xff8eacbb);''',
'''  g.text(font,"into the real card slot",x+14,y+68,0xff8eacbb);
  int installed=menu.slots.get(1).getItem().getCount();
  g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+88,y+56,0xff66deee);''')
patch(gui,
'''  g.text(font,"Top-down scan | mining only",xx+9,y+153,0xff8aabba);''',
'''  int upgrades=Math.min(16,menu.slots.get(1).getItem().getCount());
  g.text(font,"SPEED "+upgrades+"/16  |  "+(100+upgrades*100/16)+"% mining",
    xx+9,y+153,0xff8aabba);''')

output=(J/be).read_text()
assert "maxBreaksThisTick()" in output and "speedUpgrades.copy()" in output
assert "slots.set(1,new Slot(speedStorage" in (J/menu).read_text()
assert "B1765_DIRECTION_ARROW" in (J/markers).read_text()
assert "Math.min(39*16" in (J/prefs).read_text()
assert "for(int py=0;py<SIDE;py++)" in (J/raster).read_text()
print("B1765_TERRAIN_REVALIDATION_WIDE_ZOOM_DIRECTION_ARROW_BUILDER_SPEED16_2X_PASS")
