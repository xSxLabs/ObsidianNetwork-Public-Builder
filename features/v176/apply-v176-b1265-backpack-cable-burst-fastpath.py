#!/usr/bin/env python3
"""B1265: lossless high-speed cable ingress without per-insert full re-indexing.

NeoForge 26.1 ResourceHandler callbacks are synchronous & transactional.
For an existing (exact item + components) cable slot, insert() already
validated the resource and the detached V176BackpackCells.insert() accepted
the amount. Advance only the cached count and used totals on that same
validated immutable snapshot. Never skip actual cell insertion, journaling,
serialization, or rollback. New types / external edits take the old full path.

Within ONE V176BackpackCells.insert() invocation, decode each installed cell
only once across its existing-vs-new-type passes. These are local arrays, NOT
cross-transaction mutable stores. The same exact two-phase routing remains.
All changes are anchored and assembled BEFORE writing either Java target.
"""
# B1265 compiled-candidate: no throttling; strict transactional ItemCable conservation.
import os
import re
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
be=root/"backpack/NetworkBackpackBlockEntity.java"
cells=root/"backpack/V176BackpackCells.java"
be_src=be.read_text(encoding="utf-8")
cells_src=cells.read_text(encoding="utf-8")

def replace_once(source,old,new,label):
 n=source.count(old)
 assert n==1,("B1265_BACKPACK_SOURCE_DRIFT",label,n)
 return source.replace(old,new,1)

be_src=replace_once(be_src,
'''   xsxCableEntries=entries;
   xsxCableResources=java.util.List.copyOf(resources);''',
'''   // Mutable ONLY inside this server-owned cache. Never returned as inventory.
   // One count update now costs O(1) instead of re-decoding all 3 cell stores.
   xsxCableEntries=new java.util.ArrayList<>(entries);
   xsxCableResources=java.util.List.copyOf(resources);''',
"mutable cached entry view")

be_src=replace_once(be_src,
''' private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
''' private void xsxAdvanceExistingCableSlot(int index,
      net.neoforged.neoforge.transfer.item.ItemResource item,
      int accepted,ItemStack before){
  if(accepted<=0||index<0||index>=xsxCableEntries.size()
      ||index>=xsxCableResources.size()||xsxCableCacheStack!=before
      ||xsxCableCacheRevision!=xsxCableCommitRevision
      ||xsxCableCacheContainer!=before.get(net.minecraft.core.component.DataComponents.CONTAINER)
      ||!xsxCableResources.get(index).equals(item))return;
  // Exact slot is unchanged; only its count and the used total increased.
  var old=xsxCableEntries.get(index);
  long newCount=Math.addExact(old.count(),(long)accepted);
  long newUsed=Math.addExact(xsxCableUsed,(long)accepted);
  if(newUsed>xsxCableCapacity)return; // suspicious external edit: force refresh
  xsxCableEntries.set(index,new V176BackpackCells.Entry(old.descriptor(),newCount));
  xsxCableUsed=newUsed;
  xsxCableCacheStack=backpack;
  xsxCableCacheContainer=backpack.get(net.minecraft.core.component.DataComponents.CONTAINER);
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
"incremental cable cache")

be_src=replace_once(be_src,
'''     xsxCableCommitRevision++;
     setChanged();''',
'''     xsxCableCommitRevision++;
     // Keep a validated count-only cache across COMMITTED transfers.
     // Extracts, GUI writes, replacements and aborted transfers do not match
     // the identity/component guards and will refresh on their next query.
     if(xsxCableCacheStack==backpack
         &&xsxCableCacheContainer==backpack.get(net.minecraft.core.component.DataComponents.CONTAINER)
         &&xsxCableCacheRevision==xsxCableCommitRevision-1L)
      xsxCableCacheRevision=xsxCableCommitRevision;
     setChanged();''',"committed revision")

be_src=replace_once(be_src,
'''     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);''',
'''     ItemStack before=backpack;
     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);''',
"record pre-insert owner")

be_src=replace_once(be_src,
'''     cableJournal.updateSnapshots(tx);
     backpack=updated;
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS''',
'''     cableJournal.updateSnapshots(tx);
     backpack=updated;
     xsxAdvanceExistingCableSlot(i,item,accepted,before);
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS''',
"update after actual transfer")

start=cells_src.index(" public static Transfer insert(")
stop=cells_src.index(" public static List<Entry> entries(",start)
method=cells_src[start:stop]
assert "EquipmentCellItem" in method and "StorageCellItem" in method, "B1265_CELL_FAMILIES_DRIFT"
assert method.count("for(int phase=0;phase<2&&left>0;phase++)")==1, "B1265_TWO_PHASE_DRIFT"
assert "for(int i=1;i<=3&&left>0;i++)" in method, "B1265_SLOT_LOOP_DRIFT"

# The compiled B1264 shows the Equipment and Storage read calls in that order.
# Different source shape means STOP, not silently alter inventory routing.
pattern=re.compile(r"(?m)^(?P<indent>\s*)(?P<type>var|EquipmentCellStore|StorageCellStore)\s+(?P<target>\w+)\s*=\s*(?P<reader>\w+)\.readStore\((?P<stack>\w+)\);")
reads=list(pattern.finditer(method))
assert len(reads)==2,("B1265_CELL_READ_SHAPE_DRIFT",len(reads))
assert reads[0].group("target")==reads[1].group("target")=="store", "B1265_STORE_VAR_DRIFT"
assert reads[0].group("stack")==reads[1].group("stack"), "B1265_CELL_STACK_VAR_DRIFT"
assert "EquipmentCellItem" in method[:reads[0].start()], "B1265_EQUIPMENT_ORDER_DRIFT"
assert "StorageCellItem" in method[reads[0].end():reads[1].start()], "B1265_STORAGE_ORDER_DRIFT"
assert method.count("writeSlots(bag,replacements)") == 1, "B1265_FINAL_WRITE_DRIFT"

replacement = []
for kind,m in zip(("Equipment","Storage"),reads):
 arr="xsx"+kind+"ReadOnce"
 typ="dev.obsidiannetwork.core."+kind+"CellStore"
 indent=m.group("indent")
 original=m.group(0).lstrip()
 target=m.group("target")
 receiver=m.group("reader")
 stack=m.group("stack")
 declaration=m.group("type")
 body=(indent+declaration+" "+target+"="+arr+"[i];\n"
       +indent+"if("+target+"==null){"+target+"="+receiver+".readStore("+stack+");"+arr+"[i]="+target+";}")
 replacement.append(body)

for m,body in reversed(list(zip(reads,replacement))):
 method=method[:m.start()]+body+method[m.end():]
method=replace_once(method,
'''  long left=requested;''',
'''  // Read each installed cell at most once in this ONE insert invocation.
  // No cross-transaction mutable store reuse; existing phases are unchanged.
  var xsxEquipmentReadOnce=new dev.obsidiannetwork.core.EquipmentCellStore[4];
  var xsxStorageReadOnce=new dev.obsidiannetwork.core.StorageCellStore[4];
  long left=requested;''',
"local store cache placement")
assert method.count("readStore(")==2, "B1265_UNEXPECTED_ADDITIONAL_READS"
assert method.count("insertExact(")==2, "B1265_INSERT_COUNT_DRIFT"
assert method.count("previewInsertExact(")==2, "B1265_PREVIEW_COUNT_DRIFT"
cells_src=cells_src[:start]+method+cells_src[stop:]

for token in ("cableJournal.updateSnapshots(tx)","backpack=before.copy()",
              "xsxCableCacheStack==backpack","xsxCableCacheRevision==xsxCableCommitRevision"):
 assert token in be_src,("B1265_TRANSACTION_GUARD_MISSING",token)
for token in ("EquipmentCellItem","StorageCellItem","writeSlots(bag,replacements)",
              "store.previewInsertExact","store.insertExact"):
 assert token in cells_src,("B1265_CELL_SAFETY_MISSING",token)
# All drift checks complete; only now write both Java files.
be.write_text(be_src,encoding="utf-8")
cells.write_text(cells_src,encoding="utf-8")
print("B1265_BACKPACK_INCREMENTAL_CABLE_VIEW_AND_PER_CALL_CELL_READ_ONCE_PASS")
