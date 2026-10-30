#!/usr/bin/env python3
"""B469: depth-independent world-aligned cable and importer/exporter outlines.

Replaces the V173 HUD rectangles with bounded projected 3D wireframes. All
geometry is sourced from actual loaded xSxLabs cable/IO block positions.
No modifications to world blockstates, ownership, inventories or server APIs.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"client/NetworkVisionClient.java"
s=p.read_text(encoding="utf-8")
assert "V173_B351_VISION_FEEDBACK" in s, "B469 expected B351 final action-wheel Vision"
assert "V173_VISION_FACADE_ONLY_328" in s, "B469 expected B328 projection"
needle=" private static boolean enabled;"
assert s.count(needle)==1, "B469 enabled state drift"
s=s.replace(needle,needle+'''
  // V174_XRAY_WORLD_WIREFRAME_B469: source positions only, never world mutation.
  private static final java.util.ArrayList<BlockPos> xrayPositions=new java.util.ArrayList<>();
  private static net.minecraft.client.multiplayer.ClientLevel scannedWorld;
  private static BlockPos scannedCenter;
  private static int scannedAt=-1000000;
''',1)
# B471: find the method's closing brace structurally. B337 condensed HUD
# into "hud(...){ }" without the old newline, and B470 failed on that format.
signature=" @SubscribeEvent public static void hud(RenderGuiEvent.Post event){"
assert s.count(signature)==1, "B471 HUD signature changed unexpectedly"
start=s.index(signature)
opening=s.index("{",start)
depth=0
end=None
for i in range(opening,len(s)):
 if s[i]=="{":
  depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:
   end=i+1
   break
assert end is not None and depth==0, "B471 HUD closing brace missing"
assert s[end:].strip().startswith("}"), "B471 final Java class closing brace missing"
replacement=r''' // Only own mod blocks are eligible. No terrain, machines or other mod IDs.
 private static int xrayKind(net.minecraft.world.level.block.state.BlockState state) {
  var key=BuiltInRegistries.BLOCK.getKey(state.getBlock());
  if(!"obsidiannetwork".equals(key.getNamespace()))return 0;
  String name=key.getPath();
  if(name.equals("conduit_bundle")||name.endsWith("_cable"))return 1;
  if(name.equals("importer")||name.endsWith("_importer"))return 2;
  if(name.equals("exporter")||name.endsWith("_exporter"))return 3;
  return 0;
 }
 // Never search missing chunks, never force-load, and amortize world reads.
 private static void refreshXray(Minecraft mc) {
  if(mc.level==null||mc.player==null){xrayPositions.clear();scannedWorld=null;return;}
  BlockPos center=mc.player.blockPosition();
  boolean moved=scannedCenter==null||scannedCenter.distSqr(center)>9;
  if(scannedWorld==mc.level&&!moved&&mc.player.tickCount-scannedAt<8)return;
  scannedWorld=mc.level;scannedCenter=center;scannedAt=mc.player.tickCount;
  xrayPositions.clear();
  // Hard ceilings: 25x17x25 probes at most every 8 game ticks; 160 outlines.
  for(int y=-8;y<=8;y++)for(int x=-12;x<=12;x++)for(int z=-12;z<=12;z++){
   if(xrayPositions.size()>=160)return;
   if(x*x+z*z>144)continue;
   BlockPos at=center.offset(x,y,z);
   if(!mc.level.hasChunkAt(at))continue;
   if(xrayKind(mc.level.getBlockState(at))!=0)xrayPositions.add(at.immutable());
  }
 }
 // Project loaded world-space geometry through camera rotation; independent
 // of the world's depth buffer because this runs after scene rendering.
 private static float[] project(float wx,float wy,float wz,
  net.minecraft.world.phys.Vec3 origin,Quaternionf inv,
  double focal,int width,int height){
  Vector3f local=new Vector3f((float)(wx-origin.x),(float)(wy-origin.y),
                               (float)(wz-origin.z));
  inv.transform(local);
  if(local.z>=-.12F)return null;
  float sx=(float)(width*.5D+local.x*focal/-local.z);
  float sy=(float)(height*.5D-local.y*focal/-local.z);
  if(!Float.isFinite(sx)||!Float.isFinite(sy))return null;
  return new float[]{sx,sy};
 }
 private static void wireLine(net.minecraft.client.gui.GuiGraphicsExtractor g,
    float[] a,float[] b,int color,int width,int height){
  if(a==null||b==null)return;
  // Entire offscreen segments do not need rasterization.
  if(Math.max(a[0],b[0])<0||Math.min(a[0],b[0])>=width
     ||Math.max(a[1],b[1])<0||Math.min(a[1],b[1])>=height)return;
  float dx=b[0]-a[0],dy=b[1]-a[1];
  int steps=Math.min(256,Math.max(1,(int)Math.ceil(Math.max(Math.abs(dx),Math.abs(dy)))));
  for(int i=0;i<=steps;i++){
   int px=Math.round(a[0]+dx*i/steps),py=Math.round(a[1]+dy*i/steps);
   if(px>=0&&px<width&&py>=0&&py<height)g.fill(px,py,px+1,py+1,color);
  }
 }
 private static void wireCube(net.minecraft.client.gui.GuiGraphicsExtractor g,
    BlockPos p,float half,int color,
    net.minecraft.world.phys.Vec3 origin,Quaternionf inv,
    double focal,int width,int height){
  float[][] points=new float[8][];
  for(int i=0;i<8;i++){
   float x=p.getX()+.5F+((i&1)==0?-half:half);
   float y=p.getY()+.5F+((i&2)==0?-half:half);
   float z=p.getZ()+.5F+((i&4)==0?-half:half);
   points[i]=project(x,y,z,origin,inv,focal,width,height);
  }
  for(int i=0;i<8;i++)for(int axis=0;axis<3;axis++){
   int other=i^(1<<axis);
   if(i<other)wireLine(g,points[i],points[other],color,width,height);
  }
 }
 // V174_XRAY_WORLD_WIREFRAME_B469: show only actual xSxLabs cables and
 // importer/exporter nodes, even if hidden by opaque terrain or facades.
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  if(!active())return;
  var mc=Minecraft.getInstance();
  if(mc.screen!=null||mc.level==null||mc.player==null)return;
  refreshXray(mc);
  var camera=mc.gameRenderer.getMainCamera();
  var origin=camera.position();
  var inverse=new Quaternionf(camera.rotation()).conjugate();
  var g=event.getGuiGraphics();
  int width=mc.getWindow().getGuiScaledWidth();
  int height=mc.getWindow().getGuiScaledHeight();
  double fov=Math.max(35D,Math.min(110D,camera.getFov()));
  double focal=height/(2D*Math.tan(Math.toRadians(fov/2D)));
  for(BlockPos at:xrayPositions){
   // Block may change between scans, so revalidate each projected element.
   if(!mc.level.hasChunkAt(at))continue;
   var state=mc.level.getBlockState(at);
   int kind=xrayKind(state);
   if(kind==0)continue;
   int color=kind==1?0xff38ddff:kind==2?0xff4effb0:0xffffbb54;
   float half=kind==1?.21F:.32F;
   wireCube(g,at,half,color,origin,inverse,focal,width,height);
  }
 }
'''
# Keep closing class brace, replace HUD block and any internal code with helper methods.
s=s[:start]+replacement+s[end:]
assert s.count("V174_XRAY_WORLD_WIREFRAME_B469")>=2
assert "if(cable&&(" not in s, "facade-only restriction unexpectedly survived"
assert "xrayPositions.size()>=160" in s and "mc.level.hasChunkAt(at)" in s
assert "wireCube(g,at" in s and "getGuiGraphics()" in s
assert s.count("{")==s.count("}"), "B470 Java braces unbalanced after Vision HUD replacement"
p.write_text(s,encoding="utf-8")
print("V174_XRAY_WORLD_WIREFRAME_B469 PASS: bounded loaded-only 3D outlines through terrain, action wheel only")
