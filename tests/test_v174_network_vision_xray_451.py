#!/usr/bin/env python3
"""B451 regression: visual-only, bounded, depth-independent network shape projection."""
import ast
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/"features/v174/apply-network-vision-xray-451.py").read_text()
workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(script)
assert "B451_VISION_THROUGH_WALL" in script
for marker in (
 "mc.level.hasChunkAt(", "dev.obsidiannetwork.ObsidianNetwork.NETWORK_CABLE.get()",
 "dev.obsidiannetwork.ObsidianNetwork.CONDUIT_BUNDLE.get()",
 "ConduitBundleBlockEntity.Layer.NETWORK", "networkWire(mc,next)",
 'if(!"obsidiannetwork".equals(id.getNamespace()))return 0;',
 '"importer".equals(name)||name.endsWith("_importer")',
 '"exporter".equals(name)||name.endsWith("_exporter")',
 "if(!active()){visionShapes=java.util.List.of()",
 "sampleVision(mc);", "shape.bounds()", "camera.rotation()",
 "wireLine(g,corner[i],corner[i|mask]", "new int[]{1,2,4}",
 "MAXIM"
 ):
 if marker=="MAXIM":continue
 assert marker in script,marker
assert "g.text(mc.font" not in script, "Network Vision may not draw fake block labels"
assert "mc.level.addParticle" not in script, "Never replace wireframes with particles"
assert "setBlockAndUpdate(" not in script, "Must never mutate the world"
assert "getChunk(" not in script, "Must never synchronously force-load a chunk"
assert "if(seen.size()<256&&seen.add(next))" in script
assert "found.size()<64" in script
assert "now-visionSampleTick<8L" in script
assert "for(int y=-5;y<=5;y++)" in script
assert "for(int x=-7;x<=7;x++)" in script
assert "Math.min(24," in script
assert workflow.index("python3 features/v174/apply-guidebook-size-445.py") < workflow.index(
 "python3 features/v174/apply-network-vision-xray-451.py")
assert workflow.index("python3 features/v174/apply-network-vision-xray-451.py") < workflow.index(
 "python3 tests/test_v174_network_vision_xray_451.py")
if os.environ.get("V1_SOURCE_ROOT"):
 rendered=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/NetworkVisionClient.java").read_text()
 assert rendered.count("B451_VISION_THROUGH_WALL")==1
 assert "g.fill(x,y,x+2,y+2,color)" in rendered
 assert "@SubscribeEvent public static void hud(RenderGuiEvent.Post event){}" not in rendered
print("V174_NETWORK_VISION_XRAY_451_TEST_PASS")
