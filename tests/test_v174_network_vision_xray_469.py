#!/usr/bin/env python3
"""B469 Network Vision 3D projection/filter/armor gates and CI ordering."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
patch=(root/"features/v174/apply-network-vision-xray-469.py").read_text()
workflow=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(patch)
assert "V173_B351_VISION_FEEDBACK" in patch
assert 's.index(" @SubscribeEvent public static void hud(RenderGuiEvent.Post event){")' in patch
assert "V174_XRAY_WORLD_WIREFRAME_B469" in patch
for marker in (
    '"obsidiannetwork".equals(key.getNamespace())',
    'name.equals("conduit_bundle")||name.endsWith("_cable")',
    'name.equals("importer")||name.endsWith("_importer")',
    'name.equals("exporter")||name.endsWith("_exporter")',
    'xrayPositions.size()>=160',
    'mc.level.hasChunkAt(at)',
    'scannedWorld==mc.level',
    'mc.player.tickCount-scannedAt<8',
    'if(!active())return;',
    'g.fill(px,py,px+1,py+1,color)',
    'wireCube(g,at,half,color,origin,inverse,focal,width,height)',
):
    assert marker in patch,marker
for prohibited in ('setBlock(', 'setBlockEntity(', 'setChunkForced(', 'getChunk(', 'getServer().'):
    assert prohibited not in patch,prohibited
assert workflow.index("python3 features/v174/apply-nightvision-warden-darkness-464.py") < workflow.index("python3 features/v174/apply-network-vision-xray-469.py")
assert workflow.index("python3 features/v174/apply-network-vision-xray-469.py") < workflow.index("python3 tests/test_v174_network_vision_xray_469.py")
# B470: apply the real patch to the actual 328 baseline HUD. A regression
# in the original whitespace or class/method brace boundary must fail here,
# before the expensive game build.
base=(root/"features/v173/apply-holo-vision-portals-328.py").read_text()
prefix="vision.write_text(r'''"
a=base.index(prefix)+len(prefix)
b=base.index("''',encoding=\"utf-8\")",a)
fixture=base[a:b]
old_toggle=" public static void toggleFromWheel(){"
assert fixture.count(old_toggle)==1
fixture=fixture.replace(old_toggle,
    " // V173_B351_VISION_FEEDBACK\\n"+old_toggle)
with tempfile.TemporaryDirectory() as temp:
    src=Path(temp)/"dev/obsidiannetwork/client/NetworkVisionClient.java"
    src.parent.mkdir(parents=True)
    src.write_text(fixture)
    env=os.environ.copy()
    env["V1_SOURCE_ROOT"]=temp
    result=subprocess.run([sys.executable,str(root/"features/v174/apply-network-vision-xray-469.py")],
                          env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    generated=src.read_text()
    assert generated.count("{")==generated.count("}"),"Broken NetworkVisionClient Java brace nesting"
    assert generated.rstrip().endswith("}"),"Missing class closing brace"
    assert "if(cable&&(" not in generated
    assert "V174_XRAY_WORLD_WIREFRAME_B469" in generated
    assert generated.count("public static void hud(")==1
    assert generated.count("private static int xrayKind(")==1

if os.environ.get("V1_SOURCE_ROOT"):
    java=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/NetworkVisionClient.java").read_text()
    assert "V174_XRAY_WORLD_WIREFRAME_B469" in java
    assert "V173_B351_VISION_FEEDBACK" in java
    assert "toggleFromWheel()" in java
    assert "wireCube(g,at,half,color,origin,inverse,focal,width,height)" in java
    assert "xrayPositions.size()>=160" in java
    assert "name.equals(\"importer\")" in java
    assert 'mc.level.hasChunkAt(at)' in java
    assert "if(cable&&(" not in java
print("V174_XRAY_WORLD_WIREFRAME_B469_TEST_PASS")
