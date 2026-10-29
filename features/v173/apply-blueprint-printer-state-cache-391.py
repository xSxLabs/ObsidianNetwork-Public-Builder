#!/usr/bin/env python3
"""B391: cache large Blueprint block states alongside the already cached plan.

Before this patch, every Printer block placement decoded the entire (possibly
GZIP-compressed) xsxlabs_states string and split it into up to one million
entries, once per placed block. Decode once per saved-blueprint component
identity; never change the original state restoration or printer transactions.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/NetworkDeviceBlockEntity.java"
s=p.read_text(encoding="utf-8")

def replace(old,new):
 global s
 count=s.count(old)
 assert count==1,("B391_PRINTER_SOURCE_DRIFT",old[:110],count)
 s=s.replace(old,new,1)

replace(
''' private ItemStack b378Source=ItemStack.EMPTY;
 private java.util.List<String> b378Plan=java.util.List.of();
 private java.util.List<String> b378BlueprintBlocks(){
  if(!ItemStack.isSameItemSameComponents(b378Source,blueprint)){
   b378Source=blueprint.copy();
   b378Plan=NetworkBlueprintItem.blocks(blueprint);
  }
  return b378Plan;
 }''',
''' // B391_PRINTER_STATE_CACHE: blocks and block states share ONE invalidation.
 private ItemStack b378Source=ItemStack.EMPTY;
 private java.util.List<String> b378Plan=java.util.List.of();
 private String[] b391States=new String[0];
 private java.util.List<String> b378BlueprintBlocks(){
  if(!ItemStack.isSameItemSameComponents(b378Source,blueprint)){
   b378Source=blueprint.copy();
   b378Plan=NetworkBlueprintItem.blocks(blueprint);
   String states=NetworkBlueprintItem.read(blueprint,"xsxlabs_states");
   b391States=states.isBlank()?new String[0]:states.split(";",-1);
  }
  return b378Plan;
 }
 private String[] b391BlueprintStates(){
  b378BlueprintBlocks(); // Reuse B378's exact item+component cache key.
  return b391States;
 }''')

replace(
'''  String properties=NetworkBlueprintItem.read(blueprint,"xsxlabs_states");
  if(!properties.isBlank()){
   String[] all=properties.split(";",-1);
   if(index<all.length)for(String pair:all[index].split("&")){
    int mid=pair.indexOf('=');
    if(mid<=0)continue;
    var property=block.getStateDefinition().getProperty(pair.substring(0,mid));
    if(property!=null)targetState=restoreProperty(targetState,property,pair.substring(mid+1));
   }
  }''',
'''  // B391_NO_PER_BLOCK_DECOMPRESSION: only parse properties for this voxel.
  String[] all=b391BlueprintStates();
  if(index>=0&&index<all.length&&!all[index].isEmpty()){
   for(String pair:all[index].split("&")){
    int mid=pair.indexOf('=');
    if(mid<=0)continue;
    var property=block.getStateDefinition().getProperty(pair.substring(0,mid));
    if(property!=null)targetState=restoreProperty(targetState,property,pair.substring(mid+1));
   }
  }''')
for marker in ("B378_PRINTER_PLAN_CACHE","B391_PRINTER_STATE_CACHE",
               "B391_NO_PER_BLOCK_DECOMPRESSION",
               "ItemStack.isSameItemSameComponents(b378Source,blueprint)",
               "private String[] b391BlueprintStates()"):
 assert marker in s,("B391_PRINTER_MARKER_MISSING",marker)
assert s.count('NetworkBlueprintItem.read(blueprint,"xsxlabs_states")')==1, "B391_STATES_READ_NOT_ONCE"
p.write_text(s,encoding="utf-8")
print("B391_CACHED_BLUEPRINT_STATES_PRINTER_PASS")
