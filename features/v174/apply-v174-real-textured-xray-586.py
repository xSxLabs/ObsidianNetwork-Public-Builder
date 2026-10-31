#!/usr/bin/env python3
"""B586: user explicitly wants REAL textured cable models through opaque walls,
not blue GUI edges. Render actual BlockState models via 26.1 SubmitCustomGeometry
in a depth-front projection with exactly equivalent screen-space geometry.
The old HUD wireframe remains absent; no server/gameplay FE changes.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/NetworkVisionClient.java"
s=p.read_text(encoding="utf-8")
assert "B581_VISION_SHARED_VERTICES" in s
assert "B579_VISION_CACHED_CONNECTIONS" in s
assert "V174_XRAY_WORLD_WIREFRAME_B469" in s
start=s.index(" @SubscribeEvent public static void hud(RenderGuiEvent.Post event){")
opening=s.index("{",start)
depth=0;end=None
for i in range(opening,len(s)):
 if s[i]=="{":depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:end=i+1;break
assert end is not None and "pipeAt(g,at,state" in s[start:end]
# NEVER draw overlay lines; this method is still a valid lightweight HUD
# subscriber but consumes no pixel rendering and no world scans.
s=s[:start]+''' // B586_NO_WIREFRAME: the HUD pass MUST NOT draw boxes or colored
 // pipe edges. Full actual block models are submitted in world geometry.
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  // The ON/OFF status and player energy requirement remain unchanged.
 }
'''+s[end:]
assert "pipeAt(g,at,state" not in s, "B586_LEGACY_CYAN_EDGES_NOT_REMOVED"
new=r'''
 // B586_TEXTURED_XRAY_REAL_BLOCK_MODEL: actual atlas textures, all six
 // connection arms from the Minecraft BlockState model, no wireframe drawing.
 //
 // Each cable vertex is transformed as P'=camera+t*(P-camera), where t
 // is positive and small enough to put its geometry IN FRONT of opaque
 // world walls. Perspective projection is unchanged: P' has identical
 // screen X,Y and appearance to P. Nothing changes in world data.
 // This avoids a costly second world render or per-pixel HUD rasterizer.
 private static final net.minecraft.client.renderer.block.BlockDisplayContext
    b586ModelContext=net.minecraft.client.renderer.block.BlockDisplayContext.create();
 @SubscribeEvent
 public static void xrayTextured(
    net.neoforged.neoforge.client.event.SubmitCustomGeometryEvent ev){
  if(!active())return;
  var mc=Minecraft.getInstance();
  if(mc.screen!=null||mc.level==null||mc.player==null)return;
  refreshXray(mc);
  if(xrayPositions.isEmpty())return;
  var camera=mc.gameRenderer.getMainCamera();
  var eye=camera.position();
  org.joml.Vector3f forward=new org.joml.Vector3f(0f,0f,-1f);
  camera.rotation().transform(forward);
  var pose=ev.getPoseStack();
  var collector=ev.getSubmitNodeCollector();
  // One model lookup per DISTINCT immutable block state this frame, not
  // per cable. Updated state is read live when cached topology changes.
  java.util.Map<net.minecraft.world.level.block.state.BlockState,
    net.minecraft.client.renderer.block.BlockModelRenderState> models=
      new java.util.IdentityHashMap<>();
  for(BlockPos at:xrayPositions){
   if(!mc.level.hasChunkAt(at))continue;
   var state=mc.level.getBlockState(at);
   if(xrayKind(state)==0)continue;
   double dx=at.getX()+.5-eye.x,dy=at.getY()+.5-eye.y,dz=at.getZ()+.5-eye.z;
   double facing=dx*forward.x()+dy*forward.y()+dz*forward.z();
   if(facing<=.2D)continue; // behind camera/near plane
   double centerDist=Math.sqrt(dx*dx+dy*dy+dz*dz);
   if(centerDist<.01D)continue;
   // 0.65 world units from camera = in front of opaque blocks, but
   // t*model size and t*distance have the same perspective ratio.
   double t=Math.min(1D,.65D/centerDist);
   var model=models.get(state);
   if(model==null){
    model=new net.minecraft.client.renderer.block.BlockModelRenderState();
    mc.getBlockModelResolver().update(model,state,b586ModelContext);
    models.put(state,model);
   }
   pose.pushPose();
   pose.translate((at.getX()-eye.x)*t,
                  (at.getY()-eye.y)*t,
                  (at.getZ()-eye.z)*t);
   pose.scale((float)t,(float)t,(float)t);
   model.submitWithZOffset(pose,collector,0x00f000f0,
      net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY,0);
   pose.popPose();
  }
 }
'''
idx=s.rfind("\n}")
assert idx>0
s=s[:idx]+new+s[idx:]
assert s.count("B586_TEXTURED_XRAY_REAL_BLOCK_MODEL")==1
assert "wireCube(g,at" not in s
assert "pipeAt(g,at,state" not in s
assert s.count("{")==s.count("}"),("B586_JAVA_BRACES",s.count("{"),s.count("}"))
p.write_text(s,encoding="utf-8")
print("B586_TEXTURED_ACTUAL_BLOCKSTATE_CABLES_THROUGH_WALLS_NO_HUD_BOXES_PASS")
