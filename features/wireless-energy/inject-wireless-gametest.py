#!/usr/bin/env python3
"""Attach live no-cheat wireless FE proof to the existing real-world GameTest.

Test-only class is removed before packaging. Source and sink are real Energy Cells;
the transmitter and receiver are separated by air, not cables. Transactions are
tested against an actual placed transmitter, including rollback.
"""
from pathlib import Path
import os
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text()
marker="WIRELESS_CROSSDIM_READY_FE_GAMETEST_V1"
assert marker not in s
anchor='check(controllerRt!=null&&driveRt==controllerRt,"NETWORK merge rebinds real StorageDrive through bundles");'
assert s.count(anchor)==1
position=s.index(anchor)
i=s.index(".thenSucceed();",position)
assert 0<i-position<900, "Network GameTest flow drift"
addition=r'''.thenExecuteAfter(2,()->{
                    // WIRELESS_CROSSDIM_READY_FE_GAMETEST_V1: real FE machines with an air gap
                    // use exactly the same cross-dimension server source registry.
                    for(int x=0;x<10;x++)helper.getLevel().setBlock(helper.absolutePos(new BlockPos(x,1,1)),Blocks.AIR.defaultBlockState(),3);
                    BlockPos source=helper.absolutePos(new BlockPos(0,1,1));
                    BlockPos energyBridge=helper.absolutePos(new BlockPos(1,1,1));
                    BlockPos transmitter=helper.absolutePos(new BlockPos(2,1,1));
                    BlockPos receiver=helper.absolutePos(new BlockPos(7,1,1));
                    BlockPos destination=helper.absolutePos(new BlockPos(8,1,1));
                    helper.getLevel().setBlock(source,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                    helper.getLevel().setBlock(energyBridge,ObsidianNetwork.CONDUIT_BUNDLE.get().defaultBlockState(),3);
                    var bridge=(ConduitBundleBlockEntity)helper.getLevel().getBlockEntity(energyBridge);
                    check(bridge!=null,"WIRELESS real energy conduit bridge");
                    if(!bridge.has(ConduitBundleBlockEntity.Layer.ENERGY))
                     check(bridge.add(ConduitBundleBlockEntity.Layer.ENERGY),"WIRELESS conduit ENERGY layer installed");
                    helper.getLevel().setBlock(transmitter,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                    helper.getLevel().setBlock(receiver,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
                    helper.getLevel().setBlock(destination,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                    var send=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(source);
                    var txBe=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)helper.getLevel().getBlockEntity(transmitter);
                    var rxBe=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)helper.getLevel().getBlockEntity(receiver);
                    var sink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(destination);
                    check(send!=null&&sink!=null&&txBe!=null&&rxBe!=null,"WIRELESS actual block entities");
                    check(txBe.isTransmitter()&&!rxBe.isTransmitter(),"WIRELESS sender receiver identity");
                    int before=(int)txBe.stored();
                    try(var rollback=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                     check(txBe.energyHandler().insert(500,rollback)==500,"WIRELESS simulated buffer insert");
                    }
                    check(txBe.stored()==before,"WIRELESS aborted FE insert rolls back exactly");
                    try(var fill=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                     check(send.energyHandler(null).insert(8000,fill)==8000,"WIRELESS real machine source prefilled");
                     fill.commit();
                    }
                    send.cycleSide(Direction.EAST.get3DDataValue());
                    check(send.sideMode(Direction.EAST)==dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.OUTPUT,"WIRELESS source output face");
                    check(sink.sideMode(Direction.WEST)==dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.INPUT,"WIRELESS sink input face");
                   })
                   .thenExecuteAfter(35,()->{
                    var send=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(0,1,1)));
                    var sink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(8,1,1)));
                    var txBe=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)helper.getLevel().getBlockEntity(helper.absolutePos(new BlockPos(2,1,1)));
                    check(send!=null&&sink!=null&&txBe!=null,"WIRELESS runtime remains present");
                    check(sink.stored()>0,"WIRELESS FE reached separated machine through named wireless network");
                    check(send.stored()+txBe.stored()+sink.stored()==8000,"WIRELESS FE conservation exactly 8000 after transport");
                    System.out.println("WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS");
                   })
                   '''
s=s[:i]+addition+s[i:]
p.write_text(s)
print("WIRELESS_GAMETEST_INJECTION_V1 PASS")
