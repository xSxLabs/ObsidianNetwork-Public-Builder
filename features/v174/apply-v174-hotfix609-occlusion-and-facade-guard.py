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
for reg,kind,path in [("NUTRINATOR","Nutrinator","nutrinator"),
                     ("ELECTRIC_WATER_PUMP","Electric Water Pump","electric_water_pump")]:
    # Anchor on the unique registration symbol instead of an exact generic
    # DeferredBlock declaration; private reconstruction reformats its type.
    hits=list(re.finditer(r"\\b"+reg+r"\\s*=",s))
    assert len(hits)==1,("B609_MACHINE_SYMBOL_DRIFT",kind,len(hits))
    start=hits[0].start()
    end=s.find(";",start)
    assert start<end<start+1200,("B609_MACHINE_DECLARATION_RANGE",kind)
    section=s[start:end+1]
    assert re.search(r'BLOCKS\\.registerBlock\\s*\\(\\s*"'+path+r'"',section),("B609_MACHINE_REGISTRATION_CHANGED",kind,section[:650])
    marker=".requiresCorrectToolForDrops()"
    assert section.count(marker)==1 and ".noOcclusion()" not in section,("B609_MACHINE_PROPERTY_DRIFT",kind,section[:800])
    patched=section.replace(marker,marker+".noOcclusion() /* B609_MACHINE_NO_OCCLUSION */",1)
    s=s[:start]+patched+s[end+1:]
assert s.count("B609_MACHINE_NO_OCCLUSION")==2
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
