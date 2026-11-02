#!/usr/bin/env python3
"""B818: bounded withdrawals and exact Obsidian chain verification.

Run only after the B817 item-list/magnet stage. No user test-JAR.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
path=J/"backpack/V176BackpackMenu.java"
s=path.read_text(encoding="utf-8")
old='''  int count=(int)Math.min((long)wanted,entry.count());
  var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(player.level().registryAccess());
  ItemStack output=codec.recreate(entry.descriptor(),count);'''
new='''  var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(player.level().registryAccess());
  ItemStack output=codec.recreate(entry.descriptor(),1);
  int count=(int)Math.min(Math.min((long)wanted,entry.count()),
      (long)output.getMaxStackSize());
  if(count<=0)return false;
  output.setCount(count);'''
assert s.count(old)==1,("B818_WITHDRAW_API_DRIFT",s.count(old))
path.write_text(s.replace(old,new,1),encoding="utf-8")
print("V176_B818_BACKPACK_WITHDRAWAL_RESPECTS_VANILLA_MAX_STACK PASS")
