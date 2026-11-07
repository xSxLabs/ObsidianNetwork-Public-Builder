#!/usr/bin/env python3
"""B1376 live 5x5x5 in-mod Reactor -> Energy Cables -> Powerbank -> FE consumer.
NeoForge GameTest only. Never ship its source or structure in the production JAR.
"""
import gzip
import os
import struct
from pathlib import Path

src=Path(os.environ["V1_SOURCE_ROOT"])
java=src/"dev/obsidiannetwork/build103/B1376ReactorBankGameTests.java"
assert not java.exists(),("B1376_JAVA_TEST_COLLISION",java)
java.parent.mkdir(parents=True,exist_ok=True)
java.write_text(r'''package dev.obsidiannetwork.build103;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.EnergyCellBlockEntity;
import dev.obsidiannetwork.powerbank.PowerbankBlockEntity;
import dev.obsidiannetwork.reactor.ReactorControllerBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestInstance;
import net.minecraft.gametest.framework.TestData;
import net.minecraft.gametest.framework.TestEnvironmentDefinition;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.transfer.transaction.Transaction;

@EventBusSubscriber(modid="obsidiannetwork")
public final class B1376ReactorBankGameTests {
 private static final Identifier ENV=Identifier.fromNamespaceAndPath(
   "obsidiannetwork","b1376_reactor_environment");
 private static final Identifier STRUCTURE=Identifier.fromNamespaceAndPath(
   "obsidiannetwork","b1376_reactor_energy");
 @SubscribeEvent public static void register(RegisterGameTestsEvent event){
  var env=event.registerEnvironment(ENV,new TestEnvironmentDefinition.AllOf(java.util.List.of()));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1376_real_reactor_bank_automatic_transfer_and_restart"),
    new RealReactorBankTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      env,STRUCTURE,300,0,true,Rotation.NONE)));
 }
 private static final class RealReactorBankTest extends GameTestInstance {
  RealReactorBankTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){
   super(data);
  }
  @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
   throw new UnsupportedOperationException("B1376 CI-only reactor FE test");
  }
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Fueled xSxLabs Reactor POWER -> cable -> bank -> cable -> consumer");
  }
  private static void fund(EnergyCellBlockEntity cell,long amount){
   while(amount>0){
    int want=(int)Math.min((long)Integer.MAX_VALUE,amount);
    try(var tx=Transaction.openRoot()){
     int accepted=cell.energyHandler(null).insert(want,tx);
     if(accepted<=0)throw new IllegalStateException("B1376 cannot fill FE consumer");
     tx.commit();
     amount-=accepted;
    }
   }
  }
  @Override public void run(GameTestHelper h){
   ServerLevel w=(ServerLevel)h.getLevel();
   BlockPos origin=h.absolutePos(new BlockPos(0,0,0));
   // Actual 5x5x5 Reactor: complete shell, 3 required ports, an
   // complete vertical fuel column (y=2..4), fuel, and a water bucket.
   for(int x=1;x<=5;x++)for(int y=1;y<=5;y++)for(int z=1;z<=5;z++){
    BlockPos p=origin.offset(x,y,z);
    boolean outer=x==1||x==5||y==1||y==5||z==1||z==5;
    if(!outer)w.setBlock(p,x==3&&y>=2&&y<=4&&z==3?
       ObsidianNetwork.REACTOR_FUEL_ASSEMBLY.get().defaultBlockState():
       Blocks.AIR.defaultBlockState(),3);
    else if(x==1&&y==2&&z==1)
     w.setBlock(p,ObsidianNetwork.REACTOR_CONTROLLER.get().defaultBlockState(),3);
    else if(x==1&&y==2&&z==2)
     w.setBlock(p,ObsidianNetwork.REACTOR_ITEM_PORT.get().defaultBlockState(),3);
    else if(x==1&&y==2&&z==3)
     w.setBlock(p,ObsidianNetwork.REACTOR_FLUID_PORT.get().defaultBlockState(),3);
    else if(x==5&&y==2&&z==3)
     w.setBlock(p,ObsidianNetwork.REACTOR_POWER_PORT.get().defaultBlockState(),3);
    else w.setBlock(p,ObsidianNetwork.REACTOR_CASING.get().defaultBlockState(),3);
   }
   // A real fuel column also requires its control rod on the top face.
   // Look up the mod-registered reactor rod, not a simulated/copper block.
   net.minecraft.world.level.block.Block controlRod=null;
   StringBuilder reactorBlocks=new StringBuilder();
   for(var candidate:net.minecraft.core.registries.BuiltInRegistries.BLOCK){
    var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(candidate);
    if(!id.getNamespace().equals("obsidiannetwork")||!id.getPath().contains("reactor"))continue;
    reactorBlocks.append(id.getPath()).append(",");
    if(id.getPath().contains("control")&&id.getPath().contains("rod"))
     controlRod=candidate;
   }
   if(controlRod==null)
    throw new IllegalStateException("B1378 reactor control rod not registered: "+reactorBlocks);
   w.setBlock(origin.offset(3,5,3),controlRod.defaultBlockState(),3);
   // Real 3x3x3 Powerbank with its actual INPUT/OUTPUT shell port entities.
   for(int x=8;x<=10;x++)for(int y=1;y<=3;y++)for(int z=2;z<=4;z++){
    BlockPos p=origin.offset(x,y,z);
    if(x==9&&y==2&&z==3)
     w.setBlock(p,ObsidianNetwork.POWERBANK_CELL.get().defaultBlockState(),3);
    else if(x==9&&y==2&&z==2)
     w.setBlock(p,ObsidianNetwork.POWERBANK_CONTROLLER.get().defaultBlockState(),3);
    else if(x==8&&y==2&&z==3)
     w.setBlock(p,ObsidianNetwork.POWERBANK_INPUT.get().defaultBlockState(),3);
    else if(x==10&&y==2&&z==3)
     w.setBlock(p,ObsidianNetwork.POWERBANK_OUTPUT.get().defaultBlockState(),3);
    else w.setBlock(p,ObsidianNetwork.POWERBANK_CASING.get().defaultBlockState(),3);
   }
   for(int x:new int[]{6,7,11,12})
    w.setBlock(origin.offset(x,2,3),ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState(),3);
   BlockPos sinkP=origin.offset(13,2,3);
   w.setBlock(sinkP,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
   var reactor=(ReactorControllerBlockEntity)w.getBlockEntity(origin.offset(1,2,1));
   var bank=(PowerbankBlockEntity)w.getBlockEntity(origin.offset(9,2,2));
   var inlet=(PowerbankBlockEntity)w.getBlockEntity(origin.offset(8,2,3));
   var sink=(EnergyCellBlockEntity)w.getBlockEntity(sinkP);
   if(reactor==null||bank==null||inlet==null||sink==null)
    throw new IllegalStateException("B1376 real reactor/bank/consumer block entities missing");
   var formed=reactor.revalidate(w);
   if(!formed.valid())throw new IllegalStateException("B1376 reactor formation "+formed.reason());
   reactor.setItem(0,new ItemStack(ObsidianNetwork.URANIUM_ROD.get()));
   reactor.setItem(1,new ItemStack(Items.WATER_BUCKET));
   final long[] bankIdle=new long[1], reactorIdle=new long[1];
   final long[] bankBeforeDemand=new long[1], bankBeforeRestart=new long[1];
   final long[] totalBeforeRestart=new long[1];
   h.startSequence().thenExecuteAfter(80,()->{
    if(!reactor.xsxNetworkFormed()||!bank.xsxNetworkFormed())
     throw new IllegalStateException("B1376 formed reactor or bank no longer connected");
    long produced=reactor.xsxNetworkStoredFe()+bank.xsxNetworkStoredFe()+sink.stored();
    if(produced<=0L||sink.stored()<=0L)
     throw new IllegalStateException("B1376 REAL reactor output did not reach consumer: "+
       "reactor="+reactor.xsxNetworkStoredFe()+" bank="+bank.xsxNetworkStoredFe()+
       " sink="+sink.stored()+" status="+reactor.status());
    System.out.println("B1376_REAL_REACTOR_CABLE_BANK_CONSUMER_PASS produced="+produced);
    // Stop the REAL reactor, not a simulated Energy Cell producer.
    reactor.xsxNetworkSetEnabled(false);
    fund(sink,sink.energyHandler(null).getCapacityAsLong()-sink.stored());
    try(var tx=Transaction.openRoot()){
     int accepted=inlet.energyPort().insert(2_000_000_000,tx);
     if(accepted!=2_000_000_000)
      throw new IllegalStateException("B1376 bank refused exactly 2B "+accepted);
     tx.commit();
    }
    bankIdle[0]=bank.xsxNetworkStoredFe();
    reactorIdle[0]=reactor.xsxNetworkStoredFe();
    if(bankIdle[0]<2_000_000_000L)
     throw new IllegalStateException("B1376 bank reserve smaller than 2B");
   }).thenExecuteAfter(40,()->{
    if(bank.xsxNetworkStoredFe()!=bankIdle[0]
       ||reactor.xsxNetworkStoredFe()!=reactorIdle[0])
     throw new IllegalStateException("B1376 lost reserve while reactor OFF and sink FULL: "+
       bankIdle[0]+" -> "+bank.xsxNetworkStoredFe());
    if(bank.xsxNetworkOutputFePerTick()!=0L)
     throw new IllegalStateException("B1376 phantom output to full consumer");
    System.out.println("B1376_REACTOR_OFF_TWO_BILLION_IDLE_NO_LOSS_PASS");
    // True consumer demand via a separate face of the downstream block.
    sink.cycleSide(Direction.EAST.get3DDataValue());
    var consumer=w.getCapability(Capabilities.Energy.BLOCK,sinkP,Direction.EAST);
    if(consumer==null)throw new IllegalStateException("B1376 consumer capability missing");
    try(var tx=Transaction.openRoot()){
     int drawn=consumer.extract(5_000_000,tx);
     if(drawn!=5_000_000)
      throw new IllegalStateException("B1376 could not consume 5M "+drawn);
     tx.commit();
    }
    bankBeforeDemand[0]=bank.xsxNetworkStoredFe();
   }).thenExecuteAfter(20,()->{
    if(bank.xsxNetworkStoredFe()!=bankBeforeDemand[0]-5_000_000L
       ||sink.stored()!=sink.energyHandler(null).getCapacityAsLong())
     throw new IllegalStateException("B1376 lost FE on bank discharge after reactor off: "+
       "bank="+bank.xsxNetworkStoredFe()+" sink="+sink.stored());
    System.out.println("B1376_REACTOR_OFF_BANK_TO_CONSUMER_PASS");
    bankBeforeRestart[0]=bank.xsxNetworkStoredFe();
    totalBeforeRestart[0]=reactor.xsxNetworkStoredFe()+
      bank.xsxNetworkStoredFe()+sink.stored();
    // Restart actual generator without replacing the Powerbank controller.
    reactor.xsxNetworkSetEnabled(true);
   }).thenExecuteAfter(80,()->{
    long sum=reactor.xsxNetworkStoredFe()+bank.xsxNetworkStoredFe()+sink.stored();
    if(sum<=totalBeforeRestart[0]||bank.xsxNetworkStoredFe()<=bankBeforeRestart[0])
     throw new IllegalStateException("B1376 reactor restart did not auto-recharge bank: "+
       "bank="+bank.xsxNetworkStoredFe()+" reactor="+reactor.xsxNetworkStoredFe()+
       " totalDelta="+(sum-totalBeforeRestart[0])+" status="+reactor.status());
    System.out.println("B1376_REACTOR_RESTART_BANK_AUTO_RECHARGE_PASS");
   }).thenSucceed();
  }
 }
}
''',encoding="utf-8")
template=src.parent/"resources/data/obsidiannetwork/structure/b1376_reactor_energy.nbt"
assert not template.exists(),("B1376_STRUCTURE_COLLISION",template)
template.parent.mkdir(parents=True,exist_ok=True)
def name(s):
 b=s.encode("utf-8")
 return struct.pack(">H",len(b))+b
def tag(t,n,payload):return bytes([t])+name(n)+payload
def integer(i):return struct.pack(">i",i)
root=tag(3,"DataVersion",integer(0))
root+=bytes([9])+name("size")+bytes([3])+integer(3)+integer(16)+integer(8)+integer(16)
root+=bytes([9])+name("palette")+bytes([10])+integer(1)+tag(8,"Name",name("minecraft:air"))+b"\x00"
root+=bytes([9])+name("blocks")+bytes([10])+integer(0)
root+=bytes([9])+name("entities")+bytes([10])+integer(0)
with gzip.open(template,"wb") as stream:
 stream.write(bytes([10])+name("")+root+b"\x00")
print("B1376_REAL_REACTOR_GAME_TEST_INJECTED")
