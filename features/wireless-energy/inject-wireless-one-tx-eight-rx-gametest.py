#!/usr/bin/env python3
"""Inject a real server-tick proof of 1 loaded transmitter feeding 8 receivers.

Runs immediately after the density injector. Reuses its warmed isolated
Overworld chunks once 100 prior transmitters and receivers were removed.
The eight sinks receive only committed FE from one sender, with exact
conservation; neither test nor production manually invokes receiver ticks.
"""
import os
from pathlib import Path

target = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/build103/Build103GameTests.java"
s = target.read_text(encoding="utf-8")
old = r'''                     for(int cx=260;cx<=262;cx++)for(int cz=260;cz<=262;cz++)
                      world.setChunkForced(cx,cz,false);
                     System.out.println("WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS");
                   })
                   .thenSucceed();'''
new = r'''                     System.out.println("WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS");

                     // One sender, eight remote receivers, eight real input Energy Cells.
                     // The dedicated fixture has zero other loaded transmitters.
                     var fanoutSource=new BlockPos(4160,80,4161);
                     world.setBlock(fanoutSource,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                     var singleTx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)
                      world.getBlockEntity(fanoutSource);
                     check(singleTx!=null&&singleTx.isTransmitter(),
                      "WIRELESS fanout only transmitter exists");
                     for(int i=0;i<8;i++){
                      var receiverPos=new BlockPos(4162+i*3,80,4161);
                      world.setBlock(receiverPos,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
                      world.setBlock(receiverPos.east(),ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                      var rx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)
                       world.getBlockEntity(receiverPos);
                      var fanoutSink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)
                       world.getBlockEntity(receiverPos.east());
                      check(rx!=null&&!rx.isTransmitter()&&fanoutSink!=null,
                       "WIRELESS fanout real receiver and sink placed");
                      check(fanoutSink.sideMode(Direction.WEST)==
                       dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.INPUT,
                       "WIRELESS fanout sink WEST input configured");
                     }
                     try(var funding=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(singleTx.energyHandler().insert(512000,funding)==512000,
                       "WIRELESS one TX must accept all eight receivers' 512k FE in one transaction");
                      funding.commit();
                     }
                     check(singleTx.stored()==512000,
                      "WIRELESS one TX holds committed 512000 FE");
                     System.out.println("WIRELESS_ONE_TX_EIGHT_RX_V1 ARMED");
                   })
                   .thenExecuteAfter(5,()->{
                     var world=helper.getLevel();
                     var txPos=new BlockPos(4160,80,4161);
                     var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)
                      world.getBlockEntity(txPos);
                     check(tx!=null,"WIRELESS one TX persists after ticks");
                     long conservation=tx.stored(),delivered=0;
                     for(int i=0;i<8;i++){
                      var rxPos=new BlockPos(4162+i*3,80,4161);
                      var fanoutSink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)
                       world.getBlockEntity(rxPos.east());
                      check(fanoutSink!=null&&fanoutSink.stored()>0,
                       "WIRELESS all eight receivers must deliver real FE, receiver "+i);
                      delivered+=fanoutSink.stored();
                      conservation+=fanoutSink.stored();
                     }
                     check(delivered>0&&conservation==512000L,
                      "WIRELESS one TX eight RX FE conservation exactly 512000");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      world.getServer(),"obsidiannetwork:main")==tx.stored(),
                      "WIRELESS single loaded TX remaining balance matches network index");
                     System.out.println("WIRELESS_ONE_TX_EIGHT_RX_V1 PASS total="+conservation+
                      " delivered="+delivered+" remaining="+tx.stored());
                     world.setBlock(txPos,Blocks.AIR.defaultBlockState(),3);
                     for(int i=0;i<8;i++){
                      var p=new BlockPos(4162+i*3,80,4161);
                      world.setBlock(p,Blocks.AIR.defaultBlockState(),3);
                      world.setBlock(p.east(),Blocks.AIR.defaultBlockState(),3);
                     }
                     for(int cx=260;cx<=262;cx++)for(int cz=260;cz<=262;cz++)
                      world.setChunkForced(cx,cz,false);
                   })
                   .thenSucceed();'''
assert s.count(old)==1, f"WIRELESS_FANOUT_CI anchor drift: {s.count(old)}"
assert "WIRELESS_ONE_TX_EIGHT_RX_V1" not in s
target.write_text(s.replace(old,new,1),encoding="utf-8")
print("WIRELESS_ONE_TX_EIGHT_RX_V1 GAME TEST INJECTED")
