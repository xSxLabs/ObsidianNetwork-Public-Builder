"""B1269 Backpack ingress runtime cache: source drift and conservation checks.

These gates do not pretend to measure actual server MSPT. The full NeoForge
compile, active world, 16-upgrade ItemCable insertion and rollback tests remain
mandatory before the staged branch is allowed into the v1.7.6 candidate.
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
PATCH=ROOT/"features/v176/apply-v176-b1269-backpack-live-cell-runtime.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

BE='''class NetworkBackpackBlockEntity {
 // xsxCableCommitRevision++;
 private ItemStack backpack=ItemStack.EMPTY;
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=
 new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected ItemStack createSnapshot(){return backpack.copy();}
    @Override protected void revertToSnapshot(ItemStack before){backpack=before.copy();}
    @Override protected void onRootCommit(ItemStack before){xsxCableCommitRevision++;setChanged();}
 };
 int insert(int i,ItemResource item,int amount,TransactionContext tx){
     int requested=amount;
     ItemStack before=backpack;
     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);
     int accepted=(int)result.accepted();
     if(accepted<=0)return 0; // full / disallowed / no installed storage
     cableJournal.updateSnapshots(tx);
     backpack=updated;
     xsxAdvanceExistingCableSlot(i,item,accepted,before);
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS
 }
 int extract(){return (int)V176BackpackCells.extract(level,backpack,d,max).accepted();}
}'''

CELLS='''class V176BackpackCells {
 public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){
  var xsxEquipmentReadOnce=new dev.obsidiannetwork.core.EquipmentCellStore[4];
  var xsxStorageReadOnce=new dev.obsidiannetwork.core.StorageCellStore[4];
  long left=requested;
  for(int phase=0;phase<2&&left>0;phase++){
    for(int i=1;i<=3&&left>0;i++){
      if(cellStack.getItem() instanceof EquipmentCellItem equipment){
       var store=xsxEquipmentReadOnce[i];
       if(store==null){store=equipment.readStore(cellStack);xsxEquipmentReadOnce[i]=store;}
       var accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);
       store.insertExact(d.key(),d.canonicalPayload(),accepted);
      } else if(cellStack.getItem() instanceof StorageCellItem cell){
       var store=xsxStorageReadOnce[i];
       if(store==null){store=cell.readStore(cellStack);xsxStorageReadOnce[i]=store;}
       var accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);
       store.insertExact(d.key(),d.canonicalPayload(),accepted);
      }
    }
  }
  if(left<requested)writeSlots(bag,replacements);
  return new Transfer(requested-left,left);
 }
 public static List<Entry> entries(ItemStack bag){return List.of();}
}'''

def apply_patch(b=BE,c=CELLS):
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp)/"dev/obsidiannetwork/backpack"
  root.mkdir(parents=True)
  be=root/"NetworkBackpackBlockEntity.java"
  cells=root/"V176BackpackCells.java"
  be.write_text(b,encoding="utf-8")
  cells.write_text(c,encoding="utf-8")
  run=subprocess.run([sys.executable,str(PATCH)],
      env={**os.environ,"V1_SOURCE_ROOT":temp},
      capture_output=True,text=True)
  return run,be.read_text("utf-8"),cells.read_text("utf-8")

def model(stream,capacity,use_runtime):
 """Reference vs transient Store model, persistence on each accepted insert."""
 disks=[{} for _ in range(3)]
 serialized=[{} for _ in range(3)]
 reads=0
 writes=0
 cache=None
 for op,key,requested,commit in stream:
  if op=="replace":
   disks=[dict(x) for x in serialized]
   cache=None
   continue
  if op=="extract":
   for d in disks:
    taken=min(requested,d.get(key,0))
    if taken:
     d[key]-=taken
     if d[key]==0:del d[key]
     requested-=taken
     break
   serialized=[dict(x) for x in disks]
   cache=None
   continue
  if cache is None:
   cache=[dict(x) for x in serialized]
   reads+=3
  staged=[dict(d) for d in cache] if not use_runtime else cache
  before=[dict(d) for d in serialized]
  left=requested
  for phase in (0,1):
   for d in staged:
    if left<=0:break
    present=d.get(key,0)>0
    if present!=(phase==0):continue
    used=sum(d.values())
    accepted=min(left,max(0,capacity-used))
    if accepted>0:
     d[key]=d.get(key,0)+accepted
     left-=accepted
  if left<requested:
   writes+=1
   serialized=[dict(x) for x in staged]
  if not commit:
   serialized=before
   cache=None
   continue
  if not use_runtime:
   cache=None
  else:
   cache=staged
 return serialized,reads,writes

class B1269RuntimeSafety(unittest.TestCase):
 def test_patch_applies_to_b1265_source_shape(self):
  ast.parse(PATCH.read_text("utf-8"))
  r,be,cells=apply_patch()
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("B1269_NATIVE_BACKPACK_INGRESS_RUNTIME_REUSE_AND_ROLLBACK_GUARDS_PASS",r.stdout)
  self.assertIn("xsxIngressRuntimeCache.resetFor(before)",be)
  self.assertIn("xsxIngressRuntimeCache.invalidate()",be)
  self.assertIn("xsxIngressRuntimeCache.rebase(updated)",be)
  self.assertIn("cableJournal.updateSnapshots(tx)",be)
  self.assertIn("V176BackpackCells.extract(",be)
  self.assertIn("insertWithRuntime(world,bag,incoming,requested,null)",cells)
  self.assertIn("IngressRuntimeCache cache",cells)
  self.assertIn("cache==null",cells)
  self.assertIn("java.util.Arrays.fill(equipment,null)",cells)
  self.assertIn("java.util.Arrays.fill(storage,null)",cells)
  self.assertEqual(cells.count("public static Transfer insertWithRuntime("),1)

 def test_fail_closed_drift_is_atomic_across_both_files(self):
  for b,c in ((BE.replace("backpack=before.copy();","backpack=before;"),CELLS),
              (BE,CELLS.replace("new dev.obsidiannetwork.core.StorageCellStore[4]",
                                "new dev.obsidiannetwork.core.StorageCellStore[3]"))):
   r,new_b,new_c=apply_patch(b,c)
   self.assertNotEqual(r.returncode,0)
   self.assertIn("B1269_RUNTIME_SOURCE_DRIFT",r.stderr)
   self.assertEqual(new_b,b)
   self.assertEqual(new_c,c)

 def test_authoritative_counts_randomized_and_rollbacks(self):
  rng=random.Random(1269)
  old_reads=0
  new_reads=0
  for _ in range(1000):
   capacity=rng.randint(64,600)
   stream=[]
   for i in range(rng.randint(1,120)):
    op=rng.choices(["insert","extract","replace"],weights=[90,8,2])[0]
    stream.append((op,"item"+str(rng.randint(0,6)),
                   rng.randint(1,64),rng.random()>0.10))
   old,r0,w0=model(stream,capacity,False)
   new,r1,w1=model(stream,capacity,True)
   self.assertEqual(old,new)
   self.assertEqual(w0,w1)
   old_reads+=r0
   new_reads+=r1
  self.assertLess(new_reads,old_reads)

 def test_workflow_stages_patch_but_preserves_release_lock(self):
  workflow=WORKFLOW.read_text("utf-8")
  self.assertIn(PATCH.name,workflow)
  self.assertIn(Path(__file__).name,workflow)
  self.assertLess(workflow.index("apply-v176-b1265-backpack-cable-burst-fastpath.py"),
                  workflow.index(PATCH.name))
  # Feature branch is source staging, not a claimed ingame-green build.
  self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text("utf-8"))

 def test_no_throttling_and_no_changes_to_non_backpack_system(self):
  script=PATCH.read_text("utf-8")
  for forbidden in ("Thread.sleep(","tickCount%","ITEM_BUDGET",
                    "features/v175/","StorageDriveBlockEntity.java",
                    "StorageNetwork.java","setItemInHand("):
   self.assertNotIn(forbidden,script)

if __name__=="__main__":
 unittest.main()
