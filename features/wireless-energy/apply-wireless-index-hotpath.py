#!/usr/bin/env python3
"""Avoid repeated sender-index walks on every receiver face and chunk unload.

Runs after wireless-hardening. Preserves the same global 16k FE/5-tick
budget, sender fairness, NeoForge nested transactions and chunk-load rules.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(relative,old,new):
 path=root/relative
 source=path.read_text()
 assert source.count(old)==1, f"wireless indexed runtime anchor drift: {relative}: {old[:100]!r}"
 path.write_text(source.replace(old,new,1))

entity="blockentity/WirelessNetworkBlockEntity.java"
change(entity,
 """  int remainingBudget=MAX_TRANSFER;
  for(Direction side:DIRECTIONS){
   if(remainingBudget<=0)break;""",
 """  int remainingBudget=MAX_TRANSFER;
  // Resolve the loaded-sender index lazily. Empty receiver faces cost no scan.
  int remainingSupply=-1;
  for(Direction side:DIRECTIONS){
   if(remainingBudget<=0||remainingSupply==0)break;""")
change(entity,
 "   int offer=(int)Math.min(remainingBudget,WirelessEnergyRuntime.available(server.getServer(),be.networkId));",
 "   int offer=Math.min(remainingBudget,remainingSupply);")
change(entity,
 """   if(target==null)continue;
   int offer=Math.min(remainingBudget,remainingSupply);""",
 """   if(target==null)continue;
   if(remainingSupply<0){
    remainingSupply=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available(server.getServer(),be.networkId));
   }
   if(remainingSupply<=0)break;
   int offer=Math.min(remainingBudget,remainingSupply);""")
change(entity,
 "     if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;}",
 "     if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}")

runtime="wireless/WirelessEnergyRuntime.java"
change(runtime,
 """  for(var bucket:server.values())bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  server.entrySet().removeIf(e->e.getValue().isEmpty());""",
 """  // The sender is always registered under its current ID; selectNetwork()
  // removes the old bucket before updating its identity.
  var bucket=server.get(sender.networkId());
  if(bucket==null)return;
  bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  if(bucket.isEmpty())server.remove(sender.networkId());
  if(server.isEmpty())LOADED.remove(level.getServer());""")
print("WIRELESS_RECEIVER_LAZY_INDEX_WALK_V2 PASS")
