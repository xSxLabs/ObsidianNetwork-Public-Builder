#!/usr/bin/env python3
"""v1.7.3 Build306: true 2x3 portal graphics, denser volumetric 3D Maps-like
holograms, single-line CUSTOM height scaling, zero-linger blueprint ghosts.
Only affects v1.7.3 reconstructed source. No world saves or FE changes.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(relative,old,new):
 p=J/relative;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("VISUAL306_DRIFT",relative,s.count(old),old[:90])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def replace_section(relative,begin,end,contents):
 p=J/relative;s=p.read_text(encoding="utf-8")
 assert s.count(begin)==1 and s.count(end)==1,("VISUAL306_SECTION_DRIFT",relative,begin[:70])
 a=s.index(begin);b=s.index(end,a)
 p.write_text(s[:a]+contents+s[b:],encoding="utf-8")

# The old particle emitter continued leaving BLOCK_MARKER and blue dust behind
# for their lifetime after the held blueprint changed. Only the per-frame
# geometry renderer should draw any placement ghost.
edit("client/NetworkBlueprintPreviewClient.java",
     " private NetworkBlueprintPreviewClient(){}",
     """ private NetworkBlueprintPreviewClient(){}
 // Legacy particles are disabled; a frame-bound geometric ghost has no
 // leftover particles when the held Blueprint changes or the GUI opens.
 private static boolean particleGhostEnabled(){return false;}""")
edit("client/NetworkBlueprintPreviewClient.java",
     "if(mc.player==null||mc.level==null||mc.player.level()!=mc.level||",
     "if(!particleGhostEnabled()||mc.player==null||mc.level==null||mc.player.level()!=mc.level||")

renderer="client/V173WorldGhostRenderer.java"
# Render every live 2x3 aperture in the world, not only a 1x1 model block.
edit(renderer,
     """  map(mc,ev,camera);
 }""",
     """  map(mc,ev,camera);
  portals(mc,ev,camera);
 }""")
# Existing draw() handles scalar scaling; per-axis scaling allows a continuous
# miniature without artificial gaps between columns or floors.
edit(renderer,
     """ private static void blueprint(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam,""",
     """ private static void drawSized(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 camera,
                               BlockState state,double x,double y,double z,
                               double sx,double sy,double sz){
  PoseStack pose=ev.getPoseStack();
  pose.pushPose();
  pose.translate(x-camera.x,y-camera.y,z-camera.z);
  pose.scale((float)sx,(float)sy,(float)sz);
  BlockModelRenderState model=new BlockModelRenderState();
  mc.getBlockModelResolver().update(model,state,CONTEXT);
  model.submitWithZOffset(pose,ev.getSubmitNodeCollector(),FULL_BRIGHT,
       OverlayTexture.NO_OVERLAY,0);
  pose.popPose();
 }
 private static void blueprint(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam,""")

# Replace the single topmost floating-block point cloud with compact 3D voxels
# (solid exposed surfaces, side walls and internal cave faces); sample only
# loaded chunks, use a hard budget of 2200 and cached samples per 10 ticks.
start=' private record MapVoxel(BlockState state,double x,double y,double z){}'
end="\n}\n"
p=J/renderer
s=p.read_text(encoding="utf-8")
assert s.count(start)==1
a=s.index(start)
b=s.rfind(end)
assert b>a
new=r''' private record MapVoxel(BlockState state,double x,double y,double z,
                              double sx,double sy,double sz){}
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
  if(lastSample==Long.MIN_VALUE||now-lastSample>=10L){
   lastSample=now;mapSamples=sampleMap(mc,mapTerminal,be);
  }
  for(MapVoxel voxel:mapSamples)
   drawSized(mc,ev,cam,voxel.state(),voxel.x(),voxel.y(),voxel.z(),
          voxel.sx(),voxel.sy(),voxel.sz());
 }
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                     NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null)return out;
  int radius=be.holoRadius();
  int halfHeight=be.holoHeight();
  int low=Math.max(mc.level.getMinY(),t.getY()-halfHeight);
  int high=Math.min(mc.level.getMaxY()-1,t.getY()+halfHeight);
  int side=radius*2+1;
  int step=Math.max(1,(side+27)/28);
  int vertical=Math.max(1,(high-low+1+23)/24);
  double scaleX=(double)be.holoWidth()/side;
  double scaleZ=(double)be.holoDepth()/side;
  double scaleY=(double)be.holoHeight()/(high-low+1);
  // Uniform grid spacing along each axis: unlike the old .20-size blocks,
  // neighboring voxels touch and form mountains, slopes, forests and buildings.
  for(int dx=-radius;dx<=radius&&out.size()<2200;dx+=step)
   for(int dz=-radius;dz<=radius&&out.size()<2200;dz+=step){
    BlockPos base=t.offset(dx,0,dz);
    if(!mc.level.hasChunkAt(base))continue;
    for(int y=low;y<=high&&out.size()<2200;y+=vertical){
     BlockPos at=new BlockPos(base.getX(),y,base.getZ());
     BlockState state=mc.level.getBlockState(at);
     if(state.isAir())continue;
     // Only expose real visible surfaces: this includes undercuts, cave walls
     // and exposed vertical faces, not only the topmost terrain block.
     if(!mc.level.getBlockState(at.above()).isAir() &&
        !mc.level.getBlockState(at.below()).isAir() &&
        !mc.level.getBlockState(at.north()).isAir() &&
        !mc.level.getBlockState(at.south()).isAir() &&
        !mc.level.getBlockState(at.east()).isAir() &&
        !mc.level.getBlockState(at.west()).isAir())continue;
     double px=t.getX()+.5-be.holoWidth()/2D+(dx+radius)*scaleX;
     double py=t.getY()+1.15+(y-low)*scaleY;
     double pz=t.getZ()+.5-be.holoDepth()/2D+(dz+radius)*scaleZ;
     out.add(new MapVoxel(state,px,py,pz,step*scaleX,vertical*scaleY,step*scaleZ));
    }
   }
  return out;
 }

 private static net.minecraft.client.multiplayer.ClientLevel portalWorld;
 private static long lastPortalScan=Long.MIN_VALUE;
 private static java.util.List<BlockPos> portalPositions=java.util.List.of();
 private static void portals(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam){
  long now=mc.level.getGameTime();
  if(portalWorld!=mc.level){
   portalWorld=mc.level;portalPositions=java.util.List.of();
   lastPortalScan=Long.MIN_VALUE;
  }
  if(lastPortalScan==Long.MIN_VALUE||now-lastPortalScan>=20L){
   lastPortalScan=now;
   java.util.ArrayList<BlockPos> found=new java.util.ArrayList<>();
   BlockPos player=mc.player.blockPosition();
   search:for(int dy=-7;dy<=7;dy++)for(int dx=-12;dx<=12;dx++)
    for(int dz=-12;dz<=12;dz++){
     BlockPos at=player.offset(dx,dy,dz);
     if(!mc.level.hasChunkAt(at))continue;
     BlockState state=mc.level.getBlockState(at);
     if(state.is(ObsidianNetwork.NETWORK_PORTAL_A.get())||
        state.is(ObsidianNetwork.NETWORK_PORTAL_B.get())){
      found.add(at);
      if(found.size()>=24)break search;
     }
    }
   portalPositions=found;
  }
  BlockState frame=Blocks.OBSIDIAN.defaultBlockState();
  for(BlockPos at:portalPositions){
   if(!mc.level.hasChunkAt(at))continue;
   BlockState physical=mc.level.getBlockState(at);
   boolean a=physical.is(ObsidianNetwork.NETWORK_PORTAL_A.get());
   boolean b=physical.is(ObsidianNetwork.NETWORK_PORTAL_B.get());
   if(!a&&!b)continue;
   // Visual aperture is precisely 2 blocks wide and 3 high; the underlying
   // portal anchor stays a single block for old-world compatibility.
   double x=at.getX()-.5,y=at.getY(),z=at.getZ()+.42;
   for(int i=0;i<3;i++){
    drawSized(mc,ev,cam,frame,x,y+i,z,.25,1,.16);
    drawSized(mc,ev,cam,frame,x+1.75,y+i,z,.25,1,.16);
   }
   for(int i=0;i<2;i++){
    drawSized(mc,ev,cam,frame,x+i,y,z,1,.25,.16);
    drawSized(mc,ev,cam,frame,x+i,y+2.75,z,1,.25,.16);
   }
   BlockState glass=(a?Blocks.PURPLE_STAINED_GLASS:Blocks.LIGHT_BLUE_STAINED_GLASS).defaultBlockState();
   // Transparent 2x3 inner membrane, with real textures (not missing JSON).
   for(int ix=0;ix<2;ix++)for(int iy=0;iy<3;iy++)
    drawSized(mc,ev,cam,glass,x+.25+ix*.75,y+.25+iy*(2.5/3D),
               z+.055,.75,2.5/3D,.055);
  }
 }
'''
s=s[:a]+new+s[b:]
p.write_text(s,encoding="utf-8")

# Correct the single-line CUSTOM bug: its original vertical spacing only
# affected lines 2..12. Use persistent TextDisplay entities with a real
# transform scale set directly from the HEIGHT field.
be="blockentity/NetworkDeviceBlockEntity.java"
p=J/be;s=p.read_text(encoding="utf-8")
tag=' private void hologram(ServerLevel world){'
assert s.count(tag)==1
s=s.replace(tag,tag+'''
  // TextDisplays are persistent holograms, no short-lived particle labels.
  var textEntities=world.getEntitiesOfClass(
      net.minecraft.world.entity.Display.TextDisplay.class,
      new AABB(worldPosition).inflate(4,40,4),
      e->e.entityTags().contains(labelTag()));
''',1)
assert s.count('   for(ArmorStand stand:old)stand.discard();')==1
s=s.replace('   for(ArmorStand stand:old)stand.discard();',
            '   for(ArmorStand stand:old)stand.discard();\n   for(var text:textEntities)text.discard();',1)
st='  String message="network".equals(holoMode)?summary(world):holoText;'
en='  world.sendParticles(new DustParticleOptions(holoColor,.6f),'
assert s.count(st)==1 and s.count(en)==1
start=s.index(st);end=s.index(en,start)
textCode=r'''  // All legacy ArmorStand text is retired once; no duplicate overlays.
  for(ArmorStand stand:old)stand.discard();
  String message="network".equals(holoMode)?summary(world):holoText;
  String[] lines=message.split("\n",-1);
  int shown=Math.min(12,lines.length);
  java.util.Map<String,net.minecraft.world.entity.Display.TextDisplay> current=new java.util.HashMap<>();
  for(var entity:textEntities){
   for(String tag:entity.entityTags())
    if(tag.startsWith(labelTag()+"#")){current.put(tag,entity);break;}
  }
  float scale=Math.max(.25F,Math.min(8F,holoHeight/3F));
  for(int i=0;i<shown;i++){
   String tag=labelTag()+"#"+i;
   var entity=current.remove(tag);
   double y=worldPosition.getY()+1.55+(shown-1-i)*.24*scale;
   if(entity==null){
    entity=new net.minecraft.world.entity.Display.TextDisplay(
      net.minecraft.world.entity.EntityType.TEXT_DISPLAY,world);
    entity.addTag(labelTag());entity.addTag(tag);
    world.addFreshEntity(entity);
   }
   entity.setPos(worldPosition.getX()+.5,y,worldPosition.getZ()+.5);
   String line=lines[i];
   if(line.length()>180)line=line.substring(0,180);
   entity.setText(Component.literal(line).withStyle(sty->sty.withColor(holoColor)));
   entity.setBillboardConstraints(net.minecraft.world.entity.Display.BillboardConstraints.CENTER);
   entity.setTransformation(new com.mojang.math.Transformation(
        new org.joml.Vector3f(0F,0F,0F),new org.joml.Quaternionf(),
        new org.joml.Vector3f(scale,scale,scale),new org.joml.Quaternionf()));
  }
  for(var stale:current.values())stale.discard();
  setStatus("network".equals(holoMode)?message:"CUSTOM "+shown+" lines HEIGHT "+holoHeight);
'''
s=s[:start]+textCode+s[end:]
p.write_text(s,encoding="utf-8")
assert "HEIGHT "+ '" +holoHeight' not in s
print("V173_3DMAPS_CUSTOM_PORTAL_BLUEPRINT_306_PASS")
