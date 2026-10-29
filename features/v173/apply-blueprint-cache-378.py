#!/usr/bin/env python3
"""B378: cache decoded large Blueprints in Printer and hologram ghost."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"blockentity/NetworkDeviceBlockEntity.java"
s=p.read_text(encoding="utf-8")
old="NetworkBlueprintItem.blocks(blueprint)"
assert old in s,"B378_PRINTER_MISSING_PLAN_READ"
s=s.replace(old,"b378BlueprintBlocks()")
anchor=" private int[] size(){"
assert s.count(anchor)==1,"B378_PRINTER_SIZE_ANCHOR"
s=s.replace(anchor,''' // B378_PRINTER_PLAN_CACHE: decode only when the blueprint changes.
 private ItemStack b378Source=ItemStack.EMPTY;
 private java.util.List<String> b378Plan=java.util.List.of();
 private java.util.List<String> b378BlueprintBlocks(){
  if(!ItemStack.isSameItemSameComponents(b378Source,blueprint)){
   b378Source=blueprint.copy();
   b378Plan=NetworkBlueprintItem.blocks(blueprint);
  }
  return b378Plan;
 }
'''+anchor,1)
p.write_text(s,encoding="utf-8")
p=J/"client/NetworkBlueprintPreviewClient.java"
s=p.read_text(encoding="utf-8")
a='''  var blocks=NetworkBlueprintItem.blocks(held);
  String[] serializedStates=NetworkBlueprintItem.read(held,"xsxlabs_states").split(";",-1);'''
assert s.count(a)==1,("B378_PREVIEW_READ_ANCHOR",s.count(a))
s=s.replace(a,'''  // B378_PREVIEW_PLAN_CACHE: limited 90-voxel animation with one decode.
  if(!ItemStack.isSameItemSameComponents(b378PreviewSource,held)){
   b378PreviewSource=held.copy();
   b378PreviewBlocks=NetworkBlueprintItem.blocks(held);
   b378PreviewStates=NetworkBlueprintItem.read(held,"xsxlabs_states").split(";",-1);
  }
  var blocks=b378PreviewBlocks;
  String[] serializedStates=b378PreviewStates;''',1)
anchor=" private static final DustParticleOptions BLUE="
assert s.count(anchor)==1,"B378_PREVIEW_DECLARATION_ANCHOR"
s=s.replace(anchor,''' private static ItemStack b378PreviewSource=ItemStack.EMPTY;
 private static java.util.List<String> b378PreviewBlocks=java.util.List.of();
 private static String[] b378PreviewStates=new String[0];
'''+anchor,1)
# Build387: the original preview uses var held and lacks ItemStack import.
assert "import net.minecraft.world.item.ItemStack;" not in s
assert s.count("package dev.obsidiannetwork.client;")==1
s=s.replace("package dev.obsidiannetwork.client;",
            "package dev.obsidiannetwork.client;\nimport net.minecraft.world.item.ItemStack;",1)
p.write_text(s,encoding="utf-8")
print("B378_BLUEPRINT_PLAN_CACHES_PASS")
