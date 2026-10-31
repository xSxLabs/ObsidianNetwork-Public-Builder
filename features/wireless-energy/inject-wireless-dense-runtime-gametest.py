#!/usr/bin/env python3
"""CI-only loaded receiver + transmitter stress probe, 10 / 50 / 100 live devices.

Add AFTER Curios runtime injection to the same real-server StateMachineTest.
The probe warms the isolated forced-chunk Overworld fixture before testing server-tick transfers and verifies conservation for EVERY
wireless sender / receiver / real EnergyCell at each density. Chunk tickets
belong solely to the test and are all released. We report only density and
energy balances: these are NOT controlled server MSPT/p95 or spark readings.
"""
import os
from pathlib import Path

file=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=file.read_text()
anchor='''                     System.out.println("WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS");
                      }catch(ReflectiveOperationException error){'''
assert s.count(anchor)==1, "wireless dense test source drift (Curios anchor)"
assert "WIRELESS_DENSE_REAL_SERVER_100_V1" not in s
# Replace the terminal lambda, *after* Curios's conditional test, not inside it.
end='''                     }
                   })
                   .thenSucceed();'''
assert s.count(end)==1, "wireless dense test must attach after final Curios lambda"
extra=r'''                     }
                   })
                   .thenExecuteAfter(2,()->{
                     // Isolated dense Overworld fixture: 3x3 chunks, real BEs and
                     // FE capabilities. Wireless production never adds tickets.
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense Overworld world exists");
                     for(int cx=260;cx<=262;cx++)for(int cz=260;cz<=262;cz++){
                      world.setChunkForced(cx,cz,true);
                      world.getChunk(cx,cz); // CI fixture: synchronously materialize.
                     }
                     System.out.println("WIRELESS_DENSE_TICKET_WARMUP_V3 START B574_160T");
                   })
                   .thenExecuteAfter(160,()->{
                     // B574_DENSE_CHUNK_TICK_WARMUP: the Curios-installed JVM can queue
                     // distant forced-chunk ticking promotion substantially longer.
                     // Keep the true 10/50/100 loaded-BE FE transfer test strict:
                     // no synthetic transfer, no skipping assertions and no rate cuts.
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense warmed world present");
                     for(int index=0;index<10;index++){
                      var sourcePos=new BlockPos(4160+(index%10)*3,80,4161+(index/10)*3);
                      var receiverPos=new BlockPos(sourcePos.getX(),80,sourcePos.getZ()-1);
                      var cellPos=receiverPos.east();
                      world.setBlock(sourcePos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                      world.setBlock(receiverPos,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
                      world.setBlock(cellPos,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                      var denseSender=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(sourcePos);
                      var receiver=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(receiverPos);
                      var cell=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)world.getBlockEntity(cellPos);
                      check(denseSender!=null&&receiver!=null&&cell!=null,
                       "WIRELESS dense 10 real FE devices");
                      check(cell.sideMode(Direction.WEST)==dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.INPUT,
                       "WIRELESS dense sink must accept WEST FE");
                      for(int batch=0;batch<16;batch++){
                       try(var funding=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                        check(denseSender.energyHandler().insert(16000,funding)==16000,
                         "WIRELESS dense TX 256000 FE funding");
                        funding.commit();
                       }
                      }
                     }
                     System.out.println("WIRELESS_DENSE_REAL_SERVER_10_V1 ARMED B574_120T_TRANSFER_WINDOW");
                   })
                   .thenExecuteAfter(120,()->{
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense world still exists at 10");
                     long total=0,received=0;
                     for(int index=0;index<10;index++){
                      var pos=new BlockPos(4160+(index%10)*3,80,4161+(index/10)*3);
                      var denseSender=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(pos);
                      // Sender is at z+1; sink at receiver.east() = sender.north().east().
                      var denseSink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)world.getBlockEntity(pos.north().east());
                      check(denseSender!=null&&denseSink!=null,"WIRELESS dense 10 valid FE entities");
                      total+=denseSender.stored()+denseSink.stored();received+=denseSink.stored();
                     }
                     long supply=dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      world.getServer(),"obsidiannetwork:main");
                     System.out.println("WIRELESS_DENSE_10_DIAG_V2 total="+total+" expected="+(10L*256000)
                       +" received="+received+" senders="+(total-received)
                       +" indexedAvailable="+supply+" gameTime="+world.getGameTime());
                     // Leave FE untouched on failure: the diagnostic is read-only.
                     if(received==0){
                      var rp=new BlockPos(4160,80,4160);
                      var rx=world.getBlockEntity(rp);
                      var cap=world.getCapability(
                       net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
                       rp.east(),Direction.WEST);
                      System.out.println("WIRELESS_DENSE_TICK_DIAG_V3 receiver="+(rx!=null)
                       +" cellCapability="+(cap!=null)
                       +" loaded="+world.hasChunkAt(rp)
                       +" gameTime="+world.getGameTime());
                     }
                     check(total==10L*256000&&received>0,"WIRELESS dense 10 conservation/transfer");
                     System.out.println("WIRELESS_DENSE_REAL_SERVER_10_V1 PASS total="+total+" sink="+received);
                     for(int index=10;index<50;index++){
                      var txPos=new BlockPos(4160+(index%10)*3,80,4161+(index/10)*3);
                      var rxPos=txPos.north();
                      world.setBlock(txPos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                      world.setBlock(rxPos,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
                      world.setBlock(rxPos.east(),ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                      var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(txPos);
                      check(tx!=null&&world.getBlockEntity(rxPos.east()) instanceof dev.obsidiannetwork.blockentity.EnergyCellBlockEntity,
                       "WIRELESS dense 50 actual endpoint entities");
                      for(int b=0;b<16;b++)try(var tr=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                       check(tx.energyHandler().insert(16000,tr)==16000,"WIRELESS dense 50 sender funding");
                       tr.commit();
                      }
                     }
                   })
                   .thenExecuteAfter(20,()->{
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense world still exists at 50");
                     long total=0,received=0;
                     for(int i=0;i<50;i++){
                      var p=new BlockPos(4160+(i%10)*3,80,4161+(i/10)*3);
                      var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(p);
                      var cell=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)world.getBlockEntity(p.north().east());
                      check(tx!=null&&cell!=null,"WIRELESS dense 50 endpoints present");
                      total+=tx.stored()+cell.stored();received+=cell.stored();
                     }
                     check(total==50L*256000&&received>0,"WIRELESS dense 50 exact conservation");
                     System.out.println("WIRELESS_DENSE_REAL_SERVER_50_V1 PASS total="+total+" sink="+received);
                     for(int i=50;i<100;i++){
                      var p=new BlockPos(4160+(i%10)*3,80,4161+(i/10)*3);
                      world.setBlock(p,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                      world.setBlock(p.north(),ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
                      world.setBlock(p.north().east(),ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
                      var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(p);
                      check(tx!=null,"WIRELESS dense 100 sender exists");
                      for(int b=0;b<16;b++)try(var tr=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                       check(tx.energyHandler().insert(16000,tr)==16000,"WIRELESS dense 100 TX funding");
                       tr.commit();
                      }
                     }
                   })
                   .thenExecuteAfter(20,()->{
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense world still exists at 100");
                     long total=0,received=0;
                     for(int i=0;i<100;i++){
                      var p=new BlockPos(4160+(i%10)*3,80,4161+(i/10)*3);
                      var tx=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)world.getBlockEntity(p);
                      var cell=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)world.getBlockEntity(p.north().east());
                      check(tx!=null&&cell!=null,"WIRELESS dense 100 actual endpoints");
                      total+=tx.stored()+cell.stored();received+=cell.stored();
                     }
                     check(total==100L*256000&&received>0,
                      "WIRELESS dense 100 exact conservation and live FE transfer");
                     System.out.println("WIRELESS_DENSE_REAL_SERVER_100_V1 PASS total="+total+" sink="+received);
                     // Remove the loaded transmitter sources; idle receivers must not
                     // ghost-transfer FE. Use all 100 real BEs, still in loaded chunks.
                     for(int i=0;i<100;i++){
                      var p=new BlockPos(4160+(i%10)*3,80,4161+(i/10)*3);
                      world.setBlock(p,Blocks.AIR.defaultBlockState(),3);
                     }
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      world.getServer(),"obsidiannetwork:main")==0,
                      "WIRELESS dense sender registry retains deleted sources");
                   })
                   .thenExecuteAfter(10,()->{
                     var world=helper.getLevel();
                     check(world!=null,"WIRELESS dense idle world still exists");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      world.getServer(),"obsidiannetwork:main")==0,
                      "WIRELESS 100 idle receivers wrongly reactivated absent source");
                     for(int i=0;i<100;i++){
                      var p=new BlockPos(4160+(i%10)*3,80,4161+(i/10)*3);
                      world.setBlock(p.north(),Blocks.AIR.defaultBlockState(),3);
                      world.setBlock(p.north().east(),Blocks.AIR.defaultBlockState(),3);
                     }
                     for(int cx=260;cx<=262;cx++)for(int cz=260;cz<=262;cz++)
                      world.setChunkForced(cx,cz,false);
                     System.out.println("WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS");
                   })
                   .thenSucceed();'''
# Only one tail must be replaced to avoid insertion in the wrong method.
s=s.replace(end,extra,1)
file.write_text(s)
print("WIRELESS_DENSE_REAL_SERVER_10_50_100_V1 INJECTED")
