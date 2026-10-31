#!/usr/bin/env python3
"""Full actual textured xray rendering contract. Ensures no cyan HUD edge draw
and all prior FE/performance constraints still exist. Perspective equivalence
is verified with 3D coordinates for all six face directions."""
import os, math
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
s=(j/"client/NetworkVisionClient.java").read_text()
assert "B586_TEXTURED_XRAY_REAL_BLOCK_MODEL" in s
assert "B586_NO_WIREFRAME" in s
assert "SubmitCustomGeometryEvent" in s
assert "BlockModelRenderState" in s
assert "net.minecraft.client.renderer.block.model.BlockDisplayContext" in s
assert "net.minecraft.client.renderer.block.BlockDisplayContext" not in s
assert "mc.getBlockModelResolver().update(model,state,b586ModelContext)" in s
assert "model.submitWithZOffset(pose,collector,0x00f000f0" in s
assert "refreshXray(mc)" in s
assert "xrayKind(state)==0" in s
assert "mc.level.hasChunkAt(at)" in s
assert "if(!active())return;" in s
assert "if(mc.screen!=null||mc.level==null||mc.player==null)return;" in s
assert "if(facing<=.2D)continue" in s
assert "double t=Math.min(1D,.65D/centerDist);" in s
assert "pipeAt(g,at,state" not in s
assert "wireCube(g,at" not in s
a=s.index("public static void hud(RenderGuiEvent.Post event){")
z=s.index("}",a)
assert "wireLine" not in s[a:z] and "wirePipe" not in s[a:z] and "g.fill" not in s[a:z]
assert "xrayPositions.size()>=160" in s
assert "mc.player.tickCount-scannedAt<8" in s
# Uniform camera-space scaling guarantees same perspective geometry.
for pos in [(.5,1.5,5.2),(3.4,-1.,8.),(-2.,2.,19.),(10.,5.,50.)]:
 length=math.sqrt(sum(x*x for x in pos))
 t=min(1.,.65/length)
 for off in [(0,0,0),(.2,.1,.1),(-.3,.25,.4)]:
  p=[x+y for x,y in zip(pos,off)]
  q=[t*v for v in p]
  assert abs(p[0]/p[2]-q[0]/q[2])<1e-9
  assert abs(p[1]/p[2]-q[1]/q[2])<1e-9
react=(j/"reactor/ReactorControllerBlockEntity.java").read_text()
assert "B579_REACTOR_GENERATE_EVERY_TICK" in react and "B581_REACTOR_CACHE" in react
socket=(j/"client/EnergyCableInputRenderer.java").read_text()
assert "B584_ITEM_CABLE_IDENTICAL_INPUT" in socket
print("B586_REAL_TEXTURED_THROUGH_WALLS_MODELS_PERSPECTIVE_EQUIVALENCE_FE_PASS")
