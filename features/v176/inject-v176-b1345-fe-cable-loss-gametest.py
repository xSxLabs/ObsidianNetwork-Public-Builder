#!/usr/bin/env python3
"""B1345 full server runtime test of Powerbank incoming cable plus FE loop.

Runs after B1324DirectEnergyGameTests is injected (CI-only source); exercises
automatic link repair, actual EnergyCell -> EnergyCable -> Powerbank INPUT,
shared network OUTPUT cable looping back to its own INPUT, and no 2b FE loss.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/B1324DirectEnergyGameTests.java"
s=p.read_text("utf-8")

def one(old,new,label):
 global s
 n=s.count(old)
 assert n==1,("B1345_GAME_TEST_DRIFT",label,n)
 s=s.replace(old,new,1)

one("""    "b1324_true_demand_zero_buffer"),
    new DirectTest""",
"""    "b1324_true_demand_zero_buffer"),
    new DirectTest""","keep_baseline") if False else None
one('  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",\n    "b1324_powerbank_full_sink_zero_output"),',
'''  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1345_cable_powerbank_recharge_no_fe_cycle"),
    new PowerbankCableCycleTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(
      environment,STRUCTURE,200,0,true,Rotation.NONE)));
  event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork",
    "b1324_powerbank_full_sink_zero_output"),''',"new_real_recharge_game_test")

one(' private static final class PowerbankIdleTest extends GameTestInstance {',
r''' // Every action below is on the actual server and actual EnergyHandlers.
 // No direct insert to the Powerbank is used to prove cable charging.
 private static final class PowerbankCableCycleTest extends GameTestInstance {
  PowerbankCableCycleTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){
   super(data);
  }
  @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
   throw new UnsupportedOperationException("B1345 CI-only cable Powerbank test");
  }
  @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
   return Component.literal("Real cable Powerbank input and zero FE feedback");
  }
  @Override public void run(GameTestHelper h){
   ServerLevel world=(ServerLevel)h.getLevel();
   BlockPos origin=h.absolutePos(new BlockPos(3,1,3));
   BlockPos controller=origin.offset(1,1,0);
   BlockPos input=origin.offset(0,1,1);
   BlockPos output=origin.offset(2,1,1);
   BlockPos sourcePos=origin.offset(-2,1,1);
   BlockPos inputCable=origin.offset(-1,1,1);
   BlockPos outputCable=origin.offset(3,1,1);
   for(int x=0;x<3;x++)for(int y=0;y<3;y++)for(int z=0;z<3;z++){
    BlockPos at=origin.offset(x,y,z);
    if(x==1&&y==1&&z==1)
     world.setBlock(at,ObsidianNetwork.POWERBANK_CELL.get().defaultBlockState(),3);
    else if(at.equals(controller))
     world.setBlock(at,ObsidianNetwork.POWERBANK_CONTROLLER.get().defaultBlockState(),3);
    else if(at.equals(input))
     world.setBlock(at,ObsidianNetwork.POWERBANK_INPUT.get().defaultBlockState(),3);
    else if(at.equals(output))
     world.setBlock(at,ObsidianNetwork.POWERBANK_OUTPUT.get().defaultBlockState(),3);
    else world.setBlock(at,ObsidianNetwork.POWERBANK_CASING.get().defaultBlockState(),3);
   }
   // Recreate a shared loop physically: output cable returns around the
   // bank shell to its own input cable and the upstream Energy Cell.
   int[][] loop={{-1,1,1},{-1,1,2},{-1,1,3},{0,1,3},
                 {1,1,3},{2,1,3},{3,1,3},{3,1,2},{3,1,1}};
   for(int[] c:loop)world.setBlock(origin.offset(c[0],c[1],c[2]),
     ObsidianNetwork.ENERGY_CABLE.get().defaultBlockState(),3);
   world.setBlock(sourcePos,ObsidianNetwork.ULTIMATE_ENERGY_CELL.get().defaultBlockState(),3);
   var source=(EnergyCellBlockEntity)world.getBlockEntity(sourcePos);
   var bank=(dev.obsidiannetwork.powerbank.PowerbankBlockEntity)world.getBlockEntity(controller);
   if(source==null||bank==null)throw new IllegalStateException("B1345 real FE actors missing");
   // Source cell has OUTPUT EAST, INPUT on remaining sides. The old code
   // accepted back its own outgoing FE through west/north cable routes.
   source.cycleSide(Direction.EAST.get3DDataValue());
   long funded=0;
   for(int i=0;i<5;i++){
    try(var tx=Transaction.openRoot()){
     int inserted=source.energyHandler(null).insert(5_000_000,tx);
     if(inserted<=0)throw new IllegalStateException("B1345 source funding failed");
     tx.commit();funded+=inserted;
    }
   }
   final long initial=funded;
   // Deliberately DO NOT revalidate() manually: the prior version only
   // recovered INPUT/OUTPUT links after breaking/replacing the controller.
   h.startSequence().thenExecuteAfter(60,()->{
    if(!bank.xsxNetworkFormed())
     throw new IllegalStateException("B1345 bank failed automatic reload/relink");
    long bankFe=bank.xsxNetworkStoredFe(), sourceFe=source.stored();
    if(bankFe<=0L)throw new IllegalStateException(
      "B1345 energy cable fills cells but NOT Powerbank INPUT");
    if(bankFe+sourceFe!=initial)
     throw new IllegalStateException("B1345 FE lost: before="+initial+
       " bank="+bankFe+" source="+sourceFe);
    System.out.println("B1345_POWERBANK_REAL_CABLE_INPUT_RELINK_PASS bank="+bankFe);
    System.out.println("B1345_ENERGY_CELL_NO_5M_PINGPONG_PASS source="+sourceFe);
    // Replace upstream generator with air: there is zero available input,
    // and no consuming machines. Powerbank reserve must not leak to the
    // returned output cable while no consumer can accept it.
    world.setBlock(sourcePos,Blocks.AIR.defaultBlockState(),3);
    long reserve=bank.xsxNetworkStoredFe();
    h.startSequence().thenExecuteAfter(40,()->{
     if(bank.xsxNetworkStoredFe()!=reserve)
      throw new IllegalStateException("B1345 idle Powerbank lost FE "+reserve+
       " -> "+bank.xsxNetworkStoredFe());
     if(bank.xsxNetworkOutputFePerTick()!=0L)
      throw new IllegalStateException("B1345 phantom Powerbank output on empty loop");
     System.out.println("B1345_IDLE_FE_2B_BUDGET_NO_RETURN_LEAK_PASS");
    }).thenSucceed();
   });
  }
 }
 private static final class PowerbankIdleTest extends GameTestInstance {''',
"real_cable_loop_game_test")
# Add another 2b FE to existing 2m fully-charged sink test,
# AFTER old baseline setup has been validated.
one('   final long before=bank.xsxNetworkStoredFe();',
'''   // B1345_2B_NO_DRAIN: simulate the user switching the source off with
   // 2 billion FE still stored; all real sinks are already full.
   try(var huge=Transaction.openRoot()){
    if(inlet.energyPort().insert(1_998_000_000,huge)!=1_998_000_000)
     throw new IllegalStateException("B1345 Powerbank 2b fixture charge rejected");
    huge.commit();
   }
   if(bank.xsxNetworkStoredFe()!=2_000_000_000L)
    throw new IllegalStateException("B1345 cannot establish 2b FE reserve");
   final long before=bank.xsxNetworkStoredFe();''',
"two_billion_unchanged")
one('System.out.println("B1324_POWERBANK_FULL_SINK_REAL_TICK_ZERO_OUTPUT_PASS");',
'''System.out.println("B1324_POWERBANK_FULL_SINK_REAL_TICK_ZERO_OUTPUT_PASS");
    System.out.println("B1345_POWERBANK_TWO_BILLION_FE_NO_IDLE_LOSS_PASS");''',
"two_billion_marker")
assert "B1345_POWERBANK_REAL_CABLE_INPUT_RELINK_PASS" in s
assert "B1345_POWERBANK_TWO_BILLION_FE_NO_IDLE_LOSS_PASS" in s
p.write_text(s,encoding="utf-8")
print("B1345_REAL_CABLE_RECHARGE_CYCLE_AND_2B_FE_SERVER_GAMETEST_INJECTED")
