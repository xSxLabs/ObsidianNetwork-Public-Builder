#!/usr/bin/env python3
"""CI-only real ServerLevel FE regression after zero-buffer conversion.

Unlike pre-B1324 tests, the transmitter/receiver MUST have zero stored FE.
Energy comes from real adjacent EnergyCells, and transfer only commits if
a real remote receiver-side cell accepts exactly the same amount.
No tests are shipped in the distributable jar.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"build103/B1324DirectEnergyGameTests.java"
assert not p.exists(),("B1324_TEST_ALREADY_PRESENT",p)
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''package dev.obsidiannetwork.build103;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.EnergyCellBlockEntity;
import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import dev.obsidiannetwork.wireless.WirelessEnergyRuntime;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestInstance;
import net.minecraft.gametest.framework.TestData;
import net.minecraft.gametest.framework.TestEnvironmentDefinition;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.neoforged.neoforge.transfer.transaction.Transaction;

@EventBusSubscriber(modid="obsidiannetwork")
public final class B1324DirectEnergyGameTests {
 private static final Identifier ENV=Identifier.fromNamespaceAndPath(
     "obsidiannetwork","build103_env");
 private static final Identifier STRUCTURE=Identifier.fromNamespaceAndPath(
     "obsidiannetwork","build103_empty");
 @SubscribeEvent public static void register(RegisterGameTestsEvent event){
  var environment=event.registerEnvironment(ENV,
    new TestEnvironmentDefinition.AllOf(java.util.List.of()));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1324_true_demand_zero_buffer"),
    new DirectTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      environment,STRUCTURE,200,0,true,Rotation.NONE)));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1324_powerbank_full_sink_zero_output"),
    new PowerbankIdleTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      environment,STRUCTURE,120,0,true,Rotation.NONE)));
 }
 private static final class PowerbankIdleTest extends GameTestInstance {
  PowerbankIdleTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){
   super(data);
  }
  @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
   throw new UnsupportedOperationException("B1324 CI-only Powerbank idle test");
  }
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Powerbank 2M FE must remain stored when all consumers full");
  }
  @Override public void run(GameTestHelper helper){
   ServerLevel world=(ServerLevel)helper.getLevel();
   BlockPos origin=helper.absolutePos(new BlockPos(3,1,3));
   BlockPos controlPos=origin.offset(1,1,0);
   BlockPos inputPos=origin.offset(0,1,1);
   BlockPos outputPos=origin.offset(2,1,1);
   BlockPos destination=outputPos.east();
   for(int x=0;x<3;x++)for(int y=0;y<3;y++)for(int z=0;z<3;z++){
    BlockPos p=origin.offset(x,y,z);
    if(x==1&&y==1&&z==1){
     // Final v1.7.6 multiblock requires a Powerbank Cell in the core.
     world.setBlock(p,ObsidianNetwork.POWERBANK_CELL.get().defaultBlockState(),3);
    }else if(p.equals(controlPos)){
     world.setBlock(p,ObsidianNetwork.POWERBANK_CONTROLLER.get().defaultBlockState(),3);
    }else if(p.equals(inputPos)){
     world.setBlock(p,ObsidianNetwork.POWERBANK_INPUT.get().defaultBlockState(),3);
    }else if(p.equals(outputPos)){
     world.setBlock(p,ObsidianNetwork.POWERBANK_OUTPUT.get().defaultBlockState(),3);
    }else{
     world.setBlock(p,ObsidianNetwork.POWERBANK_CASING.get().defaultBlockState(),3);
    }
   }
   var bank=(dev.obsidiannetwork.powerbank.PowerbankBlockEntity)world.getBlockEntity(controlPos);
   var inlet=(dev.obsidiannetwork.powerbank.PowerbankBlockEntity)world.getBlockEntity(inputPos);
   if(bank==null||inlet==null||!bank.revalidate(world).valid())
    throw new IllegalStateException("B1324 POWERBANK structure failed");
   try(var funding=Transaction.openRoot()){
    if(inlet.energyPort().insert(2_000_000,funding)!=2_000_000)
     throw new IllegalStateException("B1324 POWERBANK failed to accept real FE");
    funding.commit();
   }
   world.setBlock(destination,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
   var full=(EnergyCellBlockEntity)world.getBlockEntity(destination);
   if(full==null)throw new IllegalStateException("B1324 no full sink");
   long cap=full.energyHandler(null).getCapacityAsLong();
   int rounds=0;
   while(full.stored()<cap&&rounds++<4096){
    try(var fill=Transaction.openRoot()){
     int actual=full.energyHandler(null).insert((int)Math.min(
         Integer.MAX_VALUE,cap-full.stored()),fill);
     if(actual<=0)throw new IllegalStateException("B1324 sink refused its own fill");
     fill.commit();
    }
   }
   if(full.stored()!=cap||bank.xsxNetworkStoredFe()!=2_000_000)
    throw new IllegalStateException("B1324 cannot establish full sink fixture");
   final long before=bank.xsxNetworkStoredFe();
   // Bank still has an active OUTPUT port and no transmitter. A completely
   // filled sink must reject every push for 40 real server ticks.
   helper.startSequence().thenExecuteAfter(40,()->{
    if(bank.xsxNetworkStoredFe()!=before||full.stored()!=cap)
     throw new IllegalStateException("B1324 2M FE lost despite full Energy Cell");
    if(bank.xsxNetworkOutputFePerTick()!=0L)
     throw new IllegalStateException("B1324 phantom Powerbank OUTPUT while idle");
    System.out.println("B1324_POWERBANK_FULL_SINK_REAL_TICK_ZERO_OUTPUT_PASS");
   }).thenSucceed();
  }
 }
 private static final class DirectTest extends GameTestInstance {
  DirectTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){
   super(data);
  }
  @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
   throw new UnsupportedOperationException("B1324 CI-only zero FE buffer test");
  }
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Wireless direct FE, full sink 0 output, atomic rollback");
  }
  @Override public void run(GameTestHelper helper){
   ServerLevel level=(ServerLevel)helper.getLevel();
   BlockPos producer=helper.absolutePos(new BlockPos(1,1,1));
   BlockPos txPos=helper.absolutePos(new BlockPos(2,1,1));
   BlockPos rxPos=helper.absolutePos(new BlockPos(8,1,1));
   BlockPos sinkPos=helper.absolutePos(new BlockPos(9,1,1));
   level.setBlock(producer,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
   level.setBlock(txPos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
   EnergyCellBlockEntity source=(EnergyCellBlockEntity)level.getBlockEntity(producer);
   WirelessNetworkBlockEntity tx=(WirelessNetworkBlockEntity)level.getBlockEntity(txPos);
   if(source==null||tx==null)throw new IllegalStateException("B1324 no transmitter/source");
   try(var funding=Transaction.openRoot()){
    int received=source.energyHandler(null).insert(120000,funding);
    if(received<10000)throw new IllegalStateException("B1324 source funding");
    funding.commit();
   }
   source.cycleSide(Direction.EAST.get3DDataValue());
   long initial=source.stored();
   // No receiver and no sink: must refuse all energy (not buffer 64M FE).
   WirelessEnergyRuntime.register(tx);
   try(var idle=Transaction.openRoot()){
    if(tx.energyHandler().insert(2_000_000,idle)!=0)
     throw new IllegalStateException("B1324 ghost demand without receiver");
   }
   if(tx.stored()!=0||source.stored()!=initial)
    throw new IllegalStateException("B1324 TX retains or loses FE while idle");

   level.setBlock(rxPos,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
   level.setBlock(sinkPos,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
   WirelessNetworkBlockEntity receiver=(WirelessNetworkBlockEntity)level.getBlockEntity(rxPos);
   EnergyCellBlockEntity target=(EnergyCellBlockEntity)level.getBlockEntity(sinkPos);
   if(receiver==null||target==null)throw new IllegalStateException("B1324 no receiver/sink");
   WirelessEnergyRuntime.register(receiver);
   long preSource=source.stored(),preTarget=target.stored();
   try(var transfer=Transaction.openRoot()){
    int drawn=source.energyHandler(null).extract(3000,transfer);
    int accepted=tx.energyHandler().insert(drawn,transfer);
    if(drawn<=0||drawn!=accepted)
     throw new IllegalStateException("B1324 direct transfer rejected "+drawn+"/"+accepted);
    transfer.commit();
   }
   int committed=(int)(source.stored()-preSource);
   if(committed>=0||target.stored()-preTarget!=-committed
      ||tx.stored()!=0||receiver.stored()!=0)
    throw new IllegalStateException("B1324 exact balance / TX RX 0 FE failed");
   System.out.println("B1324_DIRECT_TRUE_DEMAND_FE_GAME_TEST_PASS transferred="+(-committed));

   long rollbackSource=source.stored(),rollbackTarget=target.stored();
   try(var aborted=Transaction.openRoot()){
    int extracted=source.energyHandler(null).extract(1000,aborted);
    if(extracted<=0||tx.energyHandler().insert(extracted,aborted)!=extracted)
     throw new IllegalStateException("B1324 abort setup no receiver");
    // Do not commit.
   }
   if(source.stored()!=rollbackSource||target.stored()!=rollbackTarget)
    throw new IllegalStateException("B1324 aborted FE transfer changed balances");
   System.out.println("B1324_ROLLBACK_NO_ENERGY_LOSS_GAME_TEST_PASS");

   // Fill the real sink, without touching either wireless block.
   long cap=target.energyHandler(null).getCapacityAsLong();
   int rounds=0;
   while(target.stored()<cap&&rounds++<4096){
    try(var fill=Transaction.openRoot()){
     int accepted=target.energyHandler(null).insert((int)Math.min(
       Integer.MAX_VALUE,cap-target.stored()),fill);
     if(accepted<=0)throw new IllegalStateException("B1324 full sink fixture stagnant");
     fill.commit();
    }
   }
   if(target.stored()!=cap)throw new IllegalStateException("B1324 unable to fill sink");
   long fullSource=source.stored();
   for(int attempt=0;attempt<50;attempt++){
    try(var full=Transaction.openRoot()){
     if(tx.energyHandler().insert(2_000_000,full)!=0)
      throw new IllegalStateException("B1324 FULL CONSUMER DRAIN");
    }
   }
   if(source.stored()!=fullSource||tx.stored()!=0||receiver.stored()!=0
       ||target.stored()!=cap)
    throw new IllegalStateException("B1324 IDLE FULL CONSUMER CONSERVATION");
   System.out.println("B1324_FULL_SINK_ZERO_FE_OUTPUT_GAME_TEST_PASS");

   // Cross-dimension no-buffer transfer: the Nether source is a real cell,
   // not a transmitter battery, and the remote Overworld receiver is a proxy.
   WirelessEnergyRuntime.unregister(tx);
   var nether=level.getServer().getLevel(net.minecraft.world.level.Level.NETHER);
   if(nether==null)throw new IllegalStateException("B1324 Nether level unavailable");
   BlockPos remoteSourcePos=new BlockPos(8,80,8);
   BlockPos remoteTransmitterPos=remoteSourcePos.east();
   int rxChunkX=remoteSourcePos.getX()>>4,rxChunkZ=remoteSourcePos.getZ()>>4;
   nether.setChunkForced(rxChunkX,rxChunkZ,true); // test-only fixture ticket
   nether.getChunkAt(remoteSourcePos);
   nether.setBlock(remoteSourcePos,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
   nether.setBlock(remoteTransmitterPos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
   var remoteSource=(EnergyCellBlockEntity)nether.getBlockEntity(remoteSourcePos);
   var remoteTx=(WirelessNetworkBlockEntity)nether.getBlockEntity(remoteTransmitterPos);
   if(remoteSource==null||remoteTx==null)
    throw new IllegalStateException("B1324 remote energy source unavailable");
   try(var remoteFund=Transaction.openRoot()){
    if(remoteSource.energyHandler(null).insert(10000,remoteFund)!=10000)
     throw new IllegalStateException("B1324 Nether source funding");
    remoteFund.commit();
   }
   remoteSource.cycleSide(Direction.EAST.get3DDataValue());
   WirelessEnergyRuntime.register(remoteTx);
   // Empty remote target replaces the now-full local sink.
   level.setBlock(sinkPos,Blocks.AIR.defaultBlockState(),3);
   level.setBlock(sinkPos,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
   var remoteTarget=(EnergyCellBlockEntity)level.getBlockEntity(sinkPos);
   if(remoteTarget==null)throw new IllegalStateException("B1324 remote target missing");
   long remoteInitial=remoteSource.stored();
   try(var remoteTransfer=Transaction.openRoot()){
    int drawn=WirelessEnergyRuntime.pull(level.getServer(),
      "obsidiannetwork:main",2000,remoteTransfer);
    if(drawn!=2000||remoteTarget.energyHandler(null).insert(drawn,remoteTransfer)!=drawn)
     throw new IllegalStateException("B1324 crossdim FE not delivered");
    remoteTransfer.commit();
   }
   if(remoteSource.stored()+remoteTarget.stored()!=remoteInitial
      ||remoteTx.stored()!=0||receiver.stored()!=0)
    throw new IllegalStateException("B1324 crossdim energy vanished or buffered");
   nether.setBlock(remoteTransmitterPos,Blocks.AIR.defaultBlockState(),3);
   nether.setBlock(remoteSourcePos,Blocks.AIR.defaultBlockState(),3);
   nether.setChunkForced(rxChunkX,rxChunkZ,false);
   System.out.println("B1324_CROSSDIM_REAL_SOURCE_NO_BUFFER_GAME_TEST_PASS");

   level.setBlock(sinkPos,Blocks.AIR.defaultBlockState(),3);
   level.setBlock(rxPos,Blocks.AIR.defaultBlockState(),3);
   level.setBlock(txPos,Blocks.AIR.defaultBlockState(),3);
   level.setBlock(producer,Blocks.AIR.defaultBlockState(),3);
   helper.succeed();
  }
 }
}
''',encoding="utf-8")
print("B1324_REAL_NEoFORGE_DIRECT_ATOMIC_FULL_SINK_SERVER_TEST_INJECTED")
