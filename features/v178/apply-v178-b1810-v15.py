#!/usr/bin/env python3
"""B1810 / v1.7.8 v15: seven tested user-requested repairs.

Runs after B1807 v14; never invalidates the proven live-first terrain cache.
"""
import json,os,struct,zlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
DIRECTIONS=("north","south","east","west","up","down")

def patch(rel,old,new):
 p=J/rel
 s=p.read_text("utf8")
 assert s.count(old)==1,("B1810_SOURCE_DRIFT",rel,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),"utf8")
def emit(rel,source):
 p=J/rel
 assert not p.exists(),("B1810_DUPLICATE_JAVA",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(source,"utf8")

# 1: Preserve v14's live-first archive precedence. Sample an extra 13x13
# loaded neighborhood around the moving player without increasing render
# sampling or requesting chunks. Near 5x5 remains higher priority.
terrain="client/V178TerrainMap.java"
patch(terrain,
 " private static int b1802NearCursor,b1802FarCursor;",
 " private static int b1802NearCursor,b1802FarCursor,b1810WideCursor;")
patch(terrain,
 "  // Wide worldmap gets extra refresh work if there is budget left.",
 """  // B1810: 13x13 nearby area, loaded chunks only, bounded client-tick budget.
  for(int n=0;n<6;n++){
   if(System.nanoTime()-start>=2_400_000L)break;
   int i=b1810WideCursor++%169;
   int tx=cx+(i%13)-6,tz=cz+(i/13)-6;
   if(tx==cx&&tz==cz)continue;
   refreshSurface(world,tx,tz);
  }
  // Wide worldmap gets extra refresh work if there is budget left.""")
t=(J/terrain).read_text("utf8")
assert "world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)" in t
assert "b1810WideCursor++%169" in t
assert "V178MiniRaster.tick(world);" in t

# 2: Live backend slots always return snapshots, never their mutable saved
# ItemStack. Vanilla click/shift stacks are copies and MUST write back to the
# actual BE after a partial transfer; previously a shared reference mutated
# BE state without a changed/sync notification.
menu="mining/V178MiningBuilderMenu.java"
patch(menu,
 "return be.installedSpeedUpgrades();",
 "return be.installedSpeedUpgrades().copy();")
patch(menu,
 "return be.installedCard();",
 "return be.installedCard().copy();")
patch(menu,
 """  if(held.isEmpty())source.setByPlayer(ItemStack.EMPTY);
  else source.setChanged();
  return original;""",
 """  // B1810: write partial speed/card moves back to the server-owned slot.
  if(slot==0||slot==1)source.setByPlayer(held);
  else if(held.isEmpty())source.setByPlayer(ItemStack.EMPTY);
  else source.setChanged();
  return original;""")
be="mining/V178MiningBuilderBE.java"
patch(be,
 """ItemStack taken=speedUpgrades.split(amount);""",
 """ItemStack taken=speedUpgrades.split(Math.min(16,amount));""")
# Preserve the existing 16-cap, owner validation, ShapeCard and drop behavior.
m=(J/menu).read_text("utf8")
assert "moveItemStackTo(held,0,1,false)" in m
assert "moveItemStackTo(held,1,2,false)" in m
assert "new Slot(speedStorage,0,143,27)" in m
assert "return be.installedSpeedUpgrades().copy();" in m

# 3: Original reference-inspired, one-cuboid GPU-friendly builder, dark
# violet accent housing and front flush monitor with PICKAXE. One baked
# cube + two 16x16 original procedural texture sheets; no tick renderer.
model=R/"models/block/mining_builder.json"
obj=json.loads(model.read_text("utf8"))
assert len(obj["elements"])==26,("B1810_PREVIOUS_MODEL_CHANGED",len(obj["elements"]))
obj["parent"]="minecraft:block/block"
obj["ambientocclusion"]=True
obj["textures"]={
 "case":"obsidiannetwork:block/mining_builder_case_v15",
 "front":"obsidiannetwork:block/mining_builder_front_v15",
 "particle":"obsidiannetwork:block/mining_builder_case_v15"}
faces={d:{"texture":"#front" if d=="north" else "#case","cullface":d}
       for d in DIRECTIONS}
obj["elements"]=[{"from":[0,0,0],"to":[16,16,16],"faces":faces}]
model.write_text(json.dumps(obj,indent=2)+"\n","utf8")
def encode_png(pixels,sz=16):
 def chunk(tag,payload):
  return struct.pack(">I",len(payload))+tag+payload+struct.pack(">I",zlib.crc32(tag+payload)&0xffffffff)
 raw=bytearray()
 for y in range(sz):
  raw.append(0)
  for x in range(sz): raw.extend(bytes((*pixels(x,y),255)))
 return (b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",sz,sz,8,6,0,0,0))
         +chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b""))
def case_color(x,y):
 # Dark plum housing from the user's reference, subtle inset seam grid.
 color=(39,32,75)
 if x in (0,15) or y in (0,15):color=(24,19,49)
 elif x in (2,13) or y in (2,13):color=(51,42,92)
 elif (x%5==0 or y%5==0):color=(42,35,80)
 return color
def front_color(x,y):
 # Beveled monitor bezel cut into the same purple housing.
 if x in (0,15) or y in (0,15):return (24,19,49)
 if not (2<=x<=13 and 2<=y<=13):return (43,35,83)
 if x in (2,13) or y in (2,13):return (100,72,151)
 if x in (3,12) or y in (3,12):return (18,20,39)
 color=(10,24,39)
 if y==4 and 5<=x<=10:return (40,84,103)
 # Large crisp steel pickaxe head and diagonal golden shaft.
 head={(4,6),(5,5),(6,5),(7,5),(8,5),(9,5),(10,6),(11,7),
       (5,6),(6,6),(7,6),(8,6),(9,6),(10,7)}
 shaft={(8,7),(7,8),(6,9),(5,10),(4,11),(9,7),(8,8),(7,9),(6,10),(5,11)}
 if (x,y) in shaft:return (213,166,91)
 if (x,y) in head:return (141,222,239)
 return color
for name,draw in (("case",case_color),("front",front_color)):
 path=R/"textures/block"/("mining_builder_"+name+"_v15.png")
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(encode_png(draw))

# 4: Builder loot table is an explicit unconditional item drop, separate
# from the BE's one-time ShapeCard/Speed/output pre-remove drops. Ensure the
# registered item and loot model are not accidentally disabled.
loot=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork/loot_table/blocks/mining_builder.json"
data=json.loads(loot.read_text("utf8"))
assert data["type"]=="minecraft:block"
entries=[e for pool in data["pools"] for e in pool["entries"]]
assert any(e.get("name")=="obsidiannetwork:mining_builder" for e in entries)
builder=(J/"mining/V178MiningBuilderBlock.java").read_text("utf8")
assert "RenderShape.MODEL" in builder and "V178MiningBuilderBE::serverTick" in builder
miner=(J/be).read_text("utf8")
for token in ("speedUpgrades.copy()","Containers.dropItemStack","for(int i=0;i<27;i++)if(!stacks[i].isEmpty())"):
 assert token in miner,("B1810_DROP_CONTRACT",token)

# 5: Same exact 116-cuboid Wireless Charger geometry as 1.7.7 build 1609.
# v14's general occlusion pass removed 94 faces; restore every face. Correct
# the malformed texture slot dictionaries to actual Minecraft texture strings.
charger=R/"models/block/wireless_charger.json"
wc=json.loads(charger.read_text("utf8"))
assert len(wc["elements"])==116
assert sum(len(e["faces"]) for e in wc["elements"])==602
assert wc["textures"]["main"]=={"sprite":"obsidiannetwork:block/wireless_charger"}
wc["textures"]={"main":"obsidiannetwork:block/wireless_charger",
                "particle":"obsidiannetwork:block/wireless_charger"}
for el in wc["elements"]:
 assert all(v["texture"]=="#main" for v in el["faces"].values())
 el["faces"]={face:{"texture":"#main"} for face in DIRECTIONS}
assert sum(len(e["faces"]) for e in wc["elements"])==696
charger.write_text(json.dumps(wc,indent=2)+"\n","utf8")
assert (R/"textures/block/wireless_charger.png").read_bytes().startswith(b"\x89PNG")

# 6: Fix worldmap's mouse wheel resizing the OUTER panel. Zoom changes
# visible source chunks within a constant-sized centered frame. Atlas already
# supports center-cropping the 25x25 tile cache without per-frame world reads.
screen="client/V178ClaimsMapScreen.java"
patch(screen,
 """ private int tile(){return zoom;}""",
 """ private int mapSide(){return Math.max(110,Math.min(325,Math.min(width-35,height-toolbarBottom-66)));}
 private int tile(){return Math.max(1,mapSide()/Math.max(1,DIAMETER));}""")
patch(screen,
 """ private int left(){return (width-DIAMETER*tile())/2;}""",
 """ private int left(){return (width-mapSide())/2;}""")
patch(screen,
 """ private int top(){return Math.max(toolbarBottom+27,(height-DIAMETER*tile())/2);}""",
 """ private int top(){return Math.max(toolbarBottom+27,(height-mapSide())/2);}""")
patch(screen,
 """  int availableHeight=Math.max(5*zoom,height-toolbarBottom-66);
  int availableWidth=Math.max(5*zoom,width-35);
  DIAMETER=Math.max(5,Math.min(25,
      Math.min(availableHeight,availableWidth)/Math.max(1,zoom)));""",
 """  // B1810: zoom only the map source, never the worldmap panel dimensions.
  DIAMETER=Math.max(7,Math.min(25,25-(zoom-6)*3/2));
  if((DIAMETER&1)==0)DIAMETER--;""")
patch(screen,
 """  V178UiTheme.panel(g,x0-8,y0-27,w+16,w+75);""",
 """  V178UiTheme.panel(g,x0-8,y0-27,mapSide()+16,mapSide()+75);""")
patch(screen,
 """   int legendY=y0+w+34;""",
 """   int legendY=y0+mapSide()+34;""")
patch(screen,
 """return mx>=left()&&mx<left()+DIAMETER*tile()
     &&my>=top()&&my<top()+DIAMETER*tile();""",
 """return mx>=left()&&mx<left()+DIAMETER*tile()
     &&my>=top()&&my<top()+DIAMETER*tile();""") if False else None
patch(screen,"x0,y0+w+6,0xffc3d5e9","x0,y0+mapSide()+6,0xffc3d5e9")
patch(screen,"x0,y0+w+18,0xff9baec4","x0,y0+mapSide()+18,0xff9baec4")
s=(J/screen).read_text("utf8")
assert "mapSide()" in s and "25-(zoom-6)*3/2" in s

# 7: Native claim-zone popup, using the server's persisted team names. The
# server checks one  O(1) chunk hash per player every five ticks and sends
# only upon team transition, never for each adjacent chunk of the same team.
claim="claims/V178Claims.java"
patch(claim,
 """ private static final Map<UUID,String> TEAM_NAMES=new HashMap<>();""",
 """ private static final Map<UUID,String> TEAM_NAMES=new HashMap<>();
 private record B1810Area(String dimension,long chunk,UUID group){}
 private static final Map<UUID,B1810Area> B1810_LAST_AREAS=new HashMap<>();
""")
patch(claim,
 """ @SubscribeEvent public static void stopped(ServerStoppedEvent event){""",
 """ @SubscribeEvent public static void b1810AreaAlerts(ServerTickEvent.Post event){
  if(active!=event.getServer()||event.getServer().getTickCount()%5!=0)return;
  for(ServerPlayer player:event.getServer().getPlayerList().getPlayers()){
   if(!(player.level() instanceof ServerLevel level))continue;
   String dim=dimension(level);
   long chunk=key(player.blockPosition().getX()>>4,player.blockPosition().getZ()>>4);
   UUID user=player.getUUID();
   B1810Area previous=B1810_LAST_AREAS.get(user);
   if(previous!=null&&previous.dimension().equals(dim)&&previous.chunk()==chunk)continue;
   Claim found=map(level).get(chunk);
   UUID leader=found==null?null:MEMBER_TEAM.getOrDefault(found.owner(),found.owner());
   B1810_LAST_AREAS.put(user,new B1810Area(dim,chunk,leader));
   if(leader!=null&&(previous==null||!java.util.Objects.equals(previous.group(),leader)
                   ||!previous.dimension().equals(dim))){
    UUID myLeader=MEMBER_TEAM.getOrDefault(user,user);
    PacketDistributor.sendToPlayer(player,
      new V178ClaimAreaNotice(teamName(leader),leader.equals(myLeader)));
   }
  }
 }
 @SubscribeEvent public static void stopped(ServerStoppedEvent event){""")
# Keep server caches bounded across world shutdowns.
patch(claim,
 """  if(active==event.getServer()){save();active=null;CLAIMS.clear();""",
 """  if(active==event.getServer()){save();active=null;B1810_LAST_AREAS.clear();CLAIMS.clear();""")
# Registration uses existing NeoForge payload event style and 40-char
# bounded name (actual team-name validation is <=24 characters).
emit("claims/V178ClaimAreaNotice.java",r'''package dev.obsidiannetwork.claims;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

@EventBusSubscriber(modid="obsidiannetwork")
public record V178ClaimAreaNotice(String team,boolean own) implements CustomPacketPayload {
 public static final Type<V178ClaimAreaNotice> TYPE=new Type<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claim_area_enter"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178ClaimAreaNotice> CODEC=
  StreamCodec.of((buf,p)->{buf.writeUtf(p.team(),40);buf.writeBoolean(p.own());},
    buf->new V178ClaimAreaNotice(buf.readUtf(40),buf.readBoolean()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void register(RegisterPayloadHandlersEvent event){
  event.registrar("1").playToClient(TYPE,CODEC);
 }
}
''')

emit("client/V178ClaimAreaHud.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.claims.V178ClaimAreaNotice;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;
import java.nio.file.*;
import java.util.Properties;

@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178ClaimAreaHud {
 private V178ClaimAreaHud(){}
 private static boolean loaded,enabled=true;
 private static int duration=60,position=0;
 private static volatile String message="",dimension="";
 private static volatile long expires=Long.MIN_VALUE;
 private static Path file(){
  return Minecraft.getInstance().gameDirectory.toPath()
     .resolve("config/xsxlabs-claim-area-popup.properties");
 }
 private static void ensure(){
  if(loaded)return;
  loaded=true;
  if(!Files.isRegularFile(file()))return;
  try(var in=Files.newInputStream(file())){
   Properties p=new Properties();p.load(in);
   enabled=Boolean.parseBoolean(p.getProperty("enabled","true"));
   duration=Math.max(40,Math.min(160,Integer.parseInt(p.getProperty("duration","60"))));
   position=Math.floorMod(Integer.parseInt(p.getProperty("position","0")),4);
  }catch(Exception ignored){}
 }
 private static void save(){
  try{
   Files.createDirectories(file().getParent());
   Properties p=new Properties();
   p.setProperty("enabled",Boolean.toString(enabled));
   p.setProperty("duration",Integer.toString(duration));
   p.setProperty("position",Integer.toString(position));
   try(var out=Files.newOutputStream(file())){p.store(out,"xSxLabs claim-area notice");}
  }catch(Exception ignored){}
 }
 public static String enabledLabel(){ensure();return enabled?"AN":"AUS";}
 public static String durationLabel(){ensure();return (duration/20)+" s";}
 public static String positionLabel(){ensure();return switch(position){
  case 1->"Unten";case 2->"Links";case 3->"Rechts";default->"Oben";};}
 public static void toggle(){ensure();enabled=!enabled;save();}
 public static void cycleDuration(){ensure();duration=duration>=120?40:duration+20;save();}
 public static void cyclePosition(){ensure();position=(position+1)%4;save();}
 @SubscribeEvent public static void packets(RegisterClientPayloadHandlersEvent event){
  event.register(V178ClaimAreaNotice.TYPE,(p,ctx)->{
   var mc=Minecraft.getInstance();
   if(mc.level==null)return;
   ensure();
   dimension=mc.level.dimension().identifier().toString();
   message=(p.own()?"Dein Team: ":"Gebiet von: ")+p.team();
   expires=mc.level.getGameTime()+duration;
  });
 }
 @SubscribeEvent public static void draw(RenderGuiEvent.Post event){
  if(!enabled||message.isEmpty())return;
  var mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.screen!=null)return;
  if(!dimension.equals(mc.level.dimension().identifier().toString()))return;
  long tick=mc.level.getGameTime();
  if(tick>expires||tick<expires-200)return;
  GuiGraphicsExtractor g=event.getGuiGraphics();
  int w=Math.min(mc.getWindow().getGuiScaledWidth()-8,Math.max(175,mc.font.width(message)+26));
  int h=28;
  int sx=mc.getWindow().getGuiScaledWidth(),sy=mc.getWindow().getGuiScaledHeight();
  int x=switch(position){case 2->9;case 3->sx-w-9;default->(sx-w)/2;};
  int y=position==1?sy-83:32;
  g.fill(x,y,x+w,y+h,0xe40d182b);
  g.outline(x,y,w,h,0xff8a65d6);
  g.fill(x+4,y+5,x+6,y+h-5,0xff77e6f7);
  g.text(mc.font,message,x+14,y+10,0xffe4f5ff);
 }
}
''')
settings="client/V178MapSettingsScreen.java"
patch(settings,
 """  addRenderableWidget(Button.builder(Component.literal("Back to Map"),""",
 """  if(page==2){
   button(left,top+72,w,"Claim-Popup: "+V178ClaimAreaHud.enabledLabel(),
      V178ClaimAreaHud::toggle);
   button(left+w+6,top+72,w,"Dauer: "+V178ClaimAreaHud.durationLabel(),
      V178ClaimAreaHud::cycleDuration);
   button(left,top+97,w,"Position: "+V178ClaimAreaHud.positionLabel(),
      V178ClaimAreaHud::cyclePosition);
  }
  addRenderableWidget(Button.builder(Component.literal("Back to Map"),""")

print("B1810_V15_ALL_SEVEN_PATCHES_PASS")
