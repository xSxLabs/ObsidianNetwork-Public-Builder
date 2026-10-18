#!/usr/bin/env python3
"""Cache network GUI's accessible-name snapshot for the current server tick.

AbstractContainerMenu polls ContainerData indices multiple times per tick.
Without this cache each of its four get(index) calls filters/allocates the
available network list anew. Preserve live changes on the next server tick.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/menu/WirelessNetworkMenu.java"
s=p.read_text()
needle='''   public int get(int index){
    if(!(inv.player instanceof ServerPlayer player))return 0;
    var sd=WirelessNetworkData.get(player.level().getServer());
    var nets=sd.available(player);
    var selected=sd.find(be.networkId());
    return switch(index){'''
replacement='''   private long lastSnapshotTick=Long.MIN_VALUE;
   private List<WirelessNetworkData.Entry> cachedNetworks=List.of();
   public int get(int index){
    if(!(inv.player instanceof ServerPlayer player))return 0;
    var sd=WirelessNetworkData.get(player.level().getServer());
    long now=player.level().getGameTime();
    if(now!=lastSnapshotTick){
     cachedNetworks=sd.available(player);
     lastSnapshotTick=now;
    }
    var nets=cachedNetworks;
    var selected=sd.find(be.networkId());
    return switch(index){'''
assert s.count(needle)==1,"wireless menu generated source changed"
p.write_text(s.replace(needle,replacement,1))
print("WIRELESS_MENU_ONE_NETWORK_SNAPSHOT_PER_TICK_V1 PASS")
