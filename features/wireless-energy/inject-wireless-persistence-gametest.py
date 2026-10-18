#!/usr/bin/env python3
"""Inject live MC26.1 BlockEntity NBT and WirelessNetworkData Entry codec roundtrips.

Tests real ValueOutput/ValueInput via BlockEntity.saveWithFullMetadata /
BlockEntity.loadStatic while Nether FE is charged. This is intentionally NOT
claimed to be a dedicated server disk-save-and-restart integration test.
"""
import os
from pathlib import Path
target=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=target.read_text()
needle='                     check(crossTx.stored()==12000,"WIRELESS Nether transmitter 12000 FE committed");'
assert s.count(needle)==1, "crossdim game test anchor drift"
addition=r'''
                     // WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1: use actual 26.1 BlockEntity
                     // serialization entrypoints, not mocked map/string roundtrips.
                     var savedWirelessTag=crossTx.saveWithFullMetadata(nether.registryAccess());
                     var restoredWirelessBase=net.minecraft.world.level.block.entity.BlockEntity.loadStatic(
                       crossTxPos,nether.getBlockState(crossTxPos),savedWirelessTag,nether.registryAccess());
                     check(restoredWirelessBase instanceof dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity,
                      "WIRELESS deserialized real Nether transmitter BlockEntity");
                     var restoredWireless=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)restoredWirelessBase;
                     check(restoredWireless.isTransmitter()&&restoredWireless.stored()==12000
                       &&restoredWireless.networkId().equals(crossTx.networkId()),
                       "WIRELESS NBT BE roundtrip keeps 12000 FE, network identity and type");
                     var originalNetworkEntry=new dev.obsidiannetwork.wireless.WirelessNetworkData.Entry(
                       "c15e62b5-9179-4892-b210-e61cf8ee12bb","Persistent private","test-owner",31);
                     var entryTag=dev.obsidiannetwork.wireless.WirelessNetworkData.Entry.CODEC
                       .encodeStart(com.mojang.serialization.JsonOps.INSTANCE,originalNetworkEntry).getOrThrow();
                     var restoredEntry=dev.obsidiannetwork.wireless.WirelessNetworkData.Entry.CODEC
                       .parse(com.mojang.serialization.JsonOps.INSTANCE,entryTag).getOrThrow();
                     check(originalNetworkEntry.equals(restoredEntry),
                      "WIRELESS SavedData network ID, owner, name and five charging bits codec roundtrip");
                     System.out.println("WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1 PASS");
'''
s=s.replace(needle,needle+addition,1)
target.write_text(s)
print("WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1 INJECTED")
