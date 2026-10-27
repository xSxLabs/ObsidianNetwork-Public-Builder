#!/usr/bin/env python3
"""v1.7.3: consume the same canonical material keys as Terminal and Planter.

Read pre-fix ID-only stacks too. Failed world placement must restore exactly
the item key that was removed, with an acknowledged full refund.
"""
import os
from pathlib import Path

target=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/NetworkDeviceBlockEntity.java"
text=target.read_text(encoding="utf-8")
old_extract='''  ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(material.getItem()).toString());
  long extracted=net.storage().extract(key,1L);'''
new_extract='''  // V173_PRINTER_CANONICAL_MATERIALS: same exact ItemStack identity as
  // the Storage Terminal and Network Planter, with preserved item components.
  var descriptor=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(
      world.registryAccess()).describe(material.copyWithCount(1));
  ItemKey canonicalKey=descriptor.key();
  ItemKey legacyKey=ItemKey.simple(BuiltInRegistries.ITEM.getKey(material.getItem()).toString());
  ItemKey extractedKey=canonicalKey;
  long extracted=net.storage().extract(canonicalKey,1L);
  // Read a pre-fix ID-only storage key only if no exact item was available.
  if(extracted==0L && !legacyKey.equals(canonicalKey)){
   extractedKey=legacyKey;
   extracted=net.storage().extract(legacyKey,1L);
  }'''
old_refund='''  if(!placed){
   net.storage().insert(key,1L);
   setStatus("PROTECTED/BLOCKED AT "+dest.toShortString());return;
  }'''
new_refund='''  if(!placed){
   // V173_PRINTER_CONSERVATION: restore the exact variant extracted.
   // Never rekey a legacy item as a side-effect of failed placement.
   long restored;
   if(extractedKey.equals(canonicalKey)){
    net.descriptors().registerKnown(canonicalKey,descriptor.canonicalPayload());
    restored=net.storage().insertExact(canonicalKey,descriptor.canonicalPayload(),1L);
   }else restored=net.storage().insert(legacyKey,1L);
   if(restored!=1L)
    throw new IllegalStateException("Network Printer material refund failed: "+extractedKey);
   setStatus("PROTECTED/BLOCKED AT "+dest.toShortString());return;
  }'''
old_fluid='''net.storage().insert(key,1L);
    setStatus("UNSUPPORTED FLUID BLOCKSTATE "+name);return;'''
new_fluid='''// V173_PRINTER_FLUID_CONSERVATION: malformed/old fluid states must not eat materials.
     if(extractedKey.equals(canonicalKey))
      net.descriptors().registerKnown(canonicalKey,descriptor.canonicalPayload());
     long fluidRefund=extractedKey.equals(canonicalKey)
       ?net.storage().insertExact(canonicalKey,descriptor.canonicalPayload(),1L)
       :net.storage().insert(legacyKey,1L);
     if(fluidRefund!=1L)
      throw new IllegalStateException("Network Printer fluid-state refund failed: "+extractedKey);
     setStatus("UNSUPPORTED FLUID BLOCKSTATE "+name);return;'''
for label,old in (("extract",old_extract),("refund",old_refund),("fluid rollback",old_fluid)):
 if text.count(old)!=1:
  raise RuntimeError("Printer "+label+" source drift: "+str(text.count(old))+" anchors")
assert "V173_PRINTER_CANONICAL_MATERIALS" not in text
result=text.replace(old_extract,new_extract,1).replace(old_refund,new_refund,1).replace(old_fluid,new_fluid,1)
for marker in ("if(extracted!=1L)","missing=material.copyWithCount(1)",
               "missing=ItemStack.EMPTY;","boolean placed=world.setBlock(dest,targetState,3)",
               "spendFE(250L)"):
 if marker not in result:
  raise RuntimeError("Printer conservation guard missing: "+marker)
if "net.storage().insert(key,1L)" in result:
 raise RuntimeError("Printer legacy refund remains")
target.write_text(result,encoding="utf-8")
print("V173_PRINTER_CANONICAL_MATERIALS_PASS: exact terminal key, legacy fallback, checked same-key refund")
