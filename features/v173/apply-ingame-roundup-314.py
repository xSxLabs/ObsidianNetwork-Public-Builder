#!/usr/bin/env python3
"""v1.7.3 Build314 field-fix: native slot-free hologram screen, terrain map,
size/height modes, portal appearance, named anchors and hold-release wheel.
Runs after the Build306 patch. Fail closed on source drift.
"""
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V173_314_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def replace_span(rel,start,end,replacement):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(start)==1 and s.count(end)==1,("V173_314_SPAN_DRIFT",rel,start[:95],s.count(start),s.count(end))
 a=s.index(start);b=s.index(end,a)
 p.write_text(s[:a]+replacement+s[b:],encoding="utf-8")
def add(rel,content):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V173_314_DUPLICATE",rel)
 p.write_text(content,encoding="utf-8")

# The logical 1-block portal anchor must NOT also draw its 1x1 model:
# only the world-space 2x3 renderer is allowed to depict the aperture.
edit("portal/PortalGateBlock.java",
     '@Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}',
     '@Override public RenderShape getRenderShape(BlockState s){return RenderShape.INVISIBLE;}')
edit("client/V173WorldGhostRenderer.java",
     'lastPortalScan>=20L','lastPortalScan>=2L')
edit("client/V173WorldGhostRenderer.java",
     '''   // Transparent 2x3 inner membrane, with real textures (not missing JSON).
   for(int ix=0;ix<2;ix++)for(int iy=0;iy<3;iy++)
    drawSized(mc,ev,cam,glass,x+.25+ix*.75,y+.25+iy*(2.5/3D),
               z+.055,.75,2.5/3D,.055);''',
     '''   // One continuous tinted membrane instead of six tiled glass blocks.
   // No internal joints; A and B keep distinct colors.
   drawSized(mc,ev,cam,glass,x+.25,y+.25,z+.055,1.5,2.5,.055);''')

# True terrain heightfield sampled from WORLD_SURFACE, no floating dust-cloud
# and no underground point-cloud columns. Radius is measured in CHUNKS.
# Width/depth and height are derived automatically, with correct proportions.
replace_span("client/V173WorldGhostRenderer.java",
''' private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,''',
''' private static net.minecraft.client.multiplayer.ClientLevel portalWorld;''',
r''' private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                     NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null)return out;
  // Radius = chunks, not blocks. The scale/footprint follows radius.
  int radiusChunks=Math.max(1,Math.min(12,be.holoRadius()));
  int radius=radiusChunks*16,side=radius*2+1;
  int step=Math.max(1,(side+47)/48); // <=48x48 sampled columns
  int count=(side+step-1)/step;
  int[][] height=new int[count][count];
  BlockState[][] surface=new BlockState[count][count];
  int cx=t.getX(),cz=t.getZ();
  int midHeight=mc.level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.WORLD_SURFACE,cx,cz)-1;
  for(int ix=0;ix<count;ix++)for(int iz=0;iz<count;iz++){
   int wx=cx-radius+ix*step,wz=cz-radius+iz*step;
   BlockPos at=new BlockPos(wx,t.getY(),wz);
   if(!mc.level.hasChunkAt(at))continue;
   int y=mc.level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.WORLD_SURFACE,wx,wz)-1;
   if(y<mc.level.getMinY()||y>=mc.level.getMaxY())continue;
   BlockState state=mc.level.getBlockState(new BlockPos(wx,y,wz));
   if(state.isAir())continue;
   // Liquid fluid states do not have a baked block model.
   if(!state.getFluidState().isEmpty())
    state=(state.getFluidState().isSource()?Blocks.BLUE_STAINED_GLASS:Blocks.BLUE_STAINED_GLASS).defaultBlockState();
   height[ix][iz]=y;
   surface[ix][iz]=state;
  }
  double footprint=2.5D+radiusChunks*1.25D;
  double perBlock=footprint/side;
  double tile=step*perBlock;
  double originX=t.getX()+.5-footprint/2D;
  double originZ=t.getZ()+.5-footprint/2D;
  // HEIGHT is a translation in blocks, NOT the height of the 3D map.
  double originY=t.getY()-be.holoHeight()+.5D;
  for(int ix=0;ix<count;ix++)for(int iz=0;iz<count;iz++){
   BlockState top=surface[ix][iz];
   if(top==null)continue;
   int y=height[ix][iz];
   double x=originX+ix*tile,z=originZ+iz*tile;
   double topY=originY+(y-midHeight)*perBlock;
   out.add(new MapVoxel(top,x,topY,z,tile,tile,tile));
   int min=y;
   if(ix>0&&surface[ix-1][iz]!=null)min=Math.min(min,height[ix-1][iz]);
   if(ix+1<count&&surface[ix+1][iz]!=null)min=Math.min(min,height[ix+1][iz]);
   if(iz>0&&surface[ix][iz-1]!=null)min=Math.min(min,height[ix][iz-1]);
   if(iz+1<count&&surface[ix][iz+1]!=null)min=Math.min(min,height[ix][iz+1]);
   // Stretch a single solid side-wall downward to close steep terrain gaps.
   if(min<y&&out.size()<4200){
    double depth=(y-min)*perBlock;
    out.add(new MapVoxel(Blocks.STONE.defaultBlockState(),
      x,topY-depth,z,tile,depth,tile));
   }
  }
  return out;
 }

''')
# Text holograms: SIZE scales uniformly; HEIGHT offsets *all* modes below
# the holo table. HEIGHT=1 => baseline in the block immediately underneath.
edit("blockentity/NetworkDeviceBlockEntity.java",
     'float scale=Math.max(.25F,Math.min(8F,holoHeight/3F));',
     'float scale=Math.max(.25F,Math.min(8F,holoWidth/3F));')
edit("blockentity/NetworkDeviceBlockEntity.java",
     'double y=worldPosition.getY()+1.55+(shown-1-i)*.24*scale;',
     'double y=worldPosition.getY()-holoHeight+.5+(shown-1-2*i)*.12*scale;')
edit("blockentity/NetworkDeviceBlockEntity.java",
     'holoRadius=Math.max(2,Math.min(256,radius));',
     'holoRadius=Math.max(1,Math.min(12,radius));')
edit("blockentity/NetworkDeviceBlockEntity.java",
     'holoRadius=Math.max(2,Math.min(256,in.getIntOr("holo_radius",16)));',
     'holoRadius=Math.max(1,Math.min(12,in.getIntOr("holo_radius",1)));')

# Completely remove ChestMenu rendering/hover/ghost-slot interaction.
# A plain Screen is not a container screen, while the server still keeps
# the temporary menu session; on close it explicitly closes that session.
(J/"client/HologramConfigScreen.java").write_text(r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import dev.obsidiannetwork.network.HologramConfigPayload;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;

/** V173_HOLO_SLOT_FREE_314 - no inventory, slot grid, item hover or click. */
public final class HologramConfigScreen extends Screen {
 private String mode="network";
 private BlockPos terminal;
 private EditBox content,color,size,height,radius;
 private int bx,by;
 public HologramConfigScreen(ChestMenu ignored,Inventory inventory,Component title){
  super(title);
 }
 private NetworkDeviceBlockEntity device(){
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.level==null)return null;
  String s=getTitle().getString();int at=s.indexOf('@');
  if(at<0)return null;
  try{
   String[] v=s.substring(at+1).split(",");
   if(v.length!=3)return null;
   terminal=new BlockPos(Integer.parseInt(v[0]),Integer.parseInt(v[1]),Integer.parseInt(v[2]));
   var be=mc.level.getBlockEntity(terminal);
   return be instanceof NetworkDeviceBlockEntity d?d:null;
  }catch(NumberFormatException ex){return null;}
 }
 private EditBox make(int x,int y,int w,String name,String text,int max){
  EditBox e=new EditBox(font,x,y,w,20,Component.literal(name));
  e.setMaxLength(max);e.setValue(text);addRenderableWidget(e);return e;
 }
 private int val(EditBox e,int backup,int low,int high){
  try{return Math.max(low,Math.min(high,Integer.parseInt(e.getValue())));}
  catch(NumberFormatException ex){return backup;}
 }
 @Override protected void init(){
  super.init();
  bx=(width-304)/2;by=(height-216)/2;
  var be=device();
  if(be!=null)mode=be.holoMode();
  addRenderableWidget(Button.builder(Component.literal("NETWORK"),b->{mode="network";switchMode();})
     .bounds(bx+12,by+27,88,21).build());
  addRenderableWidget(Button.builder(Component.literal("MAP 3D"),b->{mode="map";switchMode();})
     .bounds(bx+108,by+27,88,21).build());
  addRenderableWidget(Button.builder(Component.literal("CUSTOM"),b->{mode="custom";switchMode();})
     .bounds(bx+204,by+27,88,21).build());
  size=make(bx+12,by+85,85,"Size",be==null?"5":""+be.holoWidth(),3);
  radius=make(bx+12,by+85,85,"Radius chunks",be==null?"1":""+Math.min(12,be.holoRadius()),2);
  height=make(bx+160,by+85,85,"Height below table",be==null?"1":""+be.holoHeight(),3);
  content=make(bx+12,by+143,270,"Text (| for newline)",
    be==null?"xSxLabs":be.holoText().replace('\n','|'),480);
  color=make(bx+12,by+181,92,"Color",be==null?"29D7EB":String.format("%06X",be.holoColor()),8);
  addRenderableWidget(Button.builder(Component.literal("APPLY"),b->save())
    .bounds(bx+204,by+178,88,23).build());
  switchMode();
 }
 private void switchMode(){
  boolean map=mode.equals("map"),custom=mode.equals("custom");
  size.visible=!map;size.active=!map;
  radius.visible=map;radius.active=map;
  content.visible=custom;content.active=custom;
  color.visible=!map;color.active=!map;
 }
 private void save(){
  if(terminal==null)return;
  int c=0x29d7eb;
  try{c=Integer.parseUnsignedInt(color.getValue().replace("#",""),16)&0xffffff;}
  catch(NumberFormatException ex){}
  int s=val(size,5,1,32),r=val(radius,1,1,12);
  ClientPacketDistributor.sendToServer(new HologramConfigPayload(
    terminal,mode,content.getValue().replace('|','\n'),c,
    s,val(height,1,1,32),s,r));
  onClose();
 }
 @Override public void onClose(){
  if(minecraft!=null&&minecraft.player!=null)minecraft.player.closeContainer();
  super.onClose();
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float tick){
  g.fill(bx-3,by-3,bx+307,by+219,0xff40d4ed);
  g.fill(bx,by,bx+304,by+216,0xf51a263b);
  g.text(font,"xSxLabs HOLOGRAM TERMINAL - "+mode.toUpperCase(),bx+12,by+9,0xff78eeff);
  g.text(font,mode.equals("map")?"RADIUS (CHUNKS)":"PROJECTION SIZE",bx+12,by+70,0xffb6eaff);
  g.text(font,"HEIGHT (BLOCKS BELOW)",bx+160,by+70,0xffb6eaff);
  if(mode.equals("map")){
   g.text(font,"3D terrain map - automatic size and proportions",bx+12,by+126,0xffd3e4f1);
   g.text(font,"Only already loaded chunks will be sampled.",bx+12,by+144,0xffa9c6d5);
  }else if(mode.equals("network")){
   g.text(font,"Live network information; uniformly scalable",bx+12,by+128,0xffd3e4f1);
  }else{
   g.text(font,"CUSTOM TEXT",bx+12,by+127,0xffd3e4f1);
   g.text(font,"COLOR HEX",bx+12,by+166,0xffd3e4f1);
  }
  g.text(font,"HEIGHT 1 = 1 block below holo table",bx+12,by+205,0xff91cde5);
 }
}
''',encoding="utf-8")

# Tool Belt-like wheel: hold G, point, RELEASE G to activate. No extra click.
wheel="client/NetworkActionWheelClient.java"
edit(wheel,"   if(cursorReleased){\n    mc.mouseHandler.grabMouse();",
     "   if(cursorReleased){\n    if(mc.player!=null&&mc.screen==null&&selected>=0)activate(selected);\n    mc.mouseHandler.grabMouse();")
p=J/wheel;s=p.read_text(encoding="utf-8")
start='  if(down&&!wasMouseDown&&selected>=0){'
end='  wasMouseDown=down;'
assert s.count(start)==1 and s.count(end)==1,("wheel input drift",s.count(start),s.count(end))
a=s.index(start);b=s.index(end,a)
s=s[:a]+'  // Tool Belt input: selection fires on hotkey release, not mouse click.\n'+s[b:]
start=' @SubscribeEvent public static void register(RegisterKeyMappingsEvent e)'
assert s.count(start)==1
s=s.replace(start,''' private static void activate(int action){
  switch(action){
   case 0->ClientPacketDistributor.sendToServer(new PowerArmorExitPayload());
   case 1->ClientPacketDistributor.sendToServer(new PortalActionPayload.Spawn());
   case 2->ClientPacketDistributor.sendToServer(new PortalActionPayload.Cycle());
   case 3->ClientPacketDistributor.sendToServer(new PowerArmorRecallPayload());
   default->{}
  }
 }
'''+start,1)
# Four radial slices with a gap and center hub, instead of overlapping boxes.
start='  g.fill(x-135,y-135,x+135,y+135,0xB9091726);'
end=' }\n}\n'
assert s.count(start)==1 and s.endswith(end),("wheel render drift",s.count(start))
a=s.index(start);b=s.rfind(end)
s=s[:a]+'''  for(int dy=-105;dy<=105;dy+=7)for(int dx=-105;dx<=105;dx+=7){
   double length=Math.sqrt(dx*dx+dy*dy);
   if(length<27||length>104)continue;
   int wedge=Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0);
   int color=wedge==selected?0xf12ad5e9:0xe21f344b;
   g.fill(x+dx,y+dy,x+dx+7,y+dy+7,color);
  }
  g.fill(x-25,y-25,x+25,y+25,0xff132538);
  g.text(mc.font,"xSxLabs",x-mc.font.width("xSxLabs")/2,y-9,0xff9bf7ff);
  g.text(mc.font,"G",x-mc.font.width("G")/2,y+4,0xffd0e2f2);
  for(int i=0;i<4;i++){
   int cx=x+(i==1?76:i==3?-76:0);
   int cy=y+(i==0?-76:i==2?76:0);
   String name=ACTIONS[i];
   int color=i==selected?0xffffffff:0xffbde8ee;
   g.text(mc.font,name,cx-mc.font.width(name)/2,cy-4,color);
  }
  g.text(mc.font,"Release G to activate",x-mc.font.width("Release G to activate")/2,y+126,0xffb7eaf5);
'''+s[b:]
p.write_text(s,encoding="utf-8")

# Server-authoritative rename UI: the user can open it with right-click on A.
# Existing UID SavedData is the sole source of truth, old worlds migrate.
add("portal/PortalRenamePayload.java",r'''package dev.obsidiannetwork.portal;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** V173_PORTAL_RENAME_314: validate owner, dimension, physical A, distance. */
public record PortalRenamePayload(BlockPos pos,String name) implements CustomPacketPayload {
 public static final Type<PortalRenamePayload> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","portal_rename"));
 public static final StreamCodec<RegistryFriendlyByteBuf,PortalRenamePayload> CODEC=
   StreamCodec.of((buf,p)->{buf.writeBlockPos(p.pos());buf.writeUtf(p.name(),48);},
      buf->new PortalRenamePayload(buf.readBlockPos(),buf.readUtf(48)));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToServer(TYPE,CODEC,(p,ctx)->{
    if(!(ctx.player() instanceof ServerPlayer player))return;
    if(player.isSpectator()||player.blockPosition().distSqr(p.pos())>64||
       !player.level().hasChunkAt(p.pos())||
       !player.level().getBlockState(p.pos()).is(ObsidianNetwork.NETWORK_PORTAL_A.get()))return;
    String clean=p.name().strip().replace("\n","").replace("\r","");
    if(clean.isEmpty()||clean.length()>48)return;
    var index=PortalIndex.get(player.level().getServer());
    String dim=player.level().dimension().identifier().toString();
    for(var a:index.owned(player.getUUID()))
     if(a.pos().equals(p.pos())&&a.dimension().equals(dim)){
      index.rename(player.getUUID(),a.uid(),clean);
      player.sendSystemMessage(net.minecraft.network.chat.Component.literal("Portal A renamed: "+clean));
      return;
     }
   });
  }
 }
}
''')
add("client/PortalRenameScreen.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.portal.PortalRenamePayload;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.core.BlockPos;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;

/** V173_PORTAL_RENAME_SCREEN_314 - native controls, no chest slot overlay. */
public final class PortalRenameScreen extends Screen {
 private final BlockPos pos;
 private final String oldName;
 private EditBox name;
 public PortalRenameScreen(BlockPos pos,String oldName){
  super(Component.literal("Rename Portal A"));
  this.pos=pos;this.oldName=oldName;
 }
 @Override protected void init(){
  super.init();
  int x=width/2,y=height/2;
  name=new EditBox(font,x-110,y-15,220,20,Component.literal("Portal name"));
  name.setMaxLength(48);name.setValue(oldName);addRenderableWidget(name);
  addRenderableWidget(Button.builder(Component.literal("SAVE"),b->save())
    .bounds(x-108,y+18,102,22).build());
  addRenderableWidget(Button.builder(Component.literal("CANCEL"),b->onClose())
    .bounds(x+6,y+18,102,22).build());
 }
 private void save(){
  String n=name.getValue().strip();
  if(n.isEmpty())return;
  ClientPacketDistributor.sendToServer(new PortalRenamePayload(pos,n));
  onClose();
 }
 @Override public void onClose(){
  if(minecraft!=null&&minecraft.player!=null)minecraft.player.closeContainer();
  super.onClose();
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=width/2,y=height/2;
  g.fill(x-124,y-58,x+124,y+55,0xff3acbda);
  g.fill(x-121,y-55,x+121,y+52,0xff182839);
  g.text(font,"PORTAL A - RENAME",x-105,y-42,0xff99f6ff);
 }
}
''')
# Hook the portal rename screen into the existing chest ScreenEvent.Opening.
edit("powerarmor/PowerArmorExitKeyClient.java",
     '''   if(!chest.getTitle().getString().startsWith("xSxLabs Hologram @"))return;''',
     '''   if(chest.getTitle().getString().startsWith("xSxLabs Portal Rename @")){
    String body=chest.getTitle().getString().substring("xSxLabs Portal Rename @".length());
    String[] parts=body.split("[|]",2);
    String[] coords=parts[0].split(",");
    if(coords.length==3)try{
     var at=new net.minecraft.core.BlockPos(Integer.parseInt(coords[0]),Integer.parseInt(coords[1]),Integer.parseInt(coords[2]));
     event.setNewScreen(new dev.obsidiannetwork.client.PortalRenameScreen(at,parts.length==2?parts[1]:""));
    }catch(NumberFormatException ignored){}
    return;
   }
   if(!chest.getTitle().getString().startsWith("xSxLabs Hologram @"))return;''')
# The server opens a name-only menu for the owner, never for portal B.
edit("portal/PortalGateBlock.java",
     '''  @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){''',
     r'''  private net.minecraft.world.InteractionResult rename(Level l,BlockPos p,Player player){
   if(!l.getBlockState(p).is( dev.obsidiannetwork.ObsidianNetwork.NETWORK_PORTAL_A.get()))
    return net.minecraft.world.InteractionResult.PASS;
   if(l instanceof ServerLevel sl&&player instanceof net.minecraft.server.level.ServerPlayer sp){
    var anchors=PortalIndex.get(sl.getServer()).owned(sp.getUUID());
    String dim=sl.dimension().identifier().toString();
    for(var a:anchors)if(a.pos().equals(p)&&a.dimension().equals(dim)){
     String title="xSxLabs Portal Rename @"+p.getX()+","+p.getY()+","+p.getZ()+"|"+a.name();
     sp.openMenu(new net.minecraft.world.SimpleMenuProvider(
       (id,inv,who)->net.minecraft.world.inventory.ChestMenu.threeRows(id,inv),
       net.minecraft.network.chat.Component.literal(title)));
     return net.minecraft.world.InteractionResult.SUCCESS;
    }
    sp.sendSystemMessage(net.minecraft.network.chat.Component.literal("Only the owner can rename this Portal A."));
   }
   return net.minecraft.world.InteractionResult.SUCCESS;
  }
  @Override protected net.minecraft.world.InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,
      Player player,net.minecraft.world.phys.BlockHitResult hit){return rename(l,p,player);}
  @Override protected net.minecraft.world.InteractionResult useItemOn(ItemStack held,BlockState s,Level l,BlockPos p,
      Player player,net.minecraft.world.InteractionHand hand,net.minecraft.world.phys.BlockHitResult hit){
   return hand==net.minecraft.world.InteractionHand.MAIN_HAND?rename(l,p,player):net.minecraft.world.InteractionResult.PASS;
  }
  @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){''')
# Note: original PortalGateBlock imports PortalIndex? Same package -> no import.
assert "V173_HOLO_SLOT_FREE_314" in (J/"client/HologramConfigScreen.java").read_text()
assert "WORLD_SURFACE" in (J/"client/V173WorldGhostRenderer.java").read_text()
assert "PortalRenamePayload" in (J/"portal/PortalRenamePayload.java").read_text()
print("V173_BUILD314_GUI_MAP_PORTALS_WHEEL_RENAME_PATCH_APPLIED")
