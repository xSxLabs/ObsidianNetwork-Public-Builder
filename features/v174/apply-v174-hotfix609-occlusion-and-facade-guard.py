#!/usr/bin/env python3
"""B609: Nutrinator and Electric Water Pump must not occlude neighboring walls.

These are block models, not x-ray renderers. Their old full-occlusion flag let
the block-face culler remove bordering solid block faces. On the small machine
models, this can expose the void behind the machine / let players see through
surrounding walls. Make only these TWO blocks non-occluding; keep all physical
collisions, actual models, inventories, FE, tanks and server ticker untouched.

Also fail if energy cable facades are not registered through B608's single
combined renderer, including unchanged client-synced selected facade state.
"""
from pathlib import Path
import os,re
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"ObsidianNetwork.java"
s=p.read_text(encoding="utf-8")
for reg,kind in [("NUTRINATOR","Nutrinator"),("ELECTRIC_WATER_PUMP","Electric Water Pump")]:
    pat=r'(?P<declaration>public\s+static\s+final\s+DeferredBlock<[^;]+?\b'+reg+r'\s*=\s*BLOCKS\.registerBlock\s*\([\s\S]*?)(?P<properties>p\s*->\s*p\.mapColor\(MapColor\.METAL\)\.strength\(3\.0F,\s*8\.0F\)\.requiresCorrectToolForDrops\(\))(?P<tail>\s*\)\s*;)'
    matches=list(re.finditer(pat,s))
    assert len(matches)==1,("B609_MACHINE_REGISTRATION_DRIFT",kind,len(matches))
    m=matches[0]
    replacement=m.group("properties").replace(".requiresCorrectToolForDrops()", ".requiresCorrectToolForDrops().noOcclusion()")
    assert replacement!=m.group("properties")
    s=s[:m.start("properties")]+replacement+s[m.end("properties"):]
assert s.count("B609_MACHINE_NO_OCCLUSION")==0
# One token marker near the actual registrations for diagnostics.
s=s.replace("p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F).requiresCorrectToolForDrops().noOcclusion()",
'''p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F).requiresCorrectToolForDrops().noOcclusion() // B609_MACHINE_NO_OCCLUSION''',1)
# Java line comments may swallow registration terminator! Prefer block comment.
s=s.replace(" // B609_MACHINE_NO_OCCLUSION", " /* B609_MACHINE_NO_OCCLUSION */")
p.write_text(s,encoding="utf-8")
for loc in ["nutrition/NutrinatorBlock.java","pump/ElectricWaterPumpBlock.java"]:
    code=(J/loc).read_text(encoding="utf-8")
    assert "return RenderShape.MODEL;" in code,("B609_MACHINE_RENDER_SHAPE_DRIFT",loc)
    assert "extends BaseEntityBlock" in code,("B609_MACHINE_BLOCK_KIND_DRIFT",loc)
# Preserve existing client facade and Input collar paths without adding a
# competing BE renderer, suppressing normal depth tests, or world scanning.
c=(J/"client/ClientModEvents.java").read_text(encoding="utf-8")
n=(J/"client/NetworkPlanterClientRenderRegistration.java").read_text(encoding="utf-8")
r=(J/"client/EnergyCableCompositeRenderer.java").read_text(encoding="utf-8")
f=(J/"client/render/CableFacadeRenderer.java").read_text(encoding="utf-8")
be=(J/"blockentity/EnergyCableBlockEntity.java").read_text(encoding="utf-8")
assert "ModBlockEntities.ENERGY_CABLE.get(), dev.obsidiannetwork.client.EnergyCableCompositeRenderer::new" in c
assert "ModBlockEntities.ENERGY_CABLE.get()" not in n, "B609_ENERGY_BER_OVERRIDDEN"
assert "facade.extractRenderState(be, state.facade" in r and "facade.submit(state.facade" in r
assert "collar.extractRenderState(be, state.collar" in r and "collar.submit(state.collar" in r
assert "facadeModel.submit" in f and "blockResolver.update" in f
assert "getUpdateTag(" in be and "getUpdatePacket(" in be and "facadeState()" in be
print("B609_MACHINE_OCCLUSION_TWO_BLOCKS_AND_ENERGY_FACADE_BER_PASS")
