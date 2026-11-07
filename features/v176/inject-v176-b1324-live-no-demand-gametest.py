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
