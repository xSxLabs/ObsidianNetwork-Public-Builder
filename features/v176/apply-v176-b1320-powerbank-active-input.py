#!/usr/bin/env python3
"""B1320 Powerbank active INPUT feed and same-controller feedback isolation.

The v1.7.6 Powerbank output actively pushes but its INPUT was passive only.
Energy cables are stateless pass-through; some generators do not push into a
passive port. Poll real connected producer capabilities at registered INPUT
ports (not at the controller) and transfer precisely what both handlers
actually accept inside a single root transaction.

The incoming cable proxy may find the SAME bank's OUTPUT first. During an
input-pull transaction make that one specific source ineligible, allowing
the cable traversal to reach the real external generator instead. Distinct
banks remain eligible. Preserve B1300 outgoing no-self-charge protection and
all 64-bit FE, I/O rates, NBT, layout, graphics, unrelated machine code.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerbank/PowerbankBlockEntity.java"
s=p.read_text(encoding="utf-8")

def once(old,new,label):
 global s
 count=s.count(old)
 assert count==1,("B1320_SOURCE_DRIFT",label,count,old[:100])
 s=s.replace(old,new,1)

for marker in ("B1300_NO_SELF_CHARGE","B1300_ACTIVE_SOURCE",
               "B1281_UNCAPPED_POWERBANK_AUTO_EXPORT",
               "b1300MarkSource(tx,b)","SnapshotJournal<long[]>",
               "xsxCommittedTransfer(",
               "private void b591PushOutput(ServerLevel server){",
               "activePorts","xsxNetworkEnabled"):
 assert marker in s,("B1320_MISSING_SAFETY_ANCHOR",marker)

once(" // B1300_NO_SELF_CHARGE: only owned controller is excluded, never other banks.",
""" // B1320_INPUT_PULL_CONTEXT: prevents ONLY the same controller's output
 // from being selected as a source while charging its own INPUT port.
 // External generators and other independent Powerbanks are unaffected.
 private static final ThreadLocal<PowerbankBlockEntity> b1320ActiveImport=
     new ThreadLocal<>();
 // B1300_NO_SELF_CHARGE: only owned controller is excluded, never other banks.""",
"input_pull_context")

once(" private void b591PushOutput(ServerLevel server){",
""" // B1320_POWERBANK_DEMAND_INPUT: actively request actual FE from adjacent
 // source ports, analogous to a storage multiblock with distinct input/output.
 // The ports are the already-validated controller activePorts; never scan
 // the world, retain FE in a single controller, and never buffer in cables.
 private void b1320PullInput(ServerLevel server){
  if(mode()!=PowerbankBlock.Mode.CONTROLLER||!formed||!xsxNetworkEnabled
      ||amount>=capacity)return;
  // Offset polling by controller position to avoid every bank traversing a
  // potentially large cable network on the same tick; direct producer push
  // into INPUT remains available on every tick without a rate cap.
  if(Math.floorMod(server.getGameTime(),5L)
      !=Math.floorMod(worldPosition.asLong(),5L))return;
  for(long encoded:activePorts){
   if(amount>=capacity)return;
   BlockPos portPos=BlockPos.of(encoded);
   if(!server.hasChunkAt(portPos)
       ||!server.getBlockState(portPos).is(
           dev.obsidiannetwork.ObsidianNetwork.POWERBANK_INPUT.get()))continue;
   var entity=server.getBlockEntity(portPos);
   if(!(entity instanceof PowerbankBlockEntity input)
       ||input.mode()!=PowerbankBlock.Mode.INPUT
       ||input.controller()!=this)continue;
   var sink=input.energyPort();
   if(sink==null)continue;
   for(net.minecraft.core.Direction face:net.minecraft.core.Direction.values()){
    if(amount>=capacity)return;
    BlockPos neighbor=portPos.relative(face);
    if(neighbor.equals(worldPosition)||activePorts.contains(neighbor.asLong())
        ||!server.hasChunkAt(neighbor))continue;
    var source=server.getCapability(
      net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
      neighbor,face.getOpposite());
    if(source==null||source==sink)continue;
    int request=(int)Math.min((long)Integer.MAX_VALUE,capacity-amount);
    if(request<=0)return;
    PowerbankBlockEntity previous=b1320ActiveImport.get();
    b1320ActiveImport.set(this);
    try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
     int extracted=source.extract(request,tx);
     // No commit for zero, rejection or partial acceptance: transaction
     // automatically restores BOTH endpoints without an unsafe refund.
     if(extracted>0&&sink.insert(extracted,tx)==extracted)tx.commit();
    }finally{
     if(previous==null)b1320ActiveImport.remove();
     else b1320ActiveImport.set(previous);
    }
   }
  }
 }
 private void b591PushOutput(ServerLevel server){""",
"active_input_transfer")

once("""  // B592_POWERBANK_OUTPUT_TICK
  be.b591PushOutput(sl);""",
"""  // B1320_POWERBANK_INPUT_PULL: first capture available external FE.
  // Never pull from this same bank's output via a cable proxy.
  be.b1320PullInput(sl);
  // B592_POWERBANK_OUTPUT_TICK
  be.b591PushOutput(sl);""",
"controller_tick_ingress_before_egress")

old="if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;"
assert s.count(old)==1,("B1320_EXPECT_OUTPUT_ONLY",s.count(old))
output=s.index("if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=0)return 0;")
assert s.index(old)>output,("B1320_OUTPUT_SCOPE_MISMATCH",s.index(old),output)
once(old,
 "if(b==null||!b.formed||!b.xsxNetworkEnabled||b1320ActiveImport.get()==b)return 0;",
 "same_controller_output_exclusion")

assert "b1300SelfCharge(tx,b)" in s
assert "b1300MarkSource(tx,b)" in s
assert "b1320ActiveImport.get()==b" in s
assert "b1320PullInput(sl)" in s
assert s.count("b1320ActiveImport.set(this)") == 1
assert s.count("b1320ActiveImport.remove()") == 1
assert "int offer=(int)Math.min((long)Integer.MAX_VALUE,amount)" in s
assert "source.extract(accepted,tx)==accepted" in s
assert "tx.commit();" in s
p.write_text(s,encoding="utf-8")
print("B1320_POWERBANK_ACTIVE_INPUT_REAL_EXTERNAL_FE_NO_SELF_IMPORT_ATOMIC_PASS")
