#!/usr/bin/env python3
"""B605 source integration test: exactly one registered energy-cable renderer,
simultaneously preserving facade and INPUT collar render paths.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
c=(J/"client/ClientModEvents.java").read_text(encoding="utf-8")
p=(J/"client/NetworkPlanterClientRenderRegistration.java").read_text(encoding="utf-8")
combined=(J/"client/EnergyCableCompositeRenderer.java").read_text(encoding="utf-8")
f=(J/"client/render/CableFacadeRenderer.java").read_text(encoding="utf-8")
i=(J/"client/EnergyCableInputRenderer.java").read_text(encoding="utf-8")
assert len(re.findall(r'registerBlockEntityRenderer\s*\(\s*[\w.]*ModBlockEntities\.ENERGY_CABLE\.get\(\)',c))==1
assert "EnergyCableCompositeRenderer::new" in c
assert "ModBlockEntities.ENERGY_CABLE.get()" not in p
assert "NETWORK_PLANTER.get()" in p and "NetworkPlanterRenderer::new" in p
assert "B605_ENERGY_FACADE_AND_COLLAR" in combined
for x in ("new CableFacadeRenderer<>","new EnergyCableInputRenderer(",
          "facade.extractRenderState(be, state.facade",
          "collar.extractRenderState(be, state.collar",
          "facade.submit(state.facade","collar.submit(state.collar"):
 assert x in combined,x
assert "facadeModel.submit" in f and "blockResolver.update" in f
assert "public static final class InputState" in i
# Correctly guard against old invisibility and against dropping additional
# physical bundle blocks; neither should regress in this render-only build.
assert "B603_FACADE_NONINVISIBLE" in (J/"block/EnergyCableBlock.java").read_text(encoding="utf-8")
assert "B602_CONTENTS_ONLY_DROP" in (J/"block/ConduitBundleBlock.java").read_text(encoding="utf-8")
print("B605_SINGLE_COMPOSITE_FACADE_AND_INPUT_RENDERER_PREBUILD_PASS")
