#!/usr/bin/env python3
"""B451: bounded world-aligned, through-wall NETWORK Vision overlay.

Runs after the v1.7.3 Vision / action-wheel patches and AFTER B445 guidebook.
Only renders client GUI geometry. No world writes, packets, server topology,
facade blockstate mutation, chunk loads or upgrade bypasses. This is a
first-pass local-component visual implementation: multiplayer ownership
authorisation still needs a dedicated server-authenticated visibility feed.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/NetworkVisionClient.java"
s=p.read_text(encoding="utf-8")
old=" @SubscribeEvent public static void hud(RenderGuiEvent.Post event){}"
assert s.count(old)==1,("B451_VISION_ANCHOR_DRIFT",s.count(old))
new=r''' // B451_VISION_THROUGH_WALL: draw projected outlines in screen space AFTER
 // world depth tests. The corners come from real NETWORK/IO voxel shapes.
 // No text labels, screen-space fake blocks, generic X-ray, or block mutations.
 private record ShapeNode(BlockPos pos,net.minecraft.world.phys.AABB bounds,int tint){}
 private static net.minecraft.client.multiplayer.ClientLevel visionWorld;
 private static BlockPos visionCenter;
 private static long visionSampleTick=Long.MIN_VALUE;
 private static java.util.List<ShapeNode> visionShapes=java.util.List.of();

 private static boolean networkWire(Minecraft mc,BlockPos at){
  if(!mc.level.hasChunkAt(at))return false; // never load chunks
  var st=mc.level.getBlockState(at);
  if(st.is(dev.obsidiannetwork.ObsidianNetwork.NETWORK_CABLE.get()))return true;
  return st.is(dev.obsidiannetwork.ObsidianNetwork.CONDUIT_BUNDLE.get())
   &&mc.level.getBlockEntity(at) instanceof
      dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity be
   &&be.has(dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.NETWORK);
 }
 private static int ioColor(Minecraft mc,BlockPos at){
  if(!mc.level.hasChunkAt(at))return 0;
  var id=BuiltInRegistries.BLOCK.getKey(mc.level.getBlockState(at).getBlock());
  // Strictly OWN MOD's importer/exporter IDs, not other mods or machines.
  if(!"obsidiannetwork".equals(id.getNamespace()))return 0;
  String name=id.getPath();
  if("importer".equals(name)||name.endsWith("_importer"))return 0xff49e9ac;
  if("exporter".equals(name)||name.endsWith("_exporter"))return 0xffffbd59;
  return 0;
 }
 private static boolean near(BlockPos origin,BlockPos at){
  return Math.abs((long)origin.getX()-at.getX())<=9L
    &&Math.abs((long)origin.getY()-at.getY())<=6L
    &&Math.abs((long)origin.getZ()-at.getZ())<=9L;
 }
 private static void addShape(Minecraft mc,BlockPos at,int color,
                              java.util.List<ShapeNode> out){
  var state=mc.level.getBlockState(at);
  // Remove the facade flag ONLY from the local, temporary render shape.
  // Existing facade items and world blockstates are completely untouched.
  var property=state.getBlock().getStateDefinition().getProperty("facaded");
  if(property instanceof net.minecraft.world.level.block.state.properties.BooleanProperty flag)
   state=state.setValue(flag,false);
  var shape=state.getShape(mc.level,at);
  if(shape.isEmpty())return;
  out.add(new ShapeNode(at,shape.bounds(),color));
 }
 private static void sampleVision(Minecraft mc){
  BlockPos center=mc.player.blockPosition();
  long now=mc.level.getGameTime();
  if(visionWorld==mc.level&&visionCenter!=null&&
     now>=visionSampleTick&&now-visionSampleTick<8L&&
     Math.abs(center.getX()-visionCenter.getX())<3&&
     Math.abs(center.getY()-visionCenter.getY())<3&&
     Math.abs(center.getZ()-visionCenter.getZ())<3)return;
  visionWorld=mc.level;visionCenter=center;visionSampleTick=now;
  // Choose one local, physically connected NETWORK component. A real
  // server-authorised owner graph is still required for multiplayer privacy.
  BlockPos root=null;int best=Integer.MAX_VALUE;
  for(int y=-5;y<=5;y++)for(int x=-7;x<=7;x++)for(int z=-7;z<=7;z++){
   BlockPos at=center.offset(x,y,z);
   if(!mc.level.hasChunkAt(at))continue;
   int dist=x*x+y*y+z*z;
   if(dist>=best)continue;
   if(networkWire(mc,at)){root=at;best=dist;}
  }
  if(root==null){visionShapes=java.util.List.of();return;}
  java.util.ArrayDeque<BlockPos> todo=new java.util.ArrayDeque<>();
  java.util.HashSet<BlockPos> seen=new java.util.HashSet<>();
  java.util.HashSet<BlockPos> shown=new java.util.HashSet<>();
  java.util.ArrayList<ShapeNode> found=new java.util.ArrayList<>();
  todo.add(root);seen.add(root);
  while(!todo.isEmpty()&&found.size()<64){
   BlockPos at=todo.removeFirst();
   if(!mc.level.hasChunkAt(at)||!networkWire(mc,at))continue;
   if(shown.add(at))addShape(mc,at,0xff45e3ff,found);
   for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()){
    BlockPos next=at.relative(d);
    if(!near(center,next)||!mc.level.hasChunkAt(next))continue;
    if(networkWire(mc,next)){
     if(seen.size()<256&&seen.add(next))todo.addLast(next);
    }else if(shown.add(next)&&found.size()<64){
     int io=ioColor(mc,next);
     if(io!=0)addShape(mc,next,io,found);
    }
   }
  }
  visionShapes=java.util.List.copyOf(found);
 }
 private static int[] project(Quaternionf inverse,
     net.minecraft.world.phys.Vec3 eye,double x,double y,double z,
     int width,int height,double focal){
  Vector3f local=new Vector3f((float)(x-eye.x),
                              (float)(y-eye.y),(float)(z-eye.z));
  inverse.transform(local);
  if(local.z>=-.12F)return null;
  double sx=width*.5D+local.x*focal/-local.z;
  double sy=height*.5D-local.y*focal/-local.z;
  if(!Double.isFinite(sx)||!Double.isFinite(sy)||
     Math.abs(sx)>width*3D||Math.abs(sy)>height*3D)return null;
  return new int[]{(int)Math.round(sx),(int)Math.round(sy)};
 }
 private static void wireLine(net.minecraft.client.gui.GuiGraphicsExtractor g,
      int[] a,int[] b,int width,int height,int color){
  if(a==null||b==null)return;
  int dx=b[0]-a[0],dy=b[1]-a[1];
  // Sample every 2 screen pixels, at most 24 plots per actual voxel edge.
  // Bounded cost per frame even at extreme camera proximity.
  int count=Math.min(24,Math.max(1,(Math.max(Math.abs(dx),Math.abs(dy))+1)/2));
  for(int i=0;i<=count;i++){
   int x=a[0]+dx*i/count,y=a[1]+dy*i/count;
   if(x>=0&&x<width&&y>=0&&y<height)g.fill(x,y,x+2,y+2,color);
  }
 }
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  if(!active()){visionShapes=java.util.List.of();visionSampleTick=Long.MIN_VALUE;return;}
  var mc=Minecraft.getInstance();
  if(mc.player==null||mc.level==null||mc.screen!=null)return;
  sampleVision(mc);
  if(visionShapes.isEmpty())return;
  var camera=mc.gameRenderer.getMainCamera();
  var eye=camera.position();
  Quaternionf inverse=new Quaternionf(camera.rotation()).conjugate();
  int w=mc.getWindow().getGuiScaledWidth(),h=mc.getWindow().getGuiScaledHeight();
  double fov=Math.max(35D,Math.min(110D,camera.getFov()));
  double focal=h/(2D*Math.tan(Math.toRadians(fov/2D)));
  var g=event.getGuiGraphics();
  for(ShapeNode node:visionShapes){
   var box=node.bounds();
   // Each actual voxel-shape bound becomes a world-aligned 3D wireframe.
   int[][] corner=new int[8][];
   for(int i=0;i<8;i++){
    double x=node.pos().getX()+((i&1)==0?box.minX:box.maxX);
    double y=node.pos().getY()+((i&2)==0?box.minY:box.maxY);
    double z=node.pos().getZ()+((i&4)==0?box.minZ:box.maxZ);
    corner[i]=project(inverse,eye,x,y,z,w,h,focal);
   }
   for(int i=0;i<8;i++)for(int mask:new int[]{1,2,4})
    if((i&mask)==0)wireLine(g,corner[i],corner[i|mask],w,h,node.tint());
  }
 }'''
s=s.replace(old,new,1)
assert "B451_VISION_THROUGH_WALL" in s
assert "public static boolean active()" in s
assert "V173_B351_VISION_FEEDBACK" in s
assert "setBlockAndUpdate(" not in new
p.write_text(s,encoding="utf-8")
print("V174_VISION_XRAY_451_PASS: bounded connected NETWORK/IO voxel wireframe HUD")
