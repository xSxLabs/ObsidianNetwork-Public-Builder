#!/usr/bin/env python3
"""Build338: render real uncamouflaged cable models while Vision is active.

Only renderer-local visual state is changed. The physical blockstate,
attached facade item, saved block entity, topology, IO and FE remain intact.
Requires Build337 and runs only on v1.7.3.
"""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
renderer=J/"client/render/CableFacadeRenderer.java"
s=renderer.read_text(encoding="utf-8")
old=('state.facade = dev.obsidiannetwork.client.NetworkVisionClient.active() ? '
     'net.minecraft.world.level.block.Blocks.AIR.defaultBlockState() : blockEntity.facadeState();')
assert s.count(old)==1,("V173_B338_CABLE_RENDERER_DRIFT",s.count(old))
new='''// V173_B338_CABLE_MODEL_REVEAL: the baked FACADED model may be empty.
      // Resolve an UNFACADED model just for this frame, not a world mutation.
      if(dev.obsidiannetwork.client.NetworkVisionClient.active()&&
         !blockEntity.facadeState().isAir()){
         net.minecraft.world.level.block.state.BlockState bare=blockEntity.getBlockState();
         var flag=bare.getBlock().getStateDefinition().getProperty("facaded");
         if(flag instanceof net.minecraft.world.level.block.state.properties.BooleanProperty bool)
           bare=bare.setValue(bool,false);
         state.facade=bare;
      }else state.facade=blockEntity.facadeState();'''
s=s.replace(old,new,1)
assert "this.blockResolver.update(state.facadeModel, state.facade" in s
renderer.write_text(s,encoding="utf-8")

# Bundled conduits use a separate BER. Their native 3D colored lanes remain
# in place; skip only the camouflage overlay when Vision is active.
bundle=J/"client/render/ConduitBundleRenderer.java"
b=bundle.read_text(encoding="utf-8")
assert "facadeModel.submit" in b and "drawLayer(" in b
assert "if(s.facaded)" in b, "V173_B338_BUNDLE_FACADE_GUARD_CHANGED"
b=b.replace("if(s.facaded)",
 '''if(s.facaded&&!dev.obsidiannetwork.client.NetworkVisionClient.active())''')
# Some renderer versions also skip native cable lanes under the disguise.
if "if(!s.facaded)" in b:
 b=b.replace("if(!s.facaded)",
  "if(!s.facaded||dev.obsidiannetwork.client.NetworkVisionClient.active())")
bundle.write_text(b,encoding="utf-8")

print("V173_B338_REAL_UNFACADED_MODELS_PASS: no fake overlays or world changes")
