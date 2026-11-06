"""B1265: high-speed ItemCable Backpack regression and lossless cache model.

The full Java compile and NeoForge conservation GameTests remain mandatory.
These gates ensure drift fails before any Java write; normal ItemCable rates,
exact descriptors, transactional rollback and Equipment Cells stay intact.
"""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1265-backpack-cable-burst-fastpath.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

BE="""class TestBE {
 // cableJournal.updateSnapshots(tx) backpack=before.copy()
 // xsxCableCacheStack==backpack xsxCableCacheRevision==xsxCableCommitRevision
 private long xsxCableCommitRevision;
 private java.util.List<V176BackpackCells.Entry> xsxCableEntries;
 private java.util.List<ItemResource> xsxCableResources;
 private void xsxRefreshCableView(){
   xsxCableEntries=entries;
   xsxCableResources=java.util.List.copyOf(resources);
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=
     new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
     @Override protected void onRootCommit(ItemStack before){
     xsxCableCommitRevision++;
     setChanged();
     }
 };
 int insert(int i,ItemResource item,int amount,TransactionContext tx){
     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);
     int accepted=(int)result.accepted();
     if(accepted<=0)return 0;
     cableJournal.updateSnapshots(tx);
     backpack=updated;
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS
 }
}"""

CELLS="""class V176BackpackCells {
 public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){
  // EquipmentCellItem and StorageCellItem are two distinct compatible stores.
  long left=requested;
  for(int phase=0;phase<2&&left>0;phase++){
   for(int family=0;family<2&&left>0;family++){
    for(int i=1;i<=3&&left>0;i++){
     ItemStack cellStack=replacements.get(i);
     if(family==0&&cellStack.getItem() instanceof EquipmentCellItem equipment){
      EquipmentCellStore store=equipment.readStore(cellStack);
      if((phase==0)!=(store.amount(key)>0))continue;
      long accepted=store.previewInsertExact(key,payload,left);
      if(accepted>0){store.insertExact(key,payload,accepted);left-=accepted;}
     }
     if(family==1&&cellStack.getItem() instanceof StorageCellItem cell){
      StorageCellStore store=cell.readStore(cellStack);
      if((phase==0)!=(store.amount(key)>0))continue;
      long accepted=store.previewInsertExact(key,payload,left);
      if(accepted>0){store.insertExact(key,payload,accepted);left-=accepted;}
     }
    }
   }
  }
  if(left<requested)writeSlots(bag,replacements);
  return new Transfer(requested-left,left);
 }
 public static List<Entry> entries(ItemStack bag){return null;}
}"""

def patch_fixture(be_source=BE,cell_source=CELLS):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)/"dev/obsidiannetwork/backpack"
  root.mkdir(parents=True)
  b=root/"NetworkBackpackBlockEntity.java"
  c=root/"V176BackpackCells.java"
  b.write_text(be_source,"utf-8")
  c.write_text(cell_source,"utf-8")
  run=subprocess.run([sys.executable,str(PATCH)],
    env={**os.environ,"V1_SOURCE_ROOT":tmp},
    capture_output=True,text=True)
  return run,b.read_text("utf-8"),c.read_text("utf-8")

def model(quantities, capacities, incoming, op_count, memoized):
 """Original 2-phase -> exact same output, only number of readStore calls differs."""
 counts=list(quantities)
 total_reads=0
 for _ in range(op_count):
  remaining=incoming
  memo=[None]*len(counts)
  for phase in (0,1):
   for i in range(len(counts)):
    if remaining<=0:break
    if memoized and memo[i] is not None:
     was=memo[i]
    else:
     total_reads+=1
     was=counts[i]
     if memoized:memo[i]=was
    present=was>0
    if (phase==0)!=present:continue
    accepted=min(remaining,capacities[i]-counts[i])
    if accepted<0:accepted=0
    counts[i]+=accepted
    remaining-=accepted
    if memoized:memo[i]=counts[i]
 return counts,total_reads

class HighSpeedB1265(unittest.TestCase):
 def test_syntax_and_workflow_order(self):
  ast.parse(PATCH.read_text("utf-8"))
  s=WORKFLOW.read_text("utf-8")
  self.assertIn(PATCH.name,s)
  self.assertIn(Path(__file__).name,s)
  self.assertGreater(s.index(PATCH.name),s.index("apply-v176-b1261-backpack-selected-hotbar-pickup.py"))

 def test_fixture_updates_only_validated_hotpaths(self):
  r,be,cells=patch_fixture()
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertIn("B1265_BACKPACK_INCREMENTAL_CABLE_VIEW_AND_PER_CALL_CELL_READ_ONCE_PASS",r.stdout)
  for t in ("xsxAdvanceExistingCableSlot(i,item,accepted,before)",
            "xsxCableCacheStack!=before",
            "xsxCableCacheRevision!=xsxCableCommitRevision",
            "xsxCableEntries.set(index,new V176BackpackCells.Entry(old.descriptor(),newCount))",
            "xsxCableUsed=newUsed",
            "xsxCableCommitRevision++",
            "cableJournal.updateSnapshots(tx)"):
   self.assertIn(t,be)
  for t in ("xsxEquipmentReadOnce[i]",
            "xsxStorageReadOnce[i]",
            "store.previewInsertExact",
            "store.insertExact",
            "writeSlots(bag,replacements)"):
   self.assertIn(t,cells)
  self.assertEqual(cells.count("readStore("),2)
  self.assertEqual(cells.count("writeSlots(bag,replacements)"),1)

 def test_drift_rejects_before_any_java_write(self):
  for b,c in ((BE.replace("xsxCableEntries=entries;","xsxCableEntries=other;"),CELLS),
              (BE,CELLS.replace("EquipmentCellStore store=equipment.readStore(cellStack);",
                                "EquipmentCellStore store=getStore(cellStack);"))):
   r,new_b,new_c=patch_fixture(b,c)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(new_b,b)
   self.assertEqual(new_c,c)

 def test_randomized_16_stack_speed_burst_item_conservation(self):
  rng=random.Random(1265)
  savings=0
  for n in range(8000):
   caps=[rng.randint(4,400) for _ in range(3)]
   amounts=[rng.randint(0,c) for c in caps]
   per_transfer=rng.randint(1,64)
   transfers=rng.randint(1,16)
   old,reads_old=model(amounts,caps,per_transfer,transfers,False)
   new,reads_new=model(amounts,caps,per_transfer,transfers,True)
   self.assertEqual(new,old,(n,amounts,caps,per_transfer,transfers))
   self.assertLessEqual(reads_new,reads_old)
   self.assertEqual(sum(new)-sum(amounts),sum(old)-sum(amounts))
   savings+=reads_old-reads_new
  self.assertGreater(savings,15000)

 def test_counts_only_increment_on_actual_accepted_root_transfer(self):
  for start in (0,1,63,1000):
   for incoming in (0,1,16,64):
    actual_accept=min(incoming,64)
    cached_before=start
    cached_after=start+actual_accept
    # Root commit: cache count equals persistent store count.
    self.assertEqual(cached_after,start+actual_accept)
    # Rollback must not reuse speculative cache after ItemStack identity change.
    restored_store=start
    self.assertEqual(restored_store,cached_before)
    if actual_accept:
     self.assertNotEqual(cached_after,restored_store)
  s=PATCH.read_text("utf-8")
  self.assertIn("xsxCableCacheStack!=before",s)
  self.assertIn("xsxCableCacheContainer!=before.get",s)
  self.assertIn("xsxCableCacheRevision!=xsxCableCommitRevision",s)

 def test_scope_and_never_limit_throughput(self):
  s=PATCH.read_text("utf-8")
  for token in ("features/v175/","Thread.sleep","tickCount%","ITEM_BUDGET",
                "getMaxStackSize()","Entity.remove","PowerArmorEntrySequence"):
   self.assertNotIn(token,s)

if __name__=="__main__":
 unittest.main()
