#!/usr/bin/env python3
"""Build328: actual visible hologram submits, strict facaded Network Vision,
conditional action wheel and compact 1x2 Portal-Gun-like apertures.

Runs ONLY on v1.7.3, after volumetric Build327. No save-format or FE changes.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def transform(path, old, new, times=1):
    file=J/path
    src=file.read_text(encoding="utf-8")
    assert src.count(old)==times, ("V173_BUILD328_SOURCE_DRIFT",path,src.count(old),old[:90])
    file.write_text(src.replace(old,new),encoding="utf-8")

renderer="client/V173WorldGhostRenderer.java"
# Source-based mode selection was map-only. All terminal modes need the same
# discovery and a frame-bound world-space draw, not an unobserved server entity.
transform(renderer,'device.holoMode().equals("map")',
          'device.mode()==dev.obsidiannetwork.block.NetworkDeviceBlock.Mode.HOLOGRAM',2)
transform(renderer,
 '   lastSample=now;mapSamples=sampleMap(mc,mapTerminal,be);',
 '   lastSample=now;mapSamples=sampleMap(mc,mapTerminal,be);')
transform(renderer,
 '  long now=mc.level.getGameTime();\n  if(lastSample==Long.MIN_VALUE||now-lastSample>=10L){',
 '''  if(!"map".equals(be.holoMode())){
   textProjection(mc,ev,cam,mapTerminal,be);
   return;
  }
  // The mode label remains visible even while terrain tiles are loading.
  textLine(mc,ev,cam,mapTerminal,be,"MAP 3D",0,0.47F);
  long now=mc.level.getGameTime();
  if(lastSample==Long.MIN_VALUE||now-lastSample>=10L){''')
# Build306's sample condition differs from Build303's; use exact resulting anchor.
transform(renderer,
 ' private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,',
 r''' // V173_HOLO_RENDER_328: text is submitted into the same modern 26.1
 // feature pipeline as 3D map blocks. SEE_THROUGH makes the projection visible
 // at the requested below-table height even if a solid block is in front.
 private static void textLine(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 camera,
         BlockPos origin,NetworkDeviceBlockEntity be,String line,int index,float sizeFactor){
   if(line==null||line.isBlank())return;
   String clipped=line.length()>58?line.substring(0,58):line;
   var text=net.minecraft.network.chat.Component.literal(clipped);
   PoseStack p=ev.getPoseStack();
   p.pushPose();
   double x=origin.getX()+.5D;
   double y=origin.getY()-be.holoHeight()+.55D+index*sizeFactor*.75D;
   double z=origin.getZ()+.5D;
   p.translate(x-camera.x,y-camera.y,z-camera.z);
   p.mulPose(ev.getLevelRenderState().cameraRenderState.orientation);
   float scale=Math.max(.016F,Math.min(.11F,be.holoWidth()*.0095F))*sizeFactor;
   p.scale(-scale,-scale,scale);
   ev.getSubmitNodeCollector().submitText(
       p,-mc.font.width(clipped)/2F,0F,text.getVisualOrderText(),
       true,net.minecraft.client.gui.Font.DisplayMode.SEE_THROUGH,
       FULL_BRIGHT,0xff000000|(be.holoColor()&0xffffff),0x77061a2f,0);
   p.popPose();
 }
 private static void textProjection(Minecraft mc,SubmitCustomGeometryEvent ev,
       Vec3 cam,BlockPos t,NetworkDeviceBlockEntity be){
  // TextDisplay entities are not required: custom text always has a client draw.
  String msg="custom".equals(be.holoMode())?be.holoText():
             "NETWORK\n"+(be.status()==null||be.status().isBlank()?"ONLINE":be.status());
  if(msg.isBlank())msg="CUSTOM";
  String[] lines=msg.split("\n",-1);
  for(int i=0;i<Math.min(lines.length,12);i++)
    textLine(mc,ev,cam,t,be,lines[i],i,1F);
 }
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,''')
# Eliminate duplicate, server-owned text holograms: all normal modes are now
# client-submitted, but still discard old display entities on existing saves.
transform("blockentity/NetworkDeviceBlockEntity.java",
 '  if("map".equals(holoMode)){',
 '  if("map".equals(holoMode)||"network".equals(holoMode)||"custom".equals(holoMode)){')
transform("blockentity/NetworkDeviceBlockEntity.java",
 '   setStatus("MAP 3D R="+holoRadius+" H="+holoHeight);return;',
 '''    setStatus("map".equals(holoMode)?"MAP 3D R="+holoRadius+" H="+holoHeight:
      "network".equals(holoMode)?summary(world):"CUSTOM "+holoText.length()+" chars");
    return;''')

# Sync the live network status to nearby clients; otherwise the new client
# projection can remain stuck displaying the stale initial "IDLE" value.
transform("blockentity/NetworkDeviceBlockEntity.java",
 ' private void setStatus(String s){if(!s.equals(status)){status=s;setChanged();}}',
 ''' private void setStatus(String s){if(!s.equals(status)){
  status=s;setChanged();
  if(level!=null&&!level.isClientSide()&&
     mode()==dev.obsidiannetwork.block.NetworkDeviceBlock.Mode.HOLOGRAM)
   level.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);
 }}''')

# Tight 1-wide x 2-tall portal aperture; current logical anchor stays one block
# so old worlds/owner-index/teleport selection remain valid.
portal=J/"client/V173WorldGhostRenderer.java"
src=portal.read_text(encoding="utf-8")
start=src.index(" private static void portals(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam){")
brace=src.index("{",start)
depth=0
end=None
for i in range(brace,len(src)):
    if src[i]=="{":depth+=1
    elif src[i]=="}":
        depth-=1
        if depth==0:
            end=i+1;break
assert end is not None
old=src[start:end]
assert "Blocks.OBSIDIAN" in old and "2 blocks wide and 3 high" in old
new=r''' // V173_PORTALGUN_1X2_328: cyan A, orange B; open curved 1x2 aperture.
 // Thin animated glass layers with illuminated oval rim; no nether frame.
 private static void portals(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam){
  long now=mc.level.getGameTime();
  if(portalWorld!=mc.level){
   portalWorld=mc.level;portalPositions=java.util.List.of();
   lastPortalScan=Long.MIN_VALUE;
  }
  if(lastPortalScan==Long.MIN_VALUE||now-lastPortalScan>=2L){
   lastPortalScan=now;
   java.util.ArrayList<BlockPos> found=new java.util.ArrayList<>();
   BlockPos player=mc.player.blockPosition();
   search:for(int dy=-6;dy<=6;dy++)for(int dx=-12;dx<=12;dx++)
    for(int dz=-12;dz<=12;dz++){
     BlockPos at=player.offset(dx,dy,dz);
     if(!mc.level.hasChunkAt(at))continue;
     BlockState s=mc.level.getBlockState(at);
     if(s.is(ObsidianNetwork.NETWORK_PORTAL_A.get())||
        s.is(ObsidianNetwork.NETWORK_PORTAL_B.get())){
       found.add(at);
       if(found.size()>=20)break search;
     }
    }
   portalPositions=found;
  }
  for(BlockPos at:portalPositions){
   if(!mc.level.hasChunkAt(at))continue;
   BlockState physical=mc.level.getBlockState(at);
   boolean a=physical.is(ObsidianNetwork.NETWORK_PORTAL_A.get());
   boolean b=physical.is(ObsidianNetwork.NETWORK_PORTAL_B.get());
   if(!a&&!b)continue;
   BlockState glow=(a?Blocks.LIGHT_BLUE_STAINED_GLASS:
                       Blocks.ORANGE_STAINED_GLASS).defaultBlockState();
   BlockState core=(a?Blocks.CYAN_STAINED_GLASS:
                       Blocks.YELLOW_STAINED_GLASS).defaultBlockState();
   double centerX=at.getX()+.5D,baseY=at.getY(),z=at.getZ()+.48D;
   // 32 horizontal bands trace an ellipse exactly 1 block wide, 2 high.
   // Distinct animated center waves suggest a Portal Gun energy surface.
   for(int i=0;i<32;i++){
    double low=i/16D,mid=(i+.5D)/16D;
    double heightRatio=mid-1D;
    double half=.485D*Math.sqrt(Math.max(0,1-heightRatio*heightRatio));
    double outer=Math.max(.012D,2*half);
    double inner=Math.max(.006D,outer-.075D);
    drawSized(mc,ev,cam,glow,centerX-half,baseY+low,z,.043D,.063D,.075D);
    drawSized(mc,ev,cam,glow,centerX+half-.043D,baseY+low,z,.043D,.063D,.075D);
    double shift=.012D*Math.sin(now*.16D+i*.65D);
    drawSized(mc,ev,cam,(i+(int)(now/4L))%6<2?core:glow,
       centerX-inner/2D+shift,baseY+low,z+.012D,inner,.063D,.034D);
   }
  }
 }'''
src=src[:start]+new+src[end:]
portal.write_text(src,encoding="utf-8")
transform("portal/PortalGateBlock.java",
 'return box(0,0,6,16,48,10);',
 'return box(0,0,6,16,32,10);')
transform("portal/PortalGateBlockEntity.java",
 'player.getY()>pos.getY()+2.85',
 'player.getY()>pos.getY()+1.85')

# VISION: no world particles, no revealing planters, energy fixtures or
# machines. Only facaded network/other cables and importer/exporter blocks;
# draw through-occlusion HUD markers precisely over client-projected centers.
vision=J/"client/NetworkVisionClient.java"
assert vision.exists() and "V173_NETWORK_VISION" in vision.read_text(encoding="utf-8")
vision.write_text(r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EquipmentSlot;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/** V173_VISION_FACADE_ONLY_328 - specifically facaded cables and IO only.
 * A screen-space projected marker bypasses the opaque facade's depth buffer.
 * Never outline solid terrain, planter, terminal, printer or other machinery.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkVisionClient {
 private NetworkVisionClient(){}
 private static boolean enabled;
 public static boolean installed(){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   var armor=mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   String tags=armor.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(tags!=null)for(String id:tags.split(","))
    if("network_vision".equals(id))return true;
  }
  return false;
 }
 private static boolean ready(){
  var mc=Minecraft.getInstance();
  if(mc.player==null||!installed())return false;
  int tier=PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1)return false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   var armor=mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(PowerArmorRuntime.tier(armor,i)!=tier||EnergyTool.energy(armor)<100L)return false;
  }
  return true;
 }
 public static boolean active(){return enabled&&ready();}
 public static void toggleFromWheel(){
  if(!ready()){enabled=false;return;}
  enabled=!enabled;
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post ignored){
  var mc=Minecraft.getInstance();
  if(mc.player==null||mc.level==null||!ready())enabled=false;
 }
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  if(!active())return;
  var mc=Minecraft.getInstance();
  if(mc.screen!=null||mc.level==null||mc.player==null)return;
  var g=event.getGuiGraphics();
  var camera=mc.gameRenderer.getMainCamera();
  var from=camera.position();
  var inverse=new Quaternionf(camera.rotation()).conjugate();
  int w=mc.getWindow().getGuiScaledWidth(),h=mc.getWindow().getGuiScaledHeight();
  double fov=Math.max(35D,Math.min(110D,camera.getFov()));
  double focal=h/(2D*Math.tan(Math.toRadians(fov/2D)));
  BlockPos center=mc.player.blockPosition();
  int count=0;
  for(int y=-5;y<=5&&count<80;y++)
   for(int x=-9;x<=9&&count<80;x++)
    for(int z=-9;z<=9&&count<80;z++){
     BlockPos p=center.offset(x,y,z);
     if(!mc.level.hasChunkAt(p))continue;
     var state=mc.level.getBlockState(p);
     String id=BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
     boolean cable=id.endsWith("_cable")||id.equals("conduit_bundle");
     boolean input=id.equals("importer")||id.endsWith("_importer");
     boolean output=id.equals("exporter")||id.endsWith("_exporter");
     if(!cable&&!input&&!output)continue;
     if(!(mc.level.getBlockEntity(p) instanceof
          dev.obsidiannetwork.blockentity.FacadeCable facade)
         ||facade.facadeState().isAir())continue;
     Vector3f local=new Vector3f(
        (float)(p.getX()+.5-from.x),
        (float)(p.getY()+.5-from.y),
        (float)(p.getZ()+.5-from.z));
     inverse.transform(local);
     if(local.z>=-.15F)continue;
     int sx=(int)Math.round(w/2D+local.x*focal/-local.z);
     int sy=(int)Math.round(h/2D-local.y*focal/-local.z);
     if(sx<0||sx>=w||sy<0||sy>=h)continue;
     String label=cable?"CABLE":input?"IMPORTER":"EXPORTER";
     int color=cable?0xff38ddff:input?0xff4effb0:0xffffbb54;
     int side=(int)Math.max(4D,Math.min(15D,15D/-local.z));
     g.fill(sx-side,sy-side,sx+side,sy-side+1,color);
     g.fill(sx-side,sy+side-1,sx+side,sy+side,color);
     g.fill(sx-side,sy-side,sx-side+1,sy+side,color);
     g.fill(sx+side-1,sy-side,sx+side,sy+side,color);
     g.text(mc.font,label,sx-mc.font.width(label)/2,sy-side-11,color);
     count++;
    }
 }
}
''',encoding="utf-8")
# Old K-key remains in source for other backwards-compat references, but is
# no longer registered. The action wheel is the only activation mechanism.
transform("client/ClientModEvents.java",
 'event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.VISION);',
 '// Network Vision is toggled from the conditional action wheel only.')

wheel="client/NetworkActionWheelClient.java"
transform(wheel,
 '''   default->{}
  }
 }
 @SubscribeEvent public static void register''',
 '''    case 4->NetworkVisionClient.toggleFromWheel();
    default->{}
   }
  }
  @SubscribeEvent public static void register''')
transform(wheel,
 '''  selected=distance<27||distance>108?-1:
    (Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0));''',
 '''  selected=NetworkVisionClient.installed()&&dx>=46&&dx<=110&&dy>=53&&dy<=92?4:
    distance<27||distance>108?-1:
    (Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0));''')
transform(wheel,
 '''  g.text(mc.font,"xSxLabs",x-mc.font.width("xSxLabs")/2,y-9,0xff9bf7ff);
  g.text(mc.font,"G",x-mc.font.width("G")/2,y+4,0xffd0e2f2);''',
 '''  g.text(mc.font,"xSxLabs",x-mc.font.width("xSxLabs")/2,y-9,0xff9bf7ff);
  g.text(mc.font,"G",x-mc.font.width("G")/2,y+4,0xffd0e2f2);
  // Optional fifth wheel action is offset: opening/releasing G at the
  // screen center must NEVER toggle vision without deliberate selection.
  if(NetworkVisionClient.installed()){
   int shade=selected==4?0xf12ad5e9:0xe21f344b;
   g.fill(x+46,y+53,x+110,y+92,shade);
   g.text(mc.font,"NETWORK",x+79-mc.font.width("NETWORK")/2,y+61,0xff9bf7ff);
   String vis=NetworkVisionClient.active()?"VISION ON":"VISION OFF";
   g.text(mc.font,vis,x+79-mc.font.width(vis)/2,y+75,
      NetworkVisionClient.active()?0xff62ffbe:0xffd0e2f2);
  }''')

assert "V173_HOLO_RENDER_328" in (J/renderer).read_text()
assert "V173_PORTALGUN_1X2_328" in (J/renderer).read_text()
assert "V173_VISION_FACADE_ONLY_328" in vision.read_text()
print("V173_BUILD328_HOLO_ALL_MODES_VISION_FACADE_WHEEL_PORTAL_1X2_PATCH_PASS")
