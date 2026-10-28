#!/usr/bin/env python3
"""v1.7.3 postpatch: real non-occluding antenna shapes, valid portal models, GUI
and client-only world-space preview. Applies AFTER all legacy feature patches."""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def replace(rel,old,new,count=1):
 p=J/rel;s=p.read_text(encoding="utf-8")
 if s.count(old)!=count:raise RuntimeError("V173_VISUAL_SOURCE_DRIFT "+rel+" "+old[:85]+" count="+str(s.count(old)))
 p.write_text(s.replace(old,new,count),encoding="utf-8")

def put(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")

# A full opaque cube shape makes Minecraft cull the face of a NEIGHBOR
# even when the model visually occupies only the small antenna footprint.
for slug,cls in (("network_signal_transmitter",True),("network_signal_receiver",False)):
 path=J/"ObsidianNetwork.java";s=path.read_text(encoding="utf-8")
 old='BLOCKS.registerBlock("'+slug+'",\n          p -> new dev.obsidiannetwork.block.NetworkSignalRelayBlock(p,'+('true' if cls else 'false')+'),\n          p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F));'
 new=old.replace('.strength(3.0F,8.0F));','.strength(3.0F,8.0F).noOcclusion());')
 if s.count(old)!=1:raise RuntimeError("antenna register source drift: "+slug)
 path.write_text(s.replace(old,new,1),encoding="utf-8")

replace("block/NetworkSignalRelayBlock.java",
 ' @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}',
 ''' // V173_ANTENNA_NO_FACE_CULL: nearby full blocks must always draw their faces.
 private static final net.minecraft.world.phys.shapes.VoxelShape ANTENNA_SHAPE=
    net.minecraft.world.phys.shapes.Shapes.or(
       net.minecraft.world.level.block.Block.box(1,0,1,15,4,15),
       net.minecraft.world.level.block.Block.box(6,4,6,10,16,10));
 @Override protected net.minecraft.world.phys.shapes.VoxelShape getShape(BlockState s,
      net.minecraft.world.level.BlockGetter level,BlockPos pos,
      net.minecraft.world.phys.shapes.CollisionContext context){return ANTENNA_SHAPE;}
 @Override protected net.minecraft.world.phys.shapes.VoxelShape getOcclusionShape(BlockState s){
      return net.minecraft.world.phys.shapes.Shapes.empty();
 }
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}''')
def cube(a,b,mat):
 return {"from":a,"to":b,"faces":{f:{"texture":"#"+mat} for f in ("north","south","east","west","up","down")}}
for name,light in (("network_signal_transmitter","minecraft:block/cyan_concrete"),
                   ("network_signal_receiver","minecraft:block/lime_concrete")):
 model={"ambientocclusion":False,
        "textures":{"particle":"minecraft:block/obsidian","base":"minecraft:block/obsidian",
                    "metal":"minecraft:block/iron_block","signal":light},
        "elements":[cube([1,0,1],[15,3,15],"base"),cube([4,3,4],[12,5,12],"metal"),
                    cube([7,5,7],[9,15,9],"metal"),cube([5,13,5],[11,16,11],"signal"),
                    cube([1,3,1],[4,5,4],"metal"),cube([12,3,1],[15,5,4],"metal"),
                    cube([1,3,12],[4,5,15],"metal"),cube([12,3,12],[15,5,15],"metal"),
                    cube([5,7,7],[7,9,9],"signal"),cube([9,7,7],[11,9,9],"signal"),
                    cube([7,7,5],[9,9,7],"signal"),cube([7,7,9],[9,9,11],"signal")]}
 put(R/"models/block"/(name+".json"),model)
 put(R/"blockstates"/(name+".json"),{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 put(R/"models/item"/(name+".json"),{"parent":"obsidiannetwork:block/"+name})
 put(R/"items"/(name+".json"),{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+name}})

# Legacy 2x3 portal model had out-of-range -8..48 cuboids. These are not
# safe for all 26.1 block-model loaders; use a bounded, complete 3-D frame.
# Keep server-side 2x3 traversal/owner logic unchanged.
for name,light in (("network_portal_a","minecraft:block/purple_stained_glass"),
                   ("network_portal_b","minecraft:block/light_blue_stained_glass")):
 model={"ambientocclusion":False,"textures":{"particle":"minecraft:block/obsidian",
        "frame":"minecraft:block/obsidian","window":{"sprite":light,"force_translucent":True}},
        "elements":[cube([0,0,5],[3,16,11],"frame"),cube([13,0,5],[16,16,11],"frame"),
         cube([3,13,5],[13,16,11],"frame"),cube([3,0,5],[13,3,11],"frame"),
         cube([3,3,7.4],[13,13,8.6],"window")]}
 put(R/"models/block"/(name+".json"),model)
 put(R/"blockstates"/(name+".json"),{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 put(R/"models/item"/(name+".json"),{"parent":"obsidiannetwork:block/"+name})
 put(R/"items"/(name+".json"),{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+name}})

# 26.1 AbstractContainerScreen accepts explicit dimensions in its
# constructor; ContainerScreen cannot resize because imageWidth is final.
# Suppress legacy slot rendering, never make up a non-existent renderSlot API.
ui="client/HologramConfigScreen.java"
replace(ui,"import net.minecraft.client.gui.screens.inventory.ContainerScreen;",
          "import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;")
replace(ui,"public final class HologramConfigScreen extends ContainerScreen {",
          "public final class HologramConfigScreen extends AbstractContainerScreen<ChestMenu> {")
replace(ui,"super(menu,inventory,title);","super(menu,inventory,title,286,242);")
replace(ui,'  addRenderableWidget(Button.builder(Component.literal("NETWORK")',
          '  addRenderableWidget(Button.builder(Component.literal("NETWORK")')
# Existing controls are moved INSIDE the resized custom panel.
for before,after in (
 ('.bounds(x,y-47,82,19)', '.bounds(x+9,y+22,82,19)'),
 ('.bounds(x+85,y-47,82,19)', '.bounds(x+96,y+22,82,19)'),
 ('.bounds(x+170,y-47,82,19)', '.bounds(x+183,y+22,82,19)'),
 ('content=make(x,y-24,251,', 'content=make(x+10,y+67,250,'),
 ('color=make(x+179,y+12,75,', 'color=make(x+10,y+112,95,'),
 ('width=make(x+179,y+46,34,', 'width=make(x+136,y+112,55,'),
 ('height=make(x+217,y+46,34,', 'height=make(x+203,y+112,55,'),
 ('depth=make(x+179,y+79,34,', 'depth=make(x+136,y+151,55,'),
 ('radius=make(x+217,y+79,34,', 'radius=make(x+203,y+151,55,'),
 ('.bounds(x+179,y+108,72,19)', '.bounds(x+183,y+192,94,21)'),
 ('g.fill(x-3,y-50,x+255,y+169,0xff35d1de);','g.fill(x-3,y-3,x+286,y+242,0xff35d1de);'),
 ('g.fill(x,y-48,x+253,y+166,0xff172c39);','g.fill(x,y,x+283,y+239,0xff172c39);'),
 ('g.text(font,"COLOR",x+180,y,0xffa8f2f3);','g.text(font,"COLOR",x+10,y+100,0xffa8f2f3);'),
 ('g.text(font,"WIDTH      HEIGHT",x+180,y+33,0xffa8f2f3);',
  'g.text(font,"WIDTH          HEIGHT",x+136,y+100,0xffa8f2f3);'),
 ('g.text(font,"DEPTH      RADIUS",x+180,y+66,0xffa8f2f3);',
  'g.text(font,"DEPTH          RADIUS",x+136,y+139,0xffa8f2f3);'),
 ('g.text(font,"Map size / depth / height configurable.",x+4,y+130,0xffbde1e8);',
  'g.text(font,"3D MAP: width / height / depth / radius",x+10,y+220,0xffbde1e8);'),
):
 replace(ui,before,after)
replace(ui,
 ' @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){',
 ''' // Configure-only screen. Inherited ChestMenu is a transport/session
 // mechanism: it must never paint a fake player hotbar over custom settings.
 @Override protected void extractSlots(GuiGraphicsExtractor g,int mx,int my){}
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''')

# Hologram particles expired long before the old two-second refresh.
# Keep diagnostics, but refresh map 4x more often without forcing chunks.
replace("blockentity/NetworkDeviceBlockEntity.java",
 '''if(world.getGameTime()%40==0)be.hologram(world);''',
 '''if(world.getGameTime()%("map".equals(be.holoMode)?10:40)==0)be.hologram(world);''')

# Render actual 3-D block models in the 26.1 feature-submit pipeline; no
# client world modifications, fake placed blocks or outdated PoseStack API.
render=J/"client/V173WorldGhostRenderer.java"
if render.exists():raise RuntimeError("Duplicate V173WorldGhostRenderer")
render.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity;
import dev.obsidiannetwork.item.NetworkBlueprintItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.SubmitCustomGeometryEvent;

/** V173_REAL_3D_GHOST: block-model submits, no ephemeral particles for shapes.
 * Uses loaded chunks only and a bounded budget per frame. No world mutation.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V173WorldGhostRenderer {
 private V173WorldGhostRenderer(){}
 private static final BlockDisplayContext CONTEXT=BlockDisplayContext.create();
 private static final int FULL_BRIGHT=0x00F000F0;

 private static void draw(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 camera,
                          BlockState state,double x,double y,double z,double scale){
  PoseStack pose=ev.getPoseStack();
  pose.pushPose();
  pose.translate(x-camera.x,y-camera.y,z-camera.z);
  if(scale!=1D)pose.scale((float)scale,(float)scale,(float)scale);
  BlockModelRenderState model=new BlockModelRenderState();
  mc.getBlockModelResolver().update(model,state,CONTEXT);
  model.submitWithZOffset(pose,ev.getSubmitNodeCollector(),FULL_BRIGHT,
        OverlayTexture.NO_OVERLAY,0);
  pose.popPose();
 }
 @SubscribeEvent public static void submit(SubmitCustomGeometryEvent ev){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.screen!=null||mc.player.isSpectator())return;
  Vec3 camera=ev.getLevelRenderState().cameraRenderState.pos;
  var held=mc.player.getMainHandItem();
  if(held.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))
    blueprint(mc,ev,camera,held);
  map(mc,ev,camera);
 }
 private static void blueprint(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam,
                               net.minecraft.world.item.ItemStack held){
  String anchor=NetworkBlueprintItem.read(held,"xsxlabs_anchor");
  String prefix=mc.level.dimension().identifier()+"|";
  if(!anchor.startsWith(prefix))return;
  String[] a=anchor.substring(prefix.length()).split("[|]");
  String[] d=NetworkBlueprintItem.read(held,"xsxlabs_size").split(",");
  if(a.length!=3||d.length!=3)return;
  int x,y,z,sx,sy,sz,rot=0;
  try{
   x=Integer.parseInt(a[0]);y=Integer.parseInt(a[1]);z=Integer.parseInt(a[2]);
   sx=Integer.parseInt(d[0]);sy=Integer.parseInt(d[1]);sz=Integer.parseInt(d[2]);
   String spin=NetworkBlueprintItem.read(held,"xsxlabs_rotation");
   if(!spin.isEmpty())rot=Integer.parseInt(spin);
  }catch(NumberFormatException ignored){return;}
  if(sx<1||sy<1||sz<1||sx>16||sy>16||sz>16||rot<0||rot>7)return;
  var ids=NetworkBlueprintItem.blocks(held);
  String[] states=NetworkBlueprintItem.read(held,"xsxlabs_states").split(";",-1);
  int shown=0,volume=sx*sy*sz;
  // Geometry is capped to avoid graphics/TPS spikes on 4096-block schematics.
  int stride=Math.max(1,(volume+255)/256);
  for(int n=0;n<Math.min(ids.size(),volume)&&shown<256;n+=stride){
   if("minecraft:air".equals(ids.get(n)))continue;
   int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);
   int px=rot>=4?sx-1-dx:dx,pz=dz;
   switch(rot%4){
    case 1->{int old=px;px=sz-1-pz;pz=old;}
    case 2->{px=sx-1-px;pz=sz-1-pz;}
    case 3->{int old=px;px=pz;pz=sx-1-old;}
   }
   BlockPos at=new BlockPos(x+px,y+dy,z+pz);
   if(at.getY()<mc.level.getMinY()||at.getY()>=mc.level.getMaxY()||
      !mc.level.hasChunkAt(at)||!mc.level.getBlockState(at).isAir())continue;
   Identifier id=Identifier.tryParse(ids.get(n));
   if(id==null)continue;
   var block=BuiltInRegistries.BLOCK.getValue(id);
   if(block==null||block==Blocks.AIR)continue;
   BlockState state=block.defaultBlockState();
   // Use saved blockstate for shape/orientation of every represented model.
   if(n<states.length)for(String pair:states[n].split("&")){
    int sep=pair.indexOf('=');
    if(sep<1)continue;
    var prop=block.getStateDefinition().getProperty(pair.substring(0,sep));
    if(prop!=null)state=withProperty(state,prop,pair.substring(sep+1));
   }
   if(rot>=4)state=state.mirror(Mirror.FRONT_BACK);
   for(int i=0;i<rot%4;i++)state=state.rotate(Rotation.CLOCKWISE_90);
   draw(mc,ev,cam,state,at.getX(),at.getY(),at.getZ(),1D);
   shown++;
  }
 }
 @SuppressWarnings({"rawtypes","unchecked"})
 private static BlockState withProperty(BlockState state,
      net.minecraft.world.level.block.state.properties.Property prop,String value){
  return (BlockState)prop.getValue(value)
           .map(v->state.setValue(prop,(Comparable)v)).orElse(state);
 }
 private static BlockPos mapTerminal;
 private static net.minecraft.client.multiplayer.ClientLevel mapWorld;
 private static long lastDiscovery=Long.MIN_VALUE;
 private static java.util.List<MapVoxel> mapSamples=java.util.List.of();
 private static long lastSample=Long.MIN_VALUE;
 private record MapVoxel(BlockState state,double x,double y,double z){}
 private static void map(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam){
  if(mapWorld!=mc.level){
   mapWorld=mc.level;mapTerminal=null;lastDiscovery=Long.MIN_VALUE;
   lastSample=Long.MIN_VALUE;mapSamples=java.util.List.of();
  }
  NetworkDeviceBlockEntity be=null;
  if(mapTerminal!=null&&mc.level.hasChunkAt(mapTerminal)&&
     mc.player.blockPosition().distSqr(mapTerminal)<=256){
   var existing=mc.level.getBlockEntity(mapTerminal);
   if(existing instanceof NetworkDeviceBlockEntity device &&
      device.holoMode().equals("map"))be=device;
  }
  if(be==null){
   mapTerminal=null;mapSamples=java.util.List.of();
   long now=mc.level.getGameTime();
   if(lastDiscovery!=Long.MIN_VALUE&&now-lastDiscovery<20L)return;
   lastDiscovery=now;
   BlockPos player=mc.player.blockPosition();
   // Search ALL nearby block positions, not every fourth coordinate:
   // the previous stride-4 grid found only 1/64 of real terminals.
   find:for(int oy=-5;oy<=5;oy++)for(int ox=-9;ox<=9;ox++)
    for(int oz=-9;oz<=9;oz++){
     BlockPos candidate=player.offset(ox,oy,oz);
     if(!mc.level.hasChunkAt(candidate))continue;
     var value=mc.level.getBlockEntity(candidate);
     if(value instanceof NetworkDeviceBlockEntity device &&
        device.holoMode().equals("map")){
      mapTerminal=candidate;be=device;break find;
     }
    }
   if(be==null)return;
  }
  long now=mc.level.getGameTime();
  if(now!=lastSample&&
     (lastSample==Long.MIN_VALUE||now-lastSample>=10L)){
   lastSample=now;mapSamples=sampleMap(mc,mapTerminal,be);
  }
  for(MapVoxel v:mapSamples)draw(mc,ev,cam,v.state,v.x,v.y,v.z,.20D);
 }
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                     NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null)return out;
  int radius=be.holoRadius(),height=be.holoHeight();
  int low=Math.max(mc.level.getMinY(),t.getY()-height);
  int high=Math.min(mc.level.getMaxY()-1,t.getY()+height);
  int step=Math.max(1,(2*radius+1)/13);
  for(int dx=-radius;dx<=radius&&out.size()<160;dx+=step)
   for(int dz=-radius;dz<=radius&&out.size()<160;dz+=step){
    BlockPos sample=t.offset(dx,0,dz);
    if(!mc.level.hasChunkAt(sample))continue;
    for(int y=high;y>=low;y--){
     BlockPos at=new BlockPos(sample.getX(),y,sample.getZ());
     BlockState state=mc.level.getBlockState(at);
     if(state.isAir())continue;
     double px=t.getX()+.5+(double)dx/radius*be.holoWidth()/2D;
     double py=t.getY()+1.1+(double)(y-low)/Math.max(1,high-low)*be.holoHeight()*.15D;
     double pz=t.getZ()+.5+(double)dz/radius*be.holoDepth()/2D;
     out.add(new MapVoxel(state,px,py,pz));
     break;
    }
   }
  return out;
 }
}
''',encoding="utf-8")
print("V173_INGAME_VISUAL_FIXES_APPLIED: antenna occlusion, bounded portal assets, 242px GUI, 3-D ghost")
