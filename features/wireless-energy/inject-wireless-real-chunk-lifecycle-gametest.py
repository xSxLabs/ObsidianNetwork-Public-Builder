#!/usr/bin/env python3
"""CI-only actual Nether chunk unload and reload wireless energy regression.

Run after the real cross-dimensional FE and saved-codec/source-index injectors.
The test explicitly loads/unloads a far-away Nether fixture; the production
wireless implementation must not force-load any chunk. An unloaded transmitter
may retain energy on disk but cannot supply FE until vanilla loads it again.
"""
import os
from pathlib import Path

target=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
source=target.read_text()
anchor='''                     System.out.println("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS");
                   })'''
assert source.count(anchor)==1,"crossdim final GameTest action changed"
assert "WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1" not in source

extra=r'''
                   .thenExecuteAfter(2,()->{
                     // Run after the original FE/conservation checks, in a distant
                     // Nether chunk with zero nearby players/spawn/other GameTests.
                     var nether=helper.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
                     check(nether!=null,"WIRELESS lifecycle Nether world exists");
                     BlockPos txPos=new BlockPos(4112,80,4112);
                     int cx=txPos.getX()>>4,cz=txPos.getZ()>>4;
                     // Remove the previously used receiver to prevent drainage of
                     // the fixture before the unload/rehydration assertions.
                     helper.getLevel().setBlock(helper.absolutePos(new BlockPos(7,1,1)),
                      Blocks.AIR.defaultBlockState(),3);
                     nether.setChunkForced(cx,cz,true); // GameTest fixture ticket ONLY.
                     nether.getChunkAt(txPos);
                     nether.setBlock(txPos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                     var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)nether.getBlockEntity(txPos);
                     check(tx!=null&&tx.isTransmitter(),"WIRELESS unload fixture BE exists");
                     try(var funding=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(tx.energyHandler().insert(4096,funding)==4096,
                       "WIRELESS distant sender accepts 4096 FE");
                      funding.commit();
                     }
                     dev.obsidiannetwork.wireless.WirelessEnergyRuntime.register(tx);
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      nether.getServer(),"obsidiannetwork:main")==4096,
                      "WIRELESS loaded remote sender exposes exactly 4096 FE");
                     nether.setChunkForced(cx,cz,false); // Real server now evicts this chunk.
                     System.out.println("WIRELESS_REAL_CHUNK_UNLOAD_PROBE_ARMED_V1");
                   })
                   .thenExecuteAfter(360,()->{
                     var nether=helper.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
                     check(nether!=null,"WIRELESS lifecycle Nether still exists");
                     BlockPos txPos=new BlockPos(4112,80,4112);
                     int cx=txPos.getX()>>4,cz=txPos.getZ()>>4;
                     // Checking the loaded map (not getChunkAt) MUST NOT load it.
                     boolean loaded=nether.getChunkSource().hasChunk(cx,cz);
                     System.out.println("WIRELESS_REAL_CHUNK_UNLOAD_DIAG_V1 loaded="+loaded);
                     check(!loaded,"WIRELESS Nether sender chunk did not actually unload");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      nether.getServer(),"obsidiannetwork:main")==0,
                      "WIRELESS unloaded source ghost FE available");
                     try(var aborted=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.pull(
                       nether.getServer(),"obsidiannetwork:main",4096,aborted)==0,
                       "WIRELESS unloaded source supplied FE");
                     }
                     // Reload is explicitly performed by the TEST, not by wireless.
                     nether.setChunkForced(cx,cz,true);
                     nether.getChunkAt(txPos);
                   })
                   .thenExecuteAfter(12,()->{
                     var nether=helper.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
                     check(nether!=null,"WIRELESS reloaded Nether world exists");
                     BlockPos txPos=new BlockPos(4112,80,4112);
                     var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)nether.getBlockEntity(txPos);
                     check(tx!=null&&tx.isTransmitter()&&tx.stored()==4096,
                      "WIRELESS loaded sender lost buffered FE on actual chunk eviction/reload");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      nether.getServer(),"obsidiannetwork:main")==4096,
                      "WIRELESS reloaded sender failed automatic onLoad registration");
                     try(var rollback=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.pull(
                       nether.getServer(),"obsidiannetwork:main",512,rollback)==512,
                       "WIRELESS reloaded sender cannot deliver remote FE");
                     }
                     check(tx.stored()==4096,"WIRELESS aborted remote FE transaction lost sender energy");
                     nether.setBlock(txPos,Blocks.AIR.defaultBlockState(),3);
                     nether.setChunkForced(txPos.getX()>>4,txPos.getZ()>>4,false);
                     System.out.println("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS");
                   })'''
source=source.replace(anchor,anchor+extra,1)
target.write_text(source)
print("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 INJECTED")
