#!/usr/bin/env python3
"""B1300 (after frozen B1292): prevent energy loops, loss on partial acceptance,
and misleading Jade cable storage bars. Preserve full-rate demand-driven FE
capabilities, controller storage, side modes and all original recipes/graphics.

Only change exact known post-B1292 source signatures; fail closed on drift.
"""
import os
from pathlib import Path
R=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
cable=R/"blockentity/EnergyCableBlockEntity.java"
bank=R/"powerbank/PowerbankBlockEntity.java"
ticker=R/"conduit/EnergyConduitTicker.java"
jade=R/"compat/EnergyCableJadePlugin.java"
files=[ticker,bank,jade]
source={p:p.read_text(encoding="utf-8") for p in files}
assert "B591_ENERGY_DIRECTED_WALK" in cable.read_text(encoding="utf-8")
assert "XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1" in source[ticker]
assert "B1281_UNCAPPED_POWERBANK_AUTO_EXPORT" in source[bank]
assert "SnapshotJournal<long[]>" in source[bank]
assert "xsxCommittedTransfer(" in source[bank]
assert "JadeIds.UNIVERSAL_ENERGY_STORAGE" in source[jade]
assert "registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class)" in source[jade]

def one(text,old,new,name):
    n=text.count(old)
    assert n==1,("B1300_SOURCE_DRIFT",name,n,old[:150])
    return text.replace(old,new,1)

# A successful transfer must ALWAYS debit precisely the amount credited.
# The legacy refund was unchecked: if the source rejects reinsertion, FE could
# vanish. Close the first transaction WITHOUT commit on partial acceptance,
# then retry the exact accepted amount in a fresh transaction. If anything
# fails on the second attempt, that transaction also rolls back completely.
t=source[ticker]
old="try(Transaction tx=Transaction.openRoot()){int got=from.extract(1000,tx);if(got<=0)continue;int put=to.insert(got,tx);if(put<=0)continue;if(put<got)from.insert(got-put,tx);tx.commit();return;}"
new="""// B1300_ATOMIC_PARTIAL_FE: NEVER refund to a possibly extract-only producer.
     int accepted=0;
     try(Transaction tx=Transaction.openRoot()){
      int got=from.extract(1000,tx);
      if(got<=0)continue;
      int put=to.insert(got,tx);
      if(put<=0)continue;
      if(put==got){tx.commit();return;}
      accepted=put; // uncommitted tentative extract/insert: auto-rollback
     }
     if(accepted>0){
      try(Transaction tx=Transaction.openRoot()){
       int got=from.extract(accepted,tx);
       if(got==accepted && to.insert(got,tx)==got){
        tx.commit();return;
       }
      }
     }"""
t=one(t,old,new,"energy_conduit_atomic_partial")
assert "from.insert(got-put,tx)" not in t
assert "B1300_ATOMIC_PARTIAL_FE" in t
source[ticker]=t

b=source[bank]
# The B591 powerbank output PUSH writes to the target first. A ThreadLocal
# identifies the originating bank while a cable recursively accepts that
# write. The transaction marker covers the inverse path (machines/conduits
# extract from an OUTPUT first, then insert into an INPUT).
anchor=" private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<long[]> journal="
guard=""" // B1300_NO_SELF_CHARGE: only owned controller is excluded, never other banks.
 private static final ThreadLocal<PowerbankBlockEntity> b1300ActiveExport=
     new ThreadLocal<>();
 private static final java.util.Map<
     net.neoforged.neoforge.transfer.transaction.TransactionContext,
     java.util.Set<PowerbankBlockEntity>> b1300TxSources=
     java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());
 private static void b1300MarkSource(
     net.neoforged.neoforge.transfer.transaction.TransactionContext tx,
     PowerbankBlockEntity owner){
  synchronized(b1300TxSources){
   b1300TxSources.computeIfAbsent(tx,
     k->java.util.Collections.newSetFromMap(
       new java.util.IdentityHashMap<PowerbankBlockEntity,Boolean>())).add(owner);
  }
 }
 private static boolean b1300SelfCharge(
     net.neoforged.neoforge.transfer.transaction.TransactionContext tx,
     PowerbankBlockEntity owner){
  if(b1300ActiveExport.get()==owner)return true;
  synchronized(b1300TxSources){
   var owners=b1300TxSources.get(tx);
   return owners!=null&&owners.contains(owner);
  }
 }
"""
b=one(b,anchor,guard+anchor,"controller_identity_transaction_guard")
old="""    try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
     int accepted=target.insert(offer,tx);
     if(accepted>0 && source.extract(accepted,tx)==accepted)tx.commit();
    }"""
new="""    // B1300_ACTIVE_SOURCE: the cable may lead back into this bank's INPUT.
    // Keep the same sink-first/source-second atomic transfer; NEVER accept
    // our own FE just because another cable endpoint advertises spare capacity.
    PowerbankBlockEntity prior=b1300ActiveExport.get();
    b1300ActiveExport.set(this);
    try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
     int accepted=target.insert(offer,tx);
     if(accepted>0 && source.extract(accepted,tx)==accepted)tx.commit();
    }finally{
     if(prior==null)b1300ActiveExport.remove();
     else b1300ActiveExport.set(prior);
    }"""
b=one(b,old,new,"powerbank_active_push_guard")
# Exact post-B1292 port code; rate/amount are not derived from getCapacity.
old="if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;"
assert b.count(old)==2,("B1300_INPUT_OUTPUT_PORT_DRIFT",b.count(old))
# Patch only the INPUT branch. Excluding the whole bank's other input ports
# would break legitimate energy generation and bank-to-bank transfers.
input_start=b.index("if(mode()!=PowerbankBlock.Mode.INPUT||offered<=0)return 0;")
output_start=b.index("if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=0)return 0;")
assert 0<input_start<output_start
seg=b[input_start:output_start]
seg=one(seg,old,"if(b==null||!b.formed||!b.xsxNetworkEnabled||b1300SelfCharge(tx,b))return 0;","powerbank_input_self_charge")
b=b[:input_start]+seg+b[output_start:]
# Record actual origin only after a positive extract, never a simulated read.
old="if(taken>0){b.journal.updateSnapshots(tx);b.amount-=taken;b.xsxPendingOut+=taken;}"
new="if(taken>0){b.journal.updateSnapshots(tx);b.amount-=taken;b.xsxPendingOut+=taken;b1300MarkSource(tx,b);}"
b=one(b,old,new,"powerbank_transaction_origin")
# No cap-based automatic export or additional FE buffers.
assert "int offer=(int)Math.min((long)Integer.MAX_VALUE,amount)" in b
assert "target.insert(offer,tx)" in b and "source.extract(accepted,tx)==accepted" in b
assert "target.getCapacityAsLong()" not in b[b.index("private void b591PushOutput("):b.index(anchor)]
assert "xsxRates.committed(level.getGameTime()" in b
source[bank]=b

# Jade BODY provider removal may run before the universal provider. Perform
# the removal AGAIN after the tooltip has been fully assembled (Jade 26.1 API),
# scoped strictly to our cable block. Never change its FE capability because
# other mods rely on cable pass-through visibility.
j=source[jade]
old="""  registration.registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class);
 }"""
new="""  registration.registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class);
  // B1300_JADE_FINAL_TOOLTIP: the old B1281 body hook did not suppress
  // the 0 FE / 2.14 GFE bar in-game. At end of collection remove the
  // universal proxy meter; leave the truthful "no internal storage" line.
  registration.addTooltipCollectedCallback((root,accessor)->{
   if(accessor instanceof BlockAccessor block
       && block.getBlock() instanceof EnergyCableBlock){
    root.getTooltip().remove(JadeIds.UNIVERSAL_ENERGY_STORAGE);
    root.getTooltip().remove(JadeIds.UNIVERSAL_ENERGY_STORAGE_DEFAULT);
   }
  });
 }"""
j=one(j,old,new,"jade_end_of_collection_cable_only")
source[jade]=j

# No output is ever committed unless the sink accepted the exact debit.
# Both rollback-sensitive files retain their existing source-of-truth.
for p in files:p.write_text(source[p],encoding="utf-8")
print("B1300_ENERGY_ATOMIC_PARTIAL_NO_SELF_CHARGE_TRUE_COMMITTED_OUTPUT_JADE_FINAL_PASS")
