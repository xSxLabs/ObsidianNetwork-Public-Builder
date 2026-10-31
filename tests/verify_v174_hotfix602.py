#!/usr/bin/env python3
"""Fail-closed final source/asset check for integrated v1.7.4 B602 hotfix."""
import os,re,json
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def src(rel):return (J/rel).read_text(encoding="utf-8")
block=src("block/ConduitBundleBlock.java")
start=block.find("getDrops(")
assert start>=0
method=block[start:block.find("return drops;",start)+14]
assert all(x in method for x in ("super.getDrops","layerStack(","containedUpgradeDrops","facadeState()","drops.removeIf(stack -> stack.getItem()==this.asItem())")),"B602_BUNDLE_LOOT_REGRESSION"
assert "playerWillDestroy(" not in block,"B602_DUPLICATE_BREAK_PATH"
energy=src("blockentity/EnergyCableBlockEntity.java")
assert all(x in energy for x in ("getUpdateTag(","getUpdatePacket(","setFacadeState(","facadeState()")),"B602_ENERGY_SYNC"
facade=src("item/CableFacadeItem.java")
assert "B602_ENERGY_FACADE_FINAL_SYNC" in facade
assert "EnergyCableBlock.FACADED" in facade and "requestModelDataUpdate()" in facade
client=src("client/ClientModEvents.java")
assert "ModBlockEntities.ENERGY_CABLE.get(), dev.obsidiannetwork.client.render.CableFacadeRenderer::new" in client
for name in ("ultra_energy_core","ultra_solar_matrix"):
 image=A/"textures/item"/(name+".png")
 with Image.open(image) as im:
  im.load()
  assert im.size==(32,32) and im.mode=="RGBA"
  colors=set(im.getdata())
  assert len(colors)>=8
  assert any(a==0 for r,g,b,a in colors) and any(a==255 for r,g,b,a in colors)
 model=json.loads((A/"models/item"/(name+".json")).read_text(encoding="utf-8"))
 assert model["textures"]["layer0"]=="obsidiannetwork:item/"+name
 item=json.loads((A/"items"/(name+".json")).read_text(encoding="utf-8"))
 assert item["model"]["model"]=="obsidiannetwork:item/"+name
print("B602_BUNDLE_DROPS_FACADE_SYNC_UNIQUE_TECH_TEXTURES_CONTRACT_PASS")
