#!/usr/bin/env python3
"""B1269 staged: keep decoded native Backpack Cells resident across cable ingress.

Like the normal StorageDriveRuntime/StorageNetwork, a placed Backpack keeps
short-lived, server-thread-only decoded StorageCellStore/EquipmentCellStore
objects across successive successful ingress transactions. The REAL cell
ItemStacks are still written on EVERY accepted transfer, until a separately
verified transaction-wide materialization mechanism can be introduced.

The cache is keyed by exact placed ItemStack identity + its immutable CONTAINER
component. Any GUI write, extraction, replacement, rollback or exception
invalidates it; accepted inserts explicitly rebase onto the newly persisted
ItemStack. Only the placed block's ItemCable insert path uses this cache.
No behavior changes to worn bags, outbound transfers, storage priorities,
preview/capacity limits or vanilla inventory and item-conservation rules.

Apply AFTER B1265 (which provides per-invocation arrays). This strict patch
checks ALL anchors before updating either Java source; unknown API => fail.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
be=root/"backpack/NetworkBackpackBlockEntity.java"
cells=root/"backpack/V176BackpackCells.java"
b=be.read_text(encoding="utf-8")
c=cells.read_text(encoding="utf-8")

def once(src,old,new,label):
    n=src.count(old)
    assert n==1,("B1269_RUNTIME_SOURCE_DRIFT",label,n)
    return src.replace(old,new,1)

c=once(c,
''' public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){''',
''' /** The original public API remains unchanged for worn bags and GUI mutations. */
 public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){
  return insertWithRuntime(world,bag,incoming,requested,null);
 }
 /** The block entity owns this transient decoded view, never shared with players
  * or other blocks. The canonical source remains the saved ItemStack. */
 public static final class IngressRuntimeCache {
  private ItemStack owner=null;
  private ItemContainerContents container=null;
  private final dev.obsidiannetwork.core.EquipmentCellStore[] equipment=new dev.obsidiannetwork.core.EquipmentCellStore[4];
  private final StorageCellStore[] storage=new StorageCellStore[4];
  public void resetFor(ItemStack stack){
   ItemContainerContents content=stack.get(DataComponents.CONTAINER);
   if(owner!=stack||container!=content){
    invalidate();
    owner=stack;
    container=content;
   }
  }
  public void rebase(ItemStack persisted){
   owner=persisted;
   container=persisted.get(DataComponents.CONTAINER);
  }
  public void invalidate(){
   java.util.Arrays.fill(equipment,null);
   java.util.Arrays.fill(storage,null);
   owner=null;
   container=null;
  }
 }
 /** STRICTLY server-owned placed-backpack ingress fastpath.
  * All native cell writes, capacity checks and exact descriptors are unchanged.
  * The owner must call resetFor(current) before passing a detached copy.
  */
 public static Transfer insertWithRuntime(Level world,ItemStack bag,ItemStack incoming,
      long requested,IngressRuntimeCache cache){''',
"insert API bridge")

c=once(c,
'''  var xsxEquipmentReadOnce=new dev.obsidiannetwork.core.EquipmentCellStore[4];
  var xsxStorageReadOnce=new dev.obsidiannetwork.core.StorageCellStore[4];''',
'''  var xsxEquipmentReadOnce=cache==null
      ?new dev.obsidiannetwork.core.EquipmentCellStore[4]:cache.equipment;
  var xsxStorageReadOnce=cache==null
      ?new dev.obsidiannetwork.core.StorageCellStore[4]:cache.storage;''',
"reuse native stores across incoming transactions")

b=once(b,
''' private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
''' // Same live decoded Store model as StorageDriveRuntime, but confined to the
 // placed Backpack BE. Canonical Cell ItemStacks are persisted per transfer.
 private final V176BackpackCells.IngressRuntimeCache xsxIngressRuntimeCache=
     new V176BackpackCells.IngressRuntimeCache();
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
"block-owned cache field")

b=once(b,
'''    @Override protected void revertToSnapshot(ItemStack before){backpack=before.copy();}''',
'''    @Override protected void revertToSnapshot(ItemStack before){
     backpack=before.copy();
     // No speculative Store state survives NeoForge transaction rollback.
     xsxIngressRuntimeCache.invalidate();
    }''',
"nested/root rollback cache invalidation")

b=once(b,
'''     ItemStack before=backpack;
     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);
     int accepted=(int)result.accepted();
     if(accepted<=0)return 0; // full / disallowed / no installed storage
     cableJournal.updateSnapshots(tx);
     backpack=updated;
     xsxAdvanceExistingCableSlot(i,item,accepted,before);
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS''',
'''     ItemStack before=backpack;
     // External GUI mutations, existing cable extraction and block replacement
     // always invalidate by owner identity / immutable CONTAINER component.
     xsxIngressRuntimeCache.resetFor(before);
     ItemStack updated=before.copy();
     try{
      var result=V176BackpackCells.insertWithRuntime(
          level,updated,item.toStack(),requested,xsxIngressRuntimeCache);
      int accepted=(int)result.accepted();
      if(accepted<=0)return 0; // no storage or no remaining capacity
      // The canonical contents have ALREADY been written by insertWithRuntime.
      // Journal before transferring ownership; rollback invalidates both caches.
      cableJournal.updateSnapshots(tx);
      backpack=updated;
      xsxIngressRuntimeCache.rebase(updated);
      xsxAdvanceExistingCableSlot(i,item,accepted,before);
      return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS
     }catch(RuntimeException failure){
      // No transient mutation may escape a failed candidate/transaction.
      xsxIngressRuntimeCache.invalidate();
      throw failure;
     }''',
"transaction-safe high-speed ingress")

# Check that all existing safety contracts are preserved in the resulting Java.
for token in (
 "cableJournal.updateSnapshots(tx)",
 "xsxAdvanceExistingCableSlot(i,item,accepted,before)",
 "xsxCableCommitRevision++",
 "xsxIngressRuntimeCache.invalidate()",
 "xsxIngressRuntimeCache.rebase(updated)",
 "backpack=before.copy()"):
 assert token in b,("B1269_BE_GUARD_MISSING",token)
for token in (
 "previewInsertExact(","insertExact(","writeSlots(bag,replacements)",
 "EquipmentCellItem","StorageCellItem",
 "EquipmentCellStore[4]","StorageCellStore[4]",
 "insertWithRuntime(world,bag,incoming,requested,null)"):
 assert token in c,("B1269_CELL_GUARD_MISSING",token)
assert c.count("public static Transfer insertWithRuntime(")==1
assert b.count("xsxIngressRuntimeCache.resetFor(before)")==1
# Never change the old API for hand-held/worn bags or outward cable transfers.
assert b.count("V176BackpackCells.extract(")==1
# Writes occur only after all fail-closed checks passed.
cells.write_text(c,encoding="utf-8")
be.write_text(b,encoding="utf-8")
print("B1269_NATIVE_BACKPACK_INGRESS_RUNTIME_REUSE_AND_ROLLBACK_GUARDS_PASS")
