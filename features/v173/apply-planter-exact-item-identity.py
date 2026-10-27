#!/usr/bin/env python3
"""v1.7.3: store planter harvests with terminal's exact ItemStack identity.

ItemKey.simple(item_id) is not always the canonical ItemStack key seen by the
Crafting Terminal. Leave v1.7.2 frozen and preserve output conservation.
"""
import os
from pathlib import Path

target = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/blockentity/NetworkPlanterBlockEntity.java"
src = target.read_text(encoding="utf-8")
old_gate = """   if(runtime==null||!runtime.powered())continue;
   for(int i=0;i<9;i++){"""
new_gate = """   if(runtime==null||!runtime.powered())continue;
   // V173_PLANTER_EXACT_ITEM_KEY: same canonical identity as the terminal.
   var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(world.registryAccess());
   for(int i=0;i<9;i++){"""
old_insert = """    ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString());
    long accepted=runtime.storage().insert(key,stack.getCount());"""
new_insert = """    // Preserve all components; vanilla oak logs and carrots now share the
    // exact same identity whether entered by planter or terminal.
    var descriptor=codec.describe(stack.copyWithCount(1));
    long accepted=runtime.storage().insertExact(
        descriptor.key(),descriptor.canonicalPayload(),stack.getCount());"""
for label, old, new in (("network gate",old_gate,new_gate),("storage insert",old_insert,new_insert)):
    if src.count(old)!=1:
        raise RuntimeError(f"Planter {label}: expected one exact anchor, got {src.count(old)}")
    src=src.replace(old,new,1)
for token in (
    "V173_PLANTER_EXACT_ITEM_KEY",
    "descriptor.key(),descriptor.canonicalPayload(),stack.getCount()",
    "stack.shrink((int)Math.min(accepted,stack.getCount()))",
    "if(stack.isEmpty())output[i]=ItemStack.EMPTY;",
    "for(int i=0;i<9;i++){",
    "if(runtime==null||!runtime.powered())continue;",
):
    if token not in src:
        raise RuntimeError(f"Missing planter conservation marker: {token}")
if "runtime.storage().insert(key,stack.getCount())" in src:
    raise RuntimeError("Legacy planter ID-only insertion remains")
target.write_text(src,encoding="utf-8")
print("V173_PLANTER_EXACT_ITEM_KEY_PASS: canonical terminal-compatible inserts and acknowledged-only output shrink")
