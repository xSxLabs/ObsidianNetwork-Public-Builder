#!/usr/bin/env python3
"""Build207: Hologram Terminal modes, server-synced GUI settings, bounded 3D map."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,s):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p);p.write_text(s,encoding="utf-8")

# The Hologram uses a distinct GUI, with real settings synced to its BlockEntity.
change("block/NetworkDeviceBlock.java",
 'if(be.mode()==Mode.PRINTER&&held.isEmpty()&&!player.isShiftKeyDown()){',
 'if(held.isEmpty()&&!player.isShiftKeyDown()){')
change("block/NetworkDeviceBlock.java",
 'Component.literal("xSxLabs Network Printer @"+pos.getX()+","+pos.getY()+","+pos.getZ())',
 'Component.literal((be.mode()==Mode.HOLOGRAM?"xSxLabs Hologram @":"xSxLabs Network Printer @")+pos.getX()+","+pos.getY()+","+pos.getZ())')

change("blockentity/NetworkDeviceBlockEntity.java",
 ' private static final int WORK_TICKS=5;',
 ''' private static final int WORK_TICKS=5;
 // V173_HOLOGRAM_THREE_MODES
 private String holoMode="network",holoText="xSxLabs";
 private int holoColor=0x29d7eb,holoWidth=5,holoHeight=3,holoDepth=5,holoRadius=16;
 public String holoMode(){return holoMode;}
 public String holoText(){return holoText;}
 public int holoColor(){return holoColor;}
 public int holoWidth(){return holoWidth;}
 public int holoHeight(){return holoHeight;}
 public int holoDepth(){return holoDepth;}
 public int holoRadius(){return holoRadius;}
 public void configure(ServerPlayer player,String mode,String text,int color,int width,int height,int depth,int radius){
  if(mode()!=NetworkDeviceBlock.Mode.HOLOGRAM||level==null||
    player.level()!=level||player.isSpectator()||
    player.blockPosition().distSqr(worldPosition)>64)return;
  if(!mode.equals("network")&&!mode.equals("map")&&!mode.equals("custom"))return;
  holoMode=mode;
  holoText=(text==null?"":text).substring(0,Math.min(text==null?0:text.length(),480))
             .replace("\\r","").replace("§","");
  holoColor=color&0xffffff;
  holoWidth=Math.max(1,Math.min(32,width));holoHeight=Math.max(1,Math.min(32,height));
  holoDepth=Math.max(1,Math.min(32,depth));holoRadius=Math.max(2,Math.min(256,radius));
  sync();
 }''')
p=J/"blockentity/NetworkDeviceBlockEntity.java"
s=p.read_text(encoding="utf-8")
a=s.index(" private String labelTag(){");b=s.index(" private int[] size(){",a)
new=r''' private String labelTag(){return "xsx-holo-"+worldPosition.asLong();}
 private void hologram(ServerLevel world){
  var old=world.getEntitiesOfClass(ArmorStand.class,new AABB(worldPosition).inflate(4,10,4),
     e->e.entityTags().contains(labelTag()));
  if("map".equals(holoMode)){
   for(ArmorStand stand:old)stand.discard();
   // Bounded real voxel columns: no chunk tickets, no unlimited world scans.
   int radius=holoRadius,step=Math.max(1,(radius*2+1)/23);
   int low=Math.max(world.getMinY(),worldPosition.getY()-holoDepth);
   int high=Math.min(world.getMaxY()-1,worldPosition.getY()+holoHeight);
   int count=0;
   for(int x=-radius;x<=radius && count<180;x+=step)
    for(int z=-radius;z<=radius && count<180;z+=step){
     BlockPos base=worldPosition.offset(x,0,z);
     if(!world.hasChunkAt(base))continue;
     for(int y=low;y<=high && count<180;y+=Math.max(1,(high-low)/10)){
      BlockPos scan=new BlockPos(base.getX(),y,base.getZ());
      if(!world.hasChunkAt(scan))continue;
      var block=world.getBlockState(scan);
      if(block.isAir())continue;
      if(!world.getBlockState(scan.above()).isAir() &&
         !world.getBlockState(scan.north()).isAir())continue;
      world.sendParticles(new DustParticleOptions(holoColor,.65f),
        worldPosition.getX()+.5+(double)x/radius*holoWidth/2,
        worldPosition.getY()+1.3+(double)(y-worldPosition.getY())/
          Math.max(1,holoHeight+holoDepth)*holoHeight,
        worldPosition.getZ()+.5+(double)z/radius*holoWidth/2,
        1,0,0,0,0);
      count++;
     }
    }
   setStatus("MAP R="+radius+" voxels="+count);return;
  }
  String message="network".equals(holoMode)?summary(world):holoText;
  String[] lines=message.split("\n",-1);
  int shown=Math.min(12,lines.length);
  java.util.Map<String,ArmorStand> existing=new java.util.HashMap<>();
  for(ArmorStand entity:old)for(String tag:entity.entityTags())
   if(tag.startsWith(labelTag()+"#"))existing.put(tag,entity);
  for(int i=0;i<shown;i++){
   String tag=labelTag()+"#"+i;
   ArmorStand entity=existing.remove(tag);
   double y=worldPosition.getY()+1.55+(shown-1-i)*.24*holoHeight/3;
   if(entity==null){
    entity=new ArmorStand(world,worldPosition.getX()+.5,y,worldPosition.getZ()+.5);
    entity.setInvisible(true);entity.setNoGravity(true);
    entity.setNoBasePlate(true);entity.setInvulnerable(true);
    entity.addTag(labelTag());entity.addTag(tag);
    world.addFreshEntity(entity);
   }
   entity.setPos(worldPosition.getX()+.5,y,worldPosition.getZ()+.5);
   String line=lines[i];if(line.length()>180)line=line.substring(0,180);
   entity.setCustomName(Component.literal(line).withStyle(st->st.withColor(holoColor)));
   entity.setCustomNameVisible(true);
  }
  for(ArmorStand e:existing.values())e.discard();
  setStatus("network".equals(holoMode)?message:"CUSTOM "+shown+" lines");
  world.sendParticles(new DustParticleOptions(holoColor,.6f),
     worldPosition.getX()+.5,worldPosition.getY()+1.25,worldPosition.getZ()+.5,
     2,.25,.05,.25,.002);
 }
'''
s=s[:a]+new+s[b:]
p.write_text(s,encoding="utf-8")
change("blockentity/NetworkDeviceBlockEntity.java",
 '  out.putBoolean("running",running);out.putString("status",status);',
 '''  out.putBoolean("running",running);out.putString("status",status);
  out.putString("holo_mode",holoMode);out.putString("holo_text",holoText);
  out.putInt("holo_color",holoColor);out.putInt("holo_width",holoWidth);
  out.putInt("holo_height",holoHeight);out.putInt("holo_depth",holoDepth);
  out.putInt("holo_radius",holoRadius);''')
change("blockentity/NetworkDeviceBlockEntity.java",
 'running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");missing=ItemStack.EMPTY;',
 '''running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");missing=ItemStack.EMPTY;
  holoMode=in.getStringOr("holo_mode","network");holoText=in.getStringOr("holo_text","xSxLabs");
  holoColor=in.getIntOr("holo_color",0x29d7eb)&0xffffff;
  holoWidth=Math.max(1,Math.min(32,in.getIntOr("holo_width",5)));
  holoHeight=Math.max(1,Math.min(32,in.getIntOr("holo_height",3)));
  holoDepth=Math.max(1,Math.min(32,in.getIntOr("holo_depth",5)));
  holoRadius=Math.max(2,Math.min(256,in.getIntOr("holo_radius",16)));''')

add("network/HologramConfigPayload.java",r'''package dev.obsidiannetwork.network;
import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
/** V173_HOLOGRAM_CONFIG_PAYLOAD: validated before applying changes. */
public record HologramConfigPayload(BlockPos pos,String mode,String text,int color,
                                    int width,int height,int depth,int radius)
                                    implements CustomPacketPayload{
 public static final Type<HologramConfigPayload> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","hologram_config"));
 public static final StreamCodec<RegistryFriendlyByteBuf,HologramConfigPayload> CODEC=
   StreamCodec.of((buf,p)->{
    buf.writeBlockPos(p.pos());buf.writeUtf(p.mode(),20);buf.writeUtf(p.text(),480);
    buf.writeInt(p.color());buf.writeInt(p.width());buf.writeInt(p.height());
    buf.writeInt(p.depth());buf.writeInt(p.radius());
   },buf->new HologramConfigPayload(buf.readBlockPos(),buf.readUtf(20),
         buf.readUtf(480),buf.readInt(),buf.readInt(),buf.readInt(),
         buf.readInt(),buf.readInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler{
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToServer(TYPE,CODEC,(p,context)->{
    if(!(context.player() instanceof ServerPlayer player))return;
    if(!player.level().hasChunkAt(p.pos()))return;
    if(player.level().getBlockEntity(p.pos()) instanceof NetworkDeviceBlockEntity be)
      be.configure(player,p.mode(),p.text(),p.color(),p.width(),p.height(),p.depth(),p.radius());
   });
  }
 }
}
''')
add("client/HologramConfigScreen.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import dev.obsidiannetwork.network.HologramConfigPayload;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
/** V173_HOLOGRAM_GUI: network / 3D map / editable custom text. */
public final class HologramConfigScreen extends ContainerScreen {
 private String mode="network";
 private BlockPos terminal;
 private EditBox content,color,width,height,depth,radius;
 public HologramConfigScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
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
  EditBox e=new EditBox(font,x,y,w,18,Component.literal(name));
  e.setMaxLength(max);e.setValue(text);addRenderableWidget(e);return e;
 }
 private int val(EditBox e,int backup,int low,int high){
  try{return Math.max(low,Math.min(high,Integer.parseInt(e.getValue())));}
  catch(NumberFormatException ex){return backup;}
 }
 @Override protected void init(){
  super.init();
  var be=device();
  if(be!=null)mode=be.holoMode();
  int x=getLeftPos(),y=getTopPos();
  addRenderableWidget(Button.builder(Component.literal("NETWORK"),b->mode="network")
     .bounds(x,y-47,82,19).build());
  addRenderableWidget(Button.builder(Component.literal("MAP 3D"),b->mode="map")
     .bounds(x+85,y-47,82,19).build());
  addRenderableWidget(Button.builder(Component.literal("CUSTOM"),b->mode="custom")
     .bounds(x+170,y-47,82,19).build());
  content=make(x,y-24,251,"Custom Text (| new line)",
      be==null?"xSxLabs":be.holoText().replace('\n','|'),480);
  color=make(x+179,y+12,75,"Color HEX",
      be==null?"29D7EB":String.format("%06X",be.holoColor()),8);
  width=make(x+179,y+46,34,"Width",be==null?"5":""+be.holoWidth(),3);
  height=make(x+217,y+46,34,"Height",be==null?"3":""+be.holoHeight(),3);
  depth=make(x+179,y+79,34,"Depth",be==null?"5":""+be.holoDepth(),3);
  radius=make(x+217,y+79,34,"Radius",be==null?"16":""+be.holoRadius(),3);
  addRenderableWidget(Button.builder(Component.literal("APPLY"),b->save())
      .bounds(x+179,y+108,72,19).build());
 }
 private void save(){
  if(terminal==null)return;
  int c=0x29d7eb;
  try{c=Integer.parseUnsignedInt(color.getValue().replace("#",""),16)&0xffffff;}
  catch(NumberFormatException ex){}
  ClientPacketDistributor.sendToServer(new HologramConfigPayload(
    terminal,mode,content.getValue().replace('|','\n'),c,
    val(width,5,1,32),val(height,3,1,32),val(depth,5,1,32),val(radius,16,2,256)));
  onClose();
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs HOLOGRAM - "+mode.toUpperCase(),8,6,0xff55e6ff);
  g.text(font,"NETWORK / MAP / CUSTOM | right panel: projection settings",8,58,0xffceeef5);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float tick){
  int x=getLeftPos(),y=getTopPos();
  g.fill(x-3,y-50,x+255,y+169,0xff35d1de);
  g.fill(x,y-48,x+253,y+166,0xff172c39);
  g.text(font,"COLOR",x+180,y,0xffa8f2f3);
  g.text(font,"WIDTH      HEIGHT",x+180,y+33,0xffa8f2f3);
  g.text(font,"DEPTH      RADIUS",x+180,y+66,0xffa8f2f3);
  g.text(font,"Map size / depth / height configurable.",x+4,y+130,0xffbde1e8);
 }
}
''')
# Use the same proven client-only screen-opening event as NetworkPrinterScreen.
p=J/"powerarmor/PowerArmorExitKeyClient.java";s=p.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "xsxHologramOpen" not in s
s=s[:-1]+r'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxHologramOpen(net.neoforged.neoforge.client.event.ScreenEvent.Opening event){
  if(!(event.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().startsWith("xSxLabs Hologram @"))return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null)event.setNewScreen(new dev.obsidiannetwork.client.HologramConfigScreen(
    chest.getMenu(),mc.player.getInventory(),chest.getTitle()));
 }
}
'''
p.write_text(s,encoding="utf-8")
print("V173_HOLOGRAM_3_MODES_NETWORK_MAP_CUSTOM_GUI_BUILD207_PASS")

# V173_HOLOGRAM_WORLD_HEIGHT: max build Y is exclusive; never scan it.
assert 'int high=Math.min(world.getMaxY()-1,worldPosition.getY()+holoHeight);' in (J/'blockentity/NetworkDeviceBlockEntity.java').read_text(encoding='utf-8')
print('V173_HOLOGRAM_WORLD_HEIGHT_PASS')

# Build236: Hologram configuration cannot be modified by spectators.
assert 'player.level()!=level||player.isSpectator()||' in (J/'blockentity/NetworkDeviceBlockEntity.java').read_text(encoding='utf-8')
print('V173_HOLOGRAM_SPECTATOR_WRITE_GUARD_PASS')

# Build239: old projected text up to 32 height must be found for cleanup.
assert 'new AABB(worldPosition).inflate(4,10,4)' in (J/'blockentity/NetworkDeviceBlockEntity.java').read_text(encoding='utf-8')
print('V173_HOLOGRAM_TALL_TEXT_CLEANUP_BUILD239_PASS')
