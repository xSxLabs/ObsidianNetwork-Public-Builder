#!/usr/bin/env python3
"""B603: fix real energy facade invisibility in the baked block render path.

B602 fixed packet ordering, but the compiled EnergyCableBlock still returned
RenderShape.INVISIBLE while facaded. In MC 26 this leaves no guaranteed visible
model while the separately scheduled facade BER resolves the chosen texture.
Keep the regular thin cable fallback painted, with the existing opaque facade
BER drawn on top; when the facade is opaque it hides the thin cable naturally.
This prevents an entirely invisible cable even if BER data is one frame late.
No cable state/capability/transfer/face logic is touched.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"block/EnergyCableBlock.java"
s=p.read_text(encoding="utf-8")
m=re.search(r"\b(?P<returntype>(?:net\.minecraft\.world\.level\.block\.)?RenderShape)\s+getRenderShape\s*\([^)]*\)\s*\{",s)
assert m,("B603_ENERGY_RENDER_METHOD_MISSING",p)
start=m.end();depth=1;end=None
for k in range(start,len(s)):
 if s[k]=="{":depth+=1
 elif s[k]=="}":
  depth-=1
  if depth==0:end=k;break
assert end is not None,("B603_ENERGY_RENDER_UNCLOSED",p)
body=s[start:end]
assert "FACADED" in body and "RenderShape.INVISIBLE" in body and "RenderShape.MODEL" in body,("B603_ENERGY_RENDER_DRIFT",body)
# Keep exactly the original render return type, visibility even for clients
# that do not yet have the facade BE update. Never hide the only model.
s=s[:start]+'''
  // B603_FACADE_NONINVISIBLE: always offer a baked visual fallback.
  // Full-size chosen facade is still rendered via CableFacadeRenderer.
  // This method must NOT return RenderShape.INVISIBLE on FACADED=true.
  return net.minecraft.world.level.block.RenderShape.MODEL;
 '''+s[end:]
p.write_text(s,encoding="utf-8")
assert s.count("B603_FACADE_NONINVISIBLE")==1
# Ensure the existing facade renderer still actually draws the selected block.
p=J/"client/render/CableFacadeRenderer.java"
r=p.read_text(encoding="utf-8")
assert "blockResolver.update" in r and "facadeModel.submit" in r and "facadeState()" in r,("B603_FACADE_DRAW_PIPELINE_MISSING",p)
client=(J/"client/ClientModEvents.java").read_text(encoding="utf-8")
assert "ModBlockEntities.ENERGY_CABLE.get(), dev.obsidiannetwork.client.render.CableFacadeRenderer::new" in client,("B603_ENERGY_RENDER_REG_MISSING",client[:500])
be=(J/"blockentity/EnergyCableBlockEntity.java").read_text(encoding="utf-8")
assert "getUpdateTag(" in be and "getUpdatePacket(" in be and "saveAdditional(" in be and "loadAdditional(" in be
assert "B602_ENERGY_FACADE_FINAL_SYNC" in (J/"item/CableFacadeItem.java").read_text(encoding="utf-8")
print("B603_ENERGY_FACADE_RENDER_MODEL_FALLBACK_AND_REAL_FACADE_BER_PASS")
