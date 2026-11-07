#!/usr/bin/env python3
"""B1351 isolated Powerbank rebuild from EXACT frozen v1.7.6 build 1319.

Design:
  - Single SnapshotJournal per physical Energy Cell, shared by all faces.
    Multiple snapshots of the same physical FE balance violate rollback.
  - Energy Cell origin tags reject same-cell self-charge on a shared cable
    network in either insertion/extraction ordering; no blanket ban on
    charging other Energy Cells (unlike the regressed v1.7.6 B1349).
  - Energy cable still owns ZERO FE. Its existing BFS routes real consumers
    first and physically separate storage endpoints second. A storage Cell
    that already advertises OUTPUT within the SAME connected cable component
    is not a recipient of energy recycled by that network. Distinct-network
    downstream storage and external Tech Mod consumers still work.
  - Source visibility counts only output-capable cell/bank ports, but does
    not falsify Energy Cell FE bars or capability storage metadata.
  - Powerbank active INPUT pulls from adjacent real producer/cable endpoints
    in a single root transaction, and cannot choose its OWN OUTPUT as source.
  - Controller shell/ports auto-link immediately on world load.
Only transactionally accepted FE changes any backed storage. No batteries
were added to cables. 2^31-1 FE per operation retained. No generation or
creative energy injection.
"""
import os,re
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
cp=j/"blockentity/EnergyCellBlockEntity.java"
bp=j/"powerbank/PowerbankBlockEntity.java"
xp=j/"blockentity/EnergyCableBlockEntity.java"
c=cp.read_text("utf8")
b=bp.read_text("utf8")
x=xp.read_text("utf8")

def once(s,old,new,label):
 n=s.count(old)
 assert n==1,("B1351_SOURCE_DRIFT",label,n,old[:130])
 return s.replace(old,new,1)

def span(src,signature):
 start=src.index(signature)
 brace=src.index("{",start+len(signature))
 depth=0
 for i in range(brace,len(src)):
  if src[i]=="{":depth+=1
  elif src[i]=="}":
   depth-=1
   if depth==0:return start,i+1,src[start:i+1]
 raise AssertionError(("B1351_UNBALANCED",signature))

# ------------------- ENERGY CELL -------------------
for token in ("private final class Handler implements EnergyHandler",
              "this.journal = new EnergyCellBlockEntity.Handler.Journal();",
              "this.journal.updateSnapshots(tx);",
              "return Math.toIntExact(EnergyCellBlockEntity.this.energy.extract(n));",
              "int accepted = target.insert(offer, tx);",
              "public long getAmountAsLong()",
              "public static void serverTick("):
 assert token in c,("B1351_CELL_ANCHOR",token)
c=once(c,"    private final class Handler implements EnergyHandler {",
"""    // B1351_PHYSICAL_CELL_ONE_JOURNAL: all seven capability views mutate the
    // same EnergyBuffer and MUST share one rollback snapshot.
    private EnergyCellBlockEntity.Handler.Journal b1351SharedJournal;
    private EnergyCellBlockEntity.Handler.Journal b1351Journal(
        EnergyCellBlockEntity.Handler sideOwner) {
       if (b1351SharedJournal == null) b1351SharedJournal = sideOwner.new Journal();
       return b1351SharedJournal;
    }
    private final class Handler implements EnergyHandler {""",
"single_cell_journal")
c=once(c,"this.journal = new EnergyCellBlockEntity.Handler.Journal();",
       "this.journal = EnergyCellBlockEntity.this.b1351Journal(this);",
       "side_handlers_share_physical_journal")
c=once(c,"public final class EnergyCellBlockEntity extends BlockEntity {",
"""public final class EnergyCellBlockEntity extends BlockEntity {
    // B1351_IDENTITY_ORIGIN: no fictitious demand from a cell's own input
    // face while its output is serving a common cable network. Other Cells
    // are NOT globally blocked merely for having an OUTPUT side.
    private static final ThreadLocal<EnergyCellBlockEntity> b1351AutoPush=
        new ThreadLocal<>();
    private static final java.util.Map<
        net.neoforged.neoforge.transfer.transaction.TransactionContext,
        java.util.Set<EnergyCellBlockEntity>> b1351TxSources=
        java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());
    private static void b1351MarkSource(
        net.neoforged.neoforge.transfer.transaction.TransactionContext tx,
        EnergyCellBlockEntity source) {
       synchronized(b1351TxSources){
          b1351TxSources.computeIfAbsent(tx,k->
            java.util.Collections.newSetFromMap(
             new java.util.IdentityHashMap<EnergyCellBlockEntity,Boolean>()))
             .add(source);
       }
    }
    private static boolean b1351SelfSource(
        net.neoforged.neoforge.transfer.transaction.TransactionContext tx,
        EnergyCellBlockEntity cell){
       if(b1351AutoPush.get()==cell)return true;
       synchronized(b1351TxSources){
          var sources=b1351TxSources.get(tx);
          return sources!=null && sources.contains(cell);
       }
    }
""","cell_per_transaction_source")
# ServerTick's receiver-first auto-export is guarded while the sink is
# interrogated. No global origin flag remains after this insert call.
c=once(c,"int accepted = target.insert(offer, tx);",
"""EnergyCellBlockEntity b1351Previous=b1351AutoPush.get();
                            b1351AutoPush.set(be);
                            int accepted;
                            try {accepted=target.insert(offer, tx);}
                            finally {
                               if(b1351Previous==null)b1351AutoPush.remove();
                               else b1351AutoPush.set(b1351Previous);
                            }""","cell_sender_sink_first_origin")
c=once(c,"          if (!this.canInsert()) {",
"""          if (b1351SelfSource(tx,EnergyCellBlockEntity.this))return 0;
          if (!this.canInsert()) {""","cell_origin_guard")
c=once(c,"return Math.toIntExact(EnergyCellBlockEntity.this.energy.extract(n));",
"""int pulled=Math.toIntExact(EnergyCellBlockEntity.this.energy.extract(n));
                if(pulled>0)b1351MarkSource(tx,EnergyCellBlockEntity.this);
                return pulled;""","source_first_cell_transaction_identity")

# ------------------- POWERBANK -------------------
for token in ("private void b591PushOutput(ServerLevel server){",
              "B1300_NO_SELF_CHARGE",
              "b1300SelfCharge(tx,b)",
              "if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;",
              "private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<long[]> journal",
              "activePorts","be.b591PushOutput(sl);"):
 assert token in b,("B1351_BANK_ANCHOR",token)

b=once(b,"  // B592_POWERBANK_OUTPUT_TICK\n  be.b591PushOutput(sl);",
"""  // B1351_RELINK_ON_LOAD: initial port owner mappings are reconstructed
  // before either I/O operation; no manual controller break is needed.
  if((!be.formed||be.activePorts.isEmpty())
      && sl.getGameTime()>=be.b1351NextRelink){
   be.b1351NextRelink=sl.getGameTime()+20L;
   be.revalidate(sl);
  }
  // Pull from actual sources via INPUT-capability/cable without an FE
  // buffer in either connector; then feed real consumers from OUTPUT.
  be.b1351PullInput(sl);
  be.b591PushOutput(sl);""","bank_tick_ingress_before_egress")
b=once(b,"  // B1300_NO_SELF_CHARGE: only owned controller is excluded, never other banks.",
"""  private long b1351NextRelink=Long.MIN_VALUE;
  private static final ThreadLocal<PowerbankBlockEntity> b1351ActiveImport=
      new ThreadLocal<>();
  // B1300_NO_SELF_CHARGE: only owned controller is excluded, never other banks.""","bank_input_origin_decl")
b=once(b,"  // B591_POWERBANK_OUTPUT_PUSH: bounded by actual validated shell ports.",
"""  // B1351_REAL_INPUT_SOURCE: on loaded, validated input ports only. Pure
  // source->sink transaction; no generator duplication or cable batteries.
  private void b1351PullInput(ServerLevel server){
   if(mode()!=PowerbankBlock.Mode.CONTROLLER||!formed||!xsxNetworkEnabled
      ||amount>=capacity)return;
   // Fast direct pushes remain unthrottled. Only producer polling is staggered.
   if(Math.floorMod(server.getGameTime(),2L)
      !=Math.floorMod(worldPosition.asLong(),2L))return;
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
     int offer=(int)Math.min((long)Integer.MAX_VALUE,capacity-amount);
     if(offer<=0)return;
     var prior=b1351ActiveImport.get();
     b1351ActiveImport.set(this);
     try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
      // Source first; exact equality required. Uncommitted partial transfers
      // roll back atomically on BOTH endpoints, including EnergyCell's
      // now-shared physical storage journal.
      int extracted=source.extract(offer,tx);
      if(extracted>0 && sink.insert(extracted,tx)==extracted)tx.commit();
     }finally{
      if(prior==null)b1351ActiveImport.remove();
      else b1351ActiveImport.set(prior);
     }
    }
   }
  }
  // B591_POWERBANK_OUTPUT_PUSH: bounded by actual validated shell ports.""",
"bank_active_input")
b=once(b,"if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;",
       "if(b==null||!b.formed||!b.xsxNetworkEnabled||b1351ActiveImport.get()==b)return 0;",
       "bank_source_excludes_own_output_during_pull")
# INPUT port advertises ZERO extractable FE to cable-source traversal. The
# stored controller value is still truthful in its GUI and own status().
b=once(b,"@Override public long getAmountAsLong(){\n      var bank=controller();return bank==null?0L:bank.amount;\n     }",
"""@Override public long getAmountAsLong(){
      if(mode()!=PowerbankBlock.Mode.OUTPUT)return 0L;
      var bank=controller();return bank==null?0L:bank.amount;
     }""","bank_source_visibility")
# ------------------- ZERO-BUFFER ENERGY CABLE -------------------
for token in ("class CableEnergyHandler implements EnergyHandler",
              "getAmountAsLong()","public int insert(","public int extract(",
              "B591_ENERGY_DIRECTED_WALK","liveBoundaryEnergy",
              "LongOpenHashSet","ENERGY_SCAN_DIRECTIONS"):
 assert token in x,("B1351_CABLE_DRIFT",token)

# getAmountAsLong() is a SOURCE hint, not its own FE buffer. Ignore INPUT
# side storage without falsifying the EnergyCell/Powerbank FE capability.
start,end,m=span(x,"public long getAmountAsLong()")
assert "long available = Math.max(0L, source.getAmountAsLong());" in m
m=once(m,"long available = Math.max(0L, source.getAmountAsLong());",
"""// B1351_FE_SOURCE_CAPABILITY_HINT: INPUT endpoints cannot
                            // supply FE even if their physical cell is charged.
                            var endpoint=server.getBlockEntity(next);
                            if(endpoint instanceof dev.obsidiannetwork.blockentity.EnergyCellBlockEntity cell
                                &&cell.sideMode(side.getOpposite())
                                    !=dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.OUTPUT)continue;
                            if(endpoint instanceof dev.obsidiannetwork.powerbank.PowerbankBlockEntity bank
                                &&bank.mode()!=dev.obsidiannetwork.powerbank.PowerbankBlock.Mode.OUTPUT)continue;
                            long available = Math.max(0L, source.getAmountAsLong());""",
"cable_correct_source_hint")
x=x[:start]+m+x[end:]

# Prioritize true machines over any storage only within THIS ONE BFS request.
# Do not ban input/output-configured cells on a different component. A cell
# whose OUTPUT is on the SAME cable component cannot receive its own
# network's exported FE; this makes filled machine networks demand=0.
start,end,m=span(x,"public int insert(int amount, TransactionContext transaction)")
assert "int var18 = amount;" in m and "BlockPos next = cable.relative(side);" in m
assert m.count("int accepted = target.insert(var18, transaction);")==1
m=once(m,"int var18 = amount;",
"""int var18 = amount;
             // B1351_DEMAND_BEFORE_STORAGE: queued storage has no FE escrow.
             java.util.ArrayList<EnergyHandler> b1351Deferred=new java.util.ArrayList<>();
             java.util.ArrayList<dev.obsidiannetwork.blockentity.EnergyCellBlockEntity>
                b1351DeferredCells=new java.util.ArrayList<>();
             java.util.HashSet<Long> b1351DeferredPositions=new java.util.HashSet<>();
             java.util.Set<dev.obsidiannetwork.blockentity.EnergyCellBlockEntity>
                b1351OutputCells=java.util.Collections.newSetFromMap(
                  new java.util.IdentityHashMap<>());
""","cable_deferred_priority")
m=once(m,"int accepted = target.insert(var18, transaction);",
"""// Only actual consumer capabilities drain FE in the first pass.
                            // A supplier EnergyCell can still charge a
                            // downstream Cell on a physically separate grid.
                            var be=server.getBlockEntity(next);
                            if(be instanceof dev.obsidiannetwork.blockentity.EnergyCellBlockEntity cell){
                               if(cell.sideMode(side.getOpposite())
                                  ==dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.OUTPUT)
                                  b1351OutputCells.add(cell);
                               else if(b1351DeferredPositions.add(next.asLong())){
                                  b1351Deferred.add(target);
                                  b1351DeferredCells.add(cell);
                               }
                               continue;
                            }
                            if(be instanceof dev.obsidiannetwork.powerbank.PowerbankBlockEntity bank){
                               if(bank.mode()==dev.obsidiannetwork.powerbank.PowerbankBlock.Mode.INPUT
                                  &&b1351DeferredPositions.add(next.asLong())){
                                  b1351Deferred.add(target);
                                  b1351DeferredCells.add(null);
                               }
                               continue;
                            }
                            int accepted = target.insert(var18, transaction);""",
"machine_demand_first")
m=once(m,"return amount - var18;",
"""// B1351_STORAGE_PHASE: only real spare capacity may accept the
             // remaining FE. Cells that have OUTPUT in THIS cable component
             // are sources, never demand for the very same component.
             for(int k=0;k<b1351Deferred.size() && var18>0;k++){
                var cell=b1351DeferredCells.get(k);
                if(cell!=null&&b1351OutputCells.contains(cell))continue;
                int stored=b1351Deferred.get(k).insert(var18,transaction);
                if(stored>0)var18-=Math.min(stored,var18);
             }
             return amount - var18;""",
"deferred_true_storage_sinks")
assert m.count("int accepted = target.insert(var18, transaction);")==1
assert "b1351OutputCells.contains(cell)" in m
x=x[:start]+m+x[end:]

for token in ("b1351SharedJournal","b1351AutoPush","b1351MarkSource"):
 assert token in c
for token in ("b1351PullInput(sl)","b1300SelfCharge(tx,b)",
              "b1351ActiveImport.get()==b","B1281_UNCAPPED_POWERBANK_AUTO_EXPORT"):
 assert token in b
for token in ("b1351DeferredCells","b1351OutputCells","b1351DeferredPositions"):
 assert token in x
# Source-drift guards complete: ONLY NOW publish all three replacements.
cp.write_text(c,"utf8")
bp.write_text(b,"utf8")
xp.write_text(x,"utf8")
print("B1351_POWERBANK_CELL_SHARED_JOURNAL_CONSUMER_PRIORITY_ZERO_BUFFER_SAFE_PASS")
