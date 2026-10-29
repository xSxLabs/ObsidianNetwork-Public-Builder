#!/usr/bin/env python3
"""Build337: restore real server hologram text, reveal true cable geometry,
and incorporate Vision into a circular five-sector action wheel.
Runs after Build328 on v1.7.3 only. Rendering-only changes; no network IO,
world blockstate mutation, save-format change, or FE transport modifications.
"""
from pathlib import Path
import os,re
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel,old,new,expected=1):
    file=J/rel
    src=file.read_text(encoding="utf-8")
    assert src.count(old)==expected,("V173_B337_DRIFT",rel,src.count(old),old[:90])
    file.write_text(src.replace(old,new),encoding="utf-8")

# Re-enable authoritative TextDisplay entities for Network/Custom modes.
# The Build328 change returned early for ALL modes, silently discarding the
# previously functioning server-side displays. Keep MAP client volume mode.
edit("blockentity/NetworkDeviceBlockEntity.java",
 'if("map".equals(holoMode)||"network".equals(holoMode)||"custom".equals(holoMode)){',
 'if("map".equals(holoMode)){')
# Actual TextDisplay code already exists beneath this guard, including
# persisted text/height, removal, billboard, and the 26.1 access transformers.
machine=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
assert 'entity.setText(Component.literal(line)' in machine
assert 'entity.setBillboardConstraints(' in machine
assert 'world.addFreshEntity(entity);' in machine

# Network Vision was drawing labeled HUD rectangles rather than the models.
# The actual base cable render remains in the world. Hide only the model of
# a fitted camouflage facade, never alter stored facade data or game blockstates.
edit("client/render/CableFacadeRenderer.java",
 'state.facade = blockEntity.facadeState();',
 'state.facade = dev.obsidiannetwork.client.NetworkVisionClient.active() ? '
 'net.minecraft.world.level.block.Blocks.AIR.defaultBlockState() : blockEntity.facadeState();')
# Conduit bundles have their own facade renderer. Keep its geometry/collars:
# suppress ONLY the facade submission when this renderer's facade is present.
bundle=J/"client/render/ConduitBundleRenderer.java"
assert bundle.exists(),("V173_B337_BUNDLE_RENDERER_MISSING",bundle)
s=bundle.read_text(encoding="utf-8")
n=0
for token in ("!state.facade.isAir()","!s.facade.isAir()","!facade.isAir()"):
    if token in s:
        s=s.replace(token, "(!dev.obsidiannetwork.client.NetworkVisionClient.active() && "+token+")")
        n+=1
if n:
    bundle.write_text(s,encoding="utf-8")
print("V173_B337_BUNDLE_FACADE_GUARDS",n)

# Delete the screen-space markers completely. The player sees the real cable
# model and genuine Importer/Exporter block geometry, not CABLE text/boxes.
vision=J/"client/NetworkVisionClient.java"
s=vision.read_text(encoding="utf-8")
start=s.index(" @SubscribeEvent public static void hud(RenderGuiEvent.Post event){")
brace=s.index("{",start)
depth=0;end=None
for i in range(brace,len(s)):
    if s[i]=="{":depth+=1
    elif s[i]=="}":
        depth-=1
        if depth==0:
            end=i+1;break
assert end is not None and 'g.text(mc.font,label' in s[start:end]
s=s[:start]+''' // V173_B337_REAL_BLOCKS: no HUD text, rectangles, or fabricated cubes.
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){}
'''+s[end:]
vision.write_text(s,encoding="utf-8")

# Round action wheel: the fifth slice shares the circle with the original
# four. With no Vision card, the exact four-sector wheel is preserved.
wheel=J/"client/NetworkActionWheelClient.java"
s=wheel.read_text(encoding="utf-8")
old='''  selected=NetworkVisionClient.installed()&&dx>=46&&dx<=110&&dy>=53&&dy<=92?4:
    distance<27||distance>108?-1:
    (Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0));'''
new='''  selected=distance<27||distance>108?-1:
    wheelSector(dx,dy,NetworkVisionClient.installed());'''
assert s.count(old)==1,("B337_WHEEL_SELECTION_DRIFT",s.count(old))
s=s.replace(old,new,1)
register=" @SubscribeEvent public static void register(RegisterKeyMappingsEvent e)"
assert s.count(register)==1
s=s.replace(register,''' // Five equal radial slices, clockwise from the upper sector:
 // EXIT, PORTAL B, VISION, RECALL, PORTAL A.
 private static int wheelSector(int dx,int dy,boolean vision){
  if(!vision)return Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0);
  double angle=Math.atan2(dy,dx)+Math.PI/2D;
  if(angle<0)angle+=Math.PI*2D;
  int slice=(int)Math.floor((angle+Math.PI/5D)/(Math.PI*2D/5D))%5;
  return switch(slice){case 0->0;case 1->1;case 2->4;case 3->2;default->3;};
 }
'''+register,1)
start=s.index('  for(int dy=-105;dy<=105;dy+=7)')
end=s.index('  g.fill(x-25,y-25,x+25,y+25',start)
s=s[:start]+'''  // B337_CIRCULAR_FIVE_WEDGE: every submitted pixel stays inside r=104.
  boolean hasVision=NetworkVisionClient.installed();
  for(int yy=-103;yy<=103;yy+=2)for(int xx=-103;xx<=103;xx+=2){
   int radius2=xx*xx+yy*yy;
   if(radius2<28*28||radius2>103*103)continue;
   int wedge=wheelSector(xx,yy,hasVision);
   int color=wedge==selected?0xf12ad5e9:0xe21f344b;
   g.fill(x+xx,y+yy,x+xx+2,y+yy+2,color);
  }
'''+s[end:]
start=s.index('  if(NetworkVisionClient.installed()){',s.index('  g.text(mc.font,"xSxLabs"'))
# The old rectangle was the only conditional after center text.
brace=s.index('{',start);depth=0;end=None
for i in range(brace,len(s)):
    if s[i]=='{':depth+=1
    elif s[i]=='}':
        depth-=1
        if depth==0:end=i+1;break
assert end is not None and 'g.fill(x+46,y+53,x+110,y+92,shade);' in s[start:end]
s=s[:start]+'''  if(hasVision){
   int ink=selected==4?0xffffffff:0xffbde8ee;
   // Both words are INSIDE the bottom-right radial wedge.
   g.text(mc.font,"VISION",x+58-mc.font.width("VISION")/2,y+48,ink);
   String state=NetworkVisionClient.active()?"ON":"OFF";
   g.text(mc.font,state,x+58-mc.font.width(state)/2,y+62,
          NetworkVisionClient.active()?0xff62ffbe:ink);
  }'''+s[end:]
wheel.write_text(s,encoding="utf-8")

assert "B337_CIRCULAR_FIVE_WEDGE" in wheel.read_text()
assert "B337_REAL_BLOCKS" in vision.read_text()
assert 'if("map".equals(holoMode)){' in machine
print("V173_B337_WORLD_VISION_SERVER_HOLO_CIRCULAR_WHEEL_PASS")
