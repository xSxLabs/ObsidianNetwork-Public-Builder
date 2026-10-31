#!/usr/bin/env python3
"""v1.7.4 B609 fail-closed source/asset validation, before expensive Gradle.

Guard two specific non-occluding machines and original full-cube baked models.
Guarantee facades and collars use ONE client renderer; prevent the B604 and
B607 regressions. No unrelated BE, cable, FE/t or recipe changes allowed.
"""
from pathlib import Path
import json,os,re
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
s=(J/"ObsidianNetwork.java").read_text(encoding="utf-8")
for ident,cl,model in [
 ("NUTRINATOR","NutrinatorBlock","nutrinator"),
 ("ELECTRIC_WATER_PUMP","ElectricWaterPumpBlock","electric_water_pump")
]:
 pattern=r"public\s+static\s+final\s+DeferredBlock<[^;]+?\b"+ident+r"\s*=\s*BLOCKS\.registerBlock\s*\([\s\S]*?(?=;)"
 m=list(re.finditer(pattern,s))
 assert len(m)==1,("B609_REG_MISSING_OR_DUPLICATE",ident,len(m))
 definition=m[0].group()
 assert ".requiresCorrectToolForDrops().noOcclusion()" in definition,("B609_MUST_NOT_CULL_NEIGHBOR_FACES",ident)
 assert definition.count(".noOcclusion()")==1,("B609_DUPLICATE_CALL",ident)
 assert cl in definition,("B609_WRONG_TYPE",ident)
 java=(J/("nutrition/NutrinatorBlock.java" if ident=="NUTRINATOR" else "pump/ElectricWaterPumpBlock.java")).read_text(encoding="utf-8")
 assert "RenderShape.MODEL" in java
 blockmodel=json.loads((R/"models/block"/(model+".json")).read_text(encoding="utf-8"))
 # These machines use inset, multi-cuboid hi-tech models, NOT full cubes.
 # If the block wrongly occludes its neighbors, adjacent stone faces get
 # culled and holes appear around the machine.
 assert isinstance(blockmodel.get("elements"),list) and len(blockmodel["elements"])>=5,("B609_DETAILED_MODEL_MISSING",model)
 assert all(len(e["from"])==3 and len(e["to"])==3 for e in blockmodel["elements"])
 assert any(e["from"][0]>0 or e["to"][0]<16 for e in blockmodel["elements"]),("B609_EXPECTED_INSET_GEOMETRY",model)
 blockstate=json.loads((R/"blockstates"/(model+".json")).read_text(encoding="utf-8"))
 assert blockstate["variants"][""]["model"]=="obsidiannetwork:block/"+model
# Tight client render regression test:
client=(J/"client/ClientModEvents.java").read_text(encoding="utf-8")
reg=(J/"client/NetworkPlanterClientRenderRegistration.java").read_text(encoding="utf-8")
composite=(J/"client/EnergyCableCompositeRenderer.java").read_text(encoding="utf-8")
facade=(J/"client/render/CableFacadeRenderer.java").read_text(encoding="utf-8")
source=(J/"blockentity/EnergyCableBlockEntity.java").read_text(encoding="utf-8")
assert client.count("ModBlockEntities.ENERGY_CABLE.get(), dev.obsidiannetwork.client.EnergyCableCompositeRenderer::new")==1
assert "ModBlockEntities.ENERGY_CABLE.get()" not in reg
assert "facade.submit(state.facade" in composite and "collar.submit(state.collar" in composite
assert "facade.extractRenderState(be, state.facade" in composite
assert "collar.extractRenderState(be, state.collar" in composite
assert "blockResolver.update" in facade and "facadeModel.submit" in facade
assert "getUpdatePacket(" in source and "getUpdateTag(" in source
assert "B602_ENERGY_FACADE_FINAL_SYNC" in (J/"item/CableFacadeItem.java").read_text(encoding="utf-8")
assert "B603_FACADE_NONINVISIBLE" in (J/"block/EnergyCableBlock.java").read_text(encoding="utf-8")
print("B609_MACHINE_NONOCCLUSION_2_AND_ENERGY_CABLE_FACADE_RENDERER_PASS")
