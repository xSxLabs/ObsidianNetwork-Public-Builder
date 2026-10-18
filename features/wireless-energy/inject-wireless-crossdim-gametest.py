#!/usr/bin/env python3
"""Add a *real second-dimension* loaded-transmitter FE conservation GameTest.

Follow-up to inject-wireless-gametest.py; test code only, never packaged into JAR.
The Nether chunk is intentionally loaded by this test fixture, NOT wireless
runtime. No production chunk tickets are created.
"""
from pathlib import Path
import os

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
source=path.read_text()
anchor='System.out.println("WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS");'
assert source.count(anchor)==1, "wireless real FE test changed"
idx=source.index(anchor)
end=source.index(".thenSucceed();",idx)
assert 0<end-idx<300, "wireless FE test step order changed"
assert "WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2" not in source

extra=r'''.thenExecuteAfter(45,()->{
                     // WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2: Nether TX -> overworld RX.
                     var nether=helper.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
                     check(nether!=null,"WIRELESS Nether dimension exists on real GameTest server");
                     BlockPos crossTxPos=new BlockPos(8,80,8);
                     // Only the TEST loads the fixture chunk; production wireless NEVER does.
                     // GameTest must supply a lifetime-long fixture chunk ticket;
                     // runtime itself is forbidden to force-load source dimensions.
                     int fixtureChunkX=crossTxPos.getX()>>4, fixtureChunkZ=crossTxPos.getZ()>>4;
                     nether.setChunkForced(fixtureChunkX,fixtureChunkZ,true);
                     nether.getChunkAt(crossTxPos);
                     nether.setBlock(crossTxPos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                     var crossTx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)nether.getBlockEntity(crossTxPos);
                     check(crossTx!=null&&crossTx.isTransmitter(),"WIRELESS crossdimension real Nether antenna placed");
                     try(var fillCross=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(crossTx.energyHandler().insert(12000,fillCross)==12000,"WIRELESS Nether source buffer accepts 12000 FE");
                      fillCross.commit();
                     }
                     check(crossTx.stored()==12000,"WIRELESS Nether transmitter 12000 FE committed");
                     // The same crossdim registry must expose transactional FE to an
                     // Overworld caller; root rollback must restore the Nether buffer.
                     try(var remoteAbort=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      int probed=dev.obsidiannetwork.wireless.WirelessEnergyRuntime.pull(
                       helper.getLevel().getServer(),"obsidiannetwork:main",512,remoteAbort);
                      check(probed==512,"WIRELESS Overworld lookup can transact with Nether source");
                     }
                     check(crossTx.stored()==12000,"WIRELESS crossdim aborted FE pull reverts Nether buffer");
                     var worldSource=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(0,1,1)));
                     var worldTransmitter=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(2,1,1)));
                     var worldSink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(8,1,1)));
                     check(worldSource!=null&&worldTransmitter!=null&&worldSink!=null,"WIRELESS overworld FE endpoints still present");
                     check(worldSource.stored()+worldTransmitter.stored()+worldSink.stored()==8000,
                      "WIRELESS first-dimension FE conservation before Nether sender");
                   })
                   .thenExecuteAfter(40,()->{
                     var nether=helper.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
                     check(nether!=null,"WIRELESS Nether dimension still loaded");
                     BlockPos crossTxPos=new BlockPos(8,80,8);
                     var crossTx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)nether.getBlockEntity(crossTxPos);
                     var worldSource=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(0,1,1)));
                     var worldTransmitter=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(2,1,1)));
                     var worldSink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(8,1,1)));
                     check(crossTx!=null&&worldSink!=null&&worldTransmitter!=null&&worldSource!=null,
                      "WIRELESS crossdim live entities after transfer");
                     System.out.println("WIRELESS_CROSSDIM_DIAG_V1 active="+crossTx.isActive()
                       +" source="+worldSource.stored()+" bridgeTX="+worldTransmitter.stored()
                       +" sink="+worldSink.stored()+" netherTX="+crossTx.stored()
                       +" available="+dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                         helper.getLevel().getServer(),"obsidiannetwork:main"));
                     check(worldSink.stored()>8000,"WIRELESS Nether FE actually reached overworld receiver and sink");
                     check(worldSource.stored()+worldTransmitter.stored()+worldSink.stored()+crossTx.stored()==20000,
                      "WIRELESS exact conservation across Overworld and Nether");
                     nether.setBlock(crossTxPos,Blocks.AIR.defaultBlockState(),3);
                     nether.setChunkForced(crossTxPos.getX()>>4,crossTxPos.getZ()>>4,false);
                     System.out.println("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS");
                   })
                   '''
source=source[:end]+extra+source[end:]
path.write_text(source)
print("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 INJECTED")
