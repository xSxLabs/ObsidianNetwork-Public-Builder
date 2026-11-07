#!/usr/bin/env python3
"""B1355 real server FE tests, isolated to the Powerbank branch.

Do not import the B1324 wireless buffer rewrite. Place CI-only NeoForge
GameTests in existing build103 test namespace and remove before distributable
JAR. Prove a single physical EnergyCell cannot clone FE via two facades, and
prove a real charged EnergyCell simultaneously fills a Powerbank which feeds
a distinct empty EnergyCell through two separate cables. Finally switch off
the source, fill receiver and verify 2 billion FE idle for 40 server ticks.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"build103/B1355EnergyGameTests.java"
assert not p.exists(),("B1355_GAME_TEST_COLLISION",p)
# Unique CI-only environment key: Build103GameTests already owns build103_env.
# Re-registering that key aborts NeoForge before any energy test executes.
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''package dev.obsidiannetwork.build103;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.EnergyCellBlockEntity;
import dev.obsidiannetwork.powerbank.PowerbankBlockEntity;
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
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.transfer.transaction.Transaction;

@EventBusSubscriber(modid="obsidiannetwork")
public final class B1355EnergyGameTests {
 private static final Identifier ENV=Identifier.fromNamespaceAndPath(
   "obsidiannetwork","b1355_energy_env");
 private static final Identifier STRUCTURE=Identifier.fromNamespaceAndPath(
   "obsidiannetwork","build103_empty");
 @SubscribeEvent public static void register(RegisterGameTestsEvent event){
  var env=event.registerEnvironment(ENV,
    new TestEnvironmentDefinition.AllOf(java.util.List.of()));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1355_physical_energy_cell_same_transaction_rollback"),
    new CellIdentityTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      env,STRUCTURE,140,0,true,Rotation.NONE)));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1355_cell_to_bank_to_cell_while_charging"),
    new BankLoadTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      env,STRUCTURE,220,0,true,Rotation.NONE)));
 }
 private abstract static class Base extends GameTestInstance {
  Base(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){super(data);}
  @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
   throw new UnsupportedOperationException("B1355 CI-only FE test");
  }
 }
 private static void fund(EnergyCellBlockEntity cell,long amount) {
  while(amount>0L){
   int want=(int)Math.min((long)Integer.MAX_VALUE,amount);
   try(var tx=Transaction.openRoot()){
    int accepted=cell.energyHandler(null).insert(want,tx);
    if(accepted<=0)throw new IllegalStateException("B1355 could not fund Energy Cell");
    tx.commit();
    amount-=accepted;
   }
  }
 }
 private static final class CellIdentityTest extends Base {
  CellIdentityTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> d){super(d);}
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Cell's physical buffer one journal across both faces");
  }
  @Override public void run(GameTestHelper h){
   var world=(ServerLevel)h.getLevel();
   var p=h.absolutePos(new BlockPos(4,1,4));
   world.setBlock(p,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
   var cell=(EnergyCellBlockEntity)world.getBlockEntity(p);
   if(cell==null)throw new IllegalStateException("B1355 cell missing");
   fund(cell,25_000_000L);
   cell.cycleSide(Direction.EAST.get3DDataValue());
   long initial=cell.stored();
   var east=world.getCapability(Capabilities.Energy.BLOCK,p,Direction.EAST);
   var west=world.getCapability(Capabilities.Energy.BLOCK,p,Direction.WEST);
   if(east==null||west==null)throw new IllegalStateException("B1355 actual side capabilities missing");
   // Transaction A: extract output then try to insert into another INPUT face
   // of the same physical cell. Must refuse and roll back, not clone FE.
   try(var rollback=Transaction.openRoot()){
    int drawn=east.extract(5_000_000,rollback);
    if(drawn<=0)throw new IllegalStateException("B1355 output refused");
    if(west.insert(drawn,rollback)!=0)
     throw new IllegalStateException("B1355 self-charge accepted across faces");
   }
   if(cell.stored()!=initial)
    throw new IllegalStateException("B1355 rollback lost FE "+initial+" -> "+cell.stored());
   // Transaction B: test opposite ordering on same root transaction.
   try(var rollback=Transaction.openRoot()){
    int received=west.insert(2_000_000,rollback);
    // Even a valid same-buffer insert/extract must remain reversible.
    // This transaction intentionally aborts, so exact starting FE is required.
    if(received>0)east.extract(received,rollback);
   }
   if(cell.stored()!=initial)
    throw new IllegalStateException("B1355 opposite-order rollback changed FE");
   // B1375: NeoForge reopens pooled root transaction objects. After an
   // aborted self-transfer the next INDEPENDENT root must be able to charge,
   // and extracting in a committed root must not lock out later charging.
   try(var fresh=Transaction.openRoot()){
    int accepted=west.insert(1_000_000,fresh);
    if(accepted!=1_000_000)throw new IllegalStateException(
       "B1375 cell input blocked after earlier root rollback "+accepted);
    fresh.commit();
   }
   if(cell.stored()!=initial+1_000_000L)
    throw new IllegalStateException("B1375 cell committed root charge missing");
   try(var fresh=Transaction.openRoot()){
    int taken=east.extract(1_000_000,fresh);
    if(taken!=1_000_000)throw new IllegalStateException(
       "B1375 cell committed root extraction blocked "+taken);
    fresh.commit();
   }
   if(cell.stored()!=initial)
    throw new IllegalStateException("B1375 cell conserved FE after root reuse");
   System.out.println("B1375_ENERGY_CELL_REUSED_ROOT_PASS");
   System.out.println("B1355_ONE_PHYSICAL_CELL_SEVEN_FACES_ROLLBACK_PASS");
   h.succeed();
  }
 }
 private static final class BankLoadTest extends Base {
  BankLoadTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> d){super(d);}
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Real EnergyCell -> cable -> Powerbank -> cable -> consumer, then no idle drain");
  }
  @Override public void run(GameTestHelper h){
   var w=(ServerLevel)h.getLevel();
   var o=h.absolutePos(new BlockPos(3,1,3));
   var cp=o.offset(1,1,0);
   var ip=o.offset(0,1,1);
   var op=o.offset(2,1,1);
   var sourceP=o.offset(-2,1,1);
   var sourceCable=o.offset(-1,1,1);
   var sinkCable=o.offset(3,1,1);
   var sinkP=o.offset(4,1,1);
   for(int x=0;x<3;x++)for(int y=0;y<3;y++)for(int z=0;z<3;z++){
    BlockPos p=o.offset(x,y,z);
    if(x==1&&y==1&&z==1)
     w.setBlock(p,ObsidianNetwork.POWERBANK_CELL.get().defaultBlockState(),3);
    else if(p.equals(cp))
     w.setBlock(p,ObsidianNetwork.POWERBANK_CONTROLLER.get().defaultBlockState(),3);
    else if(p.equals(ip))
     w.setBlock(p,ObsidianNetwork.POWERBANK_INPUT.get().defaultBlockState(),3);
    else if(p.equals(op))
     w.setBlock(p,ObsidianNetwork.POWERBANK_OUTPUT.get().defaultBlockState(),3);
    else w.setBlock(p,ObsidianNetwork.POWERBANK_CASING.get().defaultBlockState(),3);
   }
   w.setBlock(sourceP,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
   w.setBlock(sourceCable,ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState(),3);
   w.setBlock(sinkCable,ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState(),3);
   w.setBlock(sinkP,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
   var source=(EnergyCellBlockEntity)w.getBlockEntity(sourceP);
   var sink=(EnergyCellBlockEntity)w.getBlockEntity(sinkP);
   var bank=(PowerbankBlockEntity)w.getBlockEntity(cp);
   var inlet=(PowerbankBlockEntity)w.getBlockEntity(ip);
   if(source==null||sink==null||bank==null||inlet==null)
    throw new IllegalStateException("B1355 missing actual energy blocks");
   source.cycleSide(Direction.EAST.get3DDataValue());
   fund(source,25_000_000L);
   final long initial=source.stored();
   // No manual revalidate; tick must link the real multiblock.
   final long[] afterSupply=new long[1];
   final long[] afterDemandBank=new long[1];
   final long[] afterDemandSink=new long[1];
   final long[] bankBeforeRestore=new long[1];
   final long[] sinkBeforeRestore=new long[1];
   final EnergyCellBlockEntity[] restoredSource=new EnergyCellBlockEntity[1];
   h.startSequence().thenExecuteAfter(60,()->{
    if(!bank.xsxNetworkFormed())throw new IllegalStateException(
      "B1355 Powerbank did not link automatically");
    if(sink.stored()<=0)throw new IllegalStateException(
      "B1355 Powerbank output blocked despite live upstream FE");
    if(source.stored()+sink.stored()+bank.xsxNetworkStoredFe()!=initial)
     throw new IllegalStateException("B1355 network FE was not conserved: "+
       "source="+source.stored()+" bank="+bank.xsxNetworkStoredFe()+
       " sink="+sink.stored()+" initial="+initial);
    System.out.println("B1355_CELL_CABLE_POWERBANK_CABLE_LIVE_SINK_PASS sink="+sink.stored());
    // Simulate stopped reactor by actually removing producing source.
    w.setBlock(sourceP,Blocks.AIR.defaultBlockState(),3);
    // Fill real sink so its remaining capacity cannot count as demand.
    long capacity=sink.energyHandler(null).getCapacityAsLong();
    int loops=0;
    while(sink.stored()<capacity&&loops++<4096){
     try(var fill=Transaction.openRoot()){
      int n=sink.energyHandler(null).insert(
       (int)Math.min((long)Integer.MAX_VALUE,capacity-sink.stored()),fill);
      if(n<=0)throw new IllegalStateException("B1355 cannot fill sink");
      fill.commit();
     }
    }
    if(sink.stored()!=capacity)throw new IllegalStateException("B1355 sink not full");
    // Inspect controller link and true NeoForge INPUT capability before funding.
    System.out.println("B1355_IDLE_INPUT_DIAG bank="+bank.status()
      +" inlet="+inlet.status()+" inletMode="+inlet.mode()
      +" enabled="+bank.xsxNetworkEnabled()
      +" bankStored="+bank.xsxNetworkStoredFe()
      +" bankCapacity="+bank.xsxNetworkCapacityFe()
      +" inletAmount="+inlet.energyPort().getAmountAsLong()
      +" inletCapacity="+inlet.energyPort().getCapacityAsLong());
    // Fund exactly 2B stored FE on the controller via its real INPUT port.
    try(var charge=Transaction.openRoot()){
     int n=inlet.energyPort().insert(2_000_000_000,charge);
     if(n!=2_000_000_000)throw new IllegalStateException("B1355 2B Powerbank charge refused "+n);
     charge.commit();
    }
    // Follow a committed 2B INPUT with a SECOND real root transaction.
    // It must not inherit source marks from the previous pooled root.
    long beforeTopup=bank.xsxNetworkStoredFe();
    try(var topup=Transaction.openRoot()){
     int accepted=inlet.energyPort().insert(1_000_000,topup);
     if(accepted!=1_000_000)throw new IllegalStateException(
       "B1375 Powerbank reused root rejected next charge "+accepted);
     topup.commit();
    }
    if(bank.xsxNetworkStoredFe()!=beforeTopup+1_000_000L)
     throw new IllegalStateException("B1375 bank root reuse FE not committed");
    System.out.println("B1375_POWERBANK_REUSED_ROOT_INPUT_PASS");
    afterSupply[0]=bank.xsxNetworkStoredFe();
    if(afterSupply[0]<2_000_000_000L)
     throw new IllegalStateException("B1355 insufficient idle reserve "+afterSupply[0]);
   }).thenExecuteAfter(40,()->{
    if(bank.xsxNetworkStoredFe()!=afterSupply[0])
     throw new IllegalStateException("B1355 2B FE lost under zero demand: "+
       afterSupply[0]+" -> "+bank.xsxNetworkStoredFe());
    if(bank.xsxNetworkOutputFePerTick()!=0L)
     throw new IllegalStateException("B1355 phantom output "+bank.xsxNetworkOutputFePerTick());
    System.out.println("B1355_TWO_BILLION_FE_POWERBANK_SOURCE_OFF_FULL_SINK_PASS");
    // The reactor is still absent. Make actual downstream demand via the
    // Energy Cell's EAST OUTPUT, physically separate from cable WEST INPUT.
    sink.cycleSide(Direction.EAST.get3DDataValue());
    var consumer=w.getCapability(Capabilities.Energy.BLOCK,sinkP,Direction.EAST);
    if(consumer==null)throw new IllegalStateException("B1375 sink output missing");
    long full=sink.stored();
    try(var demand=Transaction.openRoot()){
     int used=consumer.extract(5_000_000,demand);
     if(used!=5_000_000)throw new IllegalStateException(
        "B1375 cannot create post-reactor-off demand "+used);
     demand.commit();
    }
    if(sink.stored()!=full-5_000_000L)
     throw new IllegalStateException("B1375 actual consumer demand mismatch");
    afterDemandBank[0]=bank.xsxNetworkStoredFe();
    afterDemandSink[0]=sink.stored();
   }).thenExecuteAfter(20,()->{
    // Must resume delivery FROM STORED FE even after producer vanishes.
    if(sink.stored()!=afterDemandSink[0]+5_000_000L)
     throw new IllegalStateException("B1375 Powerbank starved real load after reactor off: "+
       afterDemandSink[0]+" -> "+sink.stored());
    if(bank.xsxNetworkStoredFe()!=afterDemandBank[0]-5_000_000L)
     throw new IllegalStateException("B1375 FE lost or created during battery discharge: "+
       afterDemandBank[0]+" -> "+bank.xsxNetworkStoredFe());
    System.out.println("B1375_SOURCE_OFF_BANK_DISCHARGE_PASS");
    // Restart the producing cell in the SAME network without breaking or
    // placing the controller again. Verify source -> bank resumes naturally.
    w.setBlock(sourceP,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
    var resumed=(EnergyCellBlockEntity)w.getBlockEntity(sourceP);
    if(resumed==null)throw new IllegalStateException("B1375 restored reactor cell missing");
    restoredSource[0]=resumed;
    resumed.cycleSide(Direction.EAST.get3DDataValue());
    bankBeforeRestore[0]=bank.xsxNetworkStoredFe();
    sinkBeforeRestore[0]=sink.stored();
    fund(resumed,5_000_000L);
   }).thenExecuteAfter(30,()->{
    if(restoredSource[0]==null)throw new IllegalStateException("B1375 source reference absent");
    if(bank.xsxNetworkStoredFe()!=bankBeforeRestore[0]+5_000_000L
       ||restoredSource[0].stored()!=0L ||sink.stored()!=sinkBeforeRestore[0])
     throw new IllegalStateException("B1375 reactor restart failed to recharge bank: "+
       "bank="+bank.xsxNetworkStoredFe()+" before="+bankBeforeRestore[0]+
       " source="+restoredSource[0].stored()+
       " sink="+sink.stored()+" beforeSink="+sinkBeforeRestore[0]);
    System.out.println("B1375_REACTOR_RESTART_BANK_RECHARGE_PASS");
   }).thenSucceed();
  }
 }
}
''',encoding="utf-8")
print("B1355_REAL_CELL_BANK_LIVE_LOAD_AND_TWO_BILLION_IDLE_GAMETEST_INJECTED")
