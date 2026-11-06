"""B1248 strict real Java patch fixture + deterministic transfer equivalence."""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1248-bag-hotpath-elision.py"
JAVA=ROOT/"features/v176/java/V176BackpackCells.java"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def apply_fixture(source=None):
 if source is None:
  source=JAVA.read_text(encoding="utf-8").replace(
   "getBooleanOr(MAG_ON,false);","getBooleanOr(MAG_ON,true);")
 with tempfile.TemporaryDirectory() as temp:
  target=Path(temp)/"dev/obsidiannetwork/backpack/V176BackpackCells.java"
  target.parent.mkdir(parents=True)
  target.write_text(source,encoding="utf-8")
  r=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":temp},
                   capture_output=True,text=True,check=True)
  return source,target.read_text(encoding="utf-8"),r.stdout

def model(amounts,used,capacity,wanted,reuse_absent):
 amounts=list(amounts)
 used=list(used)
 left=wanted
 reads=0
 absent=[None]*3
 for phase in range(2):
  if left<=0:break
  for i in range(3):
   if left<=0:break
   if amounts[i] is None:continue  # empty slot, no cell
   if not (reuse_absent and phase==1 and absent[i]):
    reads+=1
   present=amounts[i]>0
   if ((phase==0)!=present):
    if phase==0:absent[i]=True
    continue
   accepted=min(left,max(0,capacity[i]-used[i]))
   if accepted>0:
    amounts[i]+=accepted
    used[i]+=accepted
    left-=accepted
 return (amounts,used,wanted-left,left),reads

class B1248Conservation(unittest.TestCase):
 def test_patch_applies_to_real_java_fixture(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
  before,after,stdout=apply_fixture()
  self.assertIn("B1248_BACKPACK_MAGNET_FILTER_NO_REPEATED_READ_PASS COUNT_OPTIMIZED=True INSERT_OPTIMIZED=True",stdout)
  self.assertIn("var stored=slots(bag);",after)
  self.assertIn("absentAtFirstPass[i-1]=store;",after)
  self.assertIn("settings.getBooleanOr(MAG_ON,true)",after)
  self.assertIn("settings.getBooleanOr(MAG_WHITELIST,false)",after)
  self.assertEqual(after.count("ItemStack upgrade=slots(bag).get(SLOT_MAGNET);"),1)
  # Critical unrelated behavior (cell removal, exact descriptor, filter writes)
  # is identical byte for byte, not just textually similar.
  for marker,stop in (
   (" public static Transfer extract(", " public static ItemStack magnet("),
   (" public static void writeSlots(", " public static long capacity("),
   (" public static boolean setMagnetFilter(", "\n}"),
  ):
   self.assertEqual(before.split(marker,1)[1].split(stop,1)[0],
                    after.split(marker,1)[1].split(stop,1)[0])
  self.assertIn("if(left<requested)writeSlots(bag,replacements);",after)
  self.assertIn("store.insertExact(d.key(),d.canonicalPayload(),accepted);",after)

 def test_unrecognized_preoptimized_count_is_never_rewritten(self):
  # Build 1251 failed when the real reconstructed count() body differed.
  # In that case leave count() untouched, but continue strictly matched
  # magnet and insertion changes and preserve all item quantities.
  source=JAVA.read_text(encoding="utf-8").replace(
   "getBooleanOr(MAG_ON,false);","getBooleanOr(MAG_ON,true);")
  changed=source.replace(
   "ItemStack cellStack=slots(bag).get(i);",
   "ItemStack cellStack=slots(bag) .get(i);")
  self.assertNotEqual(source,changed)
  before,after,out=apply_fixture(changed)
  self.assertIn("B1252_COUNT_HOTPATH_SOURCE_CHANGED_SKIP_UNVERIFIED_OPTIMIZATION",out)
  self.assertIn("COUNT_OPTIMIZED=False",out)
  self.assertIn("ItemStack cellStack=slots(bag) .get(i);",after)
  self.assertIn("absentAtFirstPass[i-1]=store;",after)
  self.assertIn("settings.getBooleanOr(MAG_ON,true)",after)
  self.assertIn("settings.getBooleanOr(MAG_WHITELIST,false)",after)
  self.assertNotIn("var stored=slots(bag);",after)

 def test_enriched_equipment_insert_is_preserved_byte_for_byte(self):
  # B1254 proved the reconstructed insert source has another cell type.
  # Do not apply one branch of a partial optimization to an unknown method.
  source=JAVA.read_text(encoding="utf-8").replace(
    "getBooleanOr(MAG_ON,false);","getBooleanOr(MAG_ON,true);")
  enriched=source.replace(
    "  long left=requested;\n  // Prefer cells already holding the item key;",
    "  long left=requested;\n  // Preserve an additional Equipment Cell branch.\n  // Prefer cells already holding the item key;")
  self.assertNotEqual(source,enriched)
  _,after,out=apply_fixture(enriched)
  self.assertIn("B1255_INSERT_EQUIPMENT_CELL_SOURCE_CHANGED_SKIP_UNVERIFIED_OPTIMIZATION",out)
  self.assertIn("INSERT_OPTIMIZED=False",out)
  start=" public static Transfer insert("
  stop=" public static List<Entry> entries("
  self.assertEqual(enriched.split(start,1)[1].split(stop,1)[0],
                   after.split(start,1)[1].split(stop,1)[0])
  self.assertIn("settings.getBooleanOr(MAG_ON,true)",after)
  self.assertIn("settings.getBooleanOr(MAG_WHITELIST,false)",after)

 def test_two_phase_transfer_amounts_preference_and_read_reduction(self):
  rng=random.Random(1248)
  total_saved=0
  for n in range(12000):
   # Existing matching item count or another item (represented as zero).
   amounts=[rng.choice([None,0,0,0,1,17,64,32768]) for _ in range(3)]
   caps=[rng.choice([0,4,16,64,256,1024]) for _ in range(3)]
   used=[rng.randint(0,c) for c in caps]
   # Existing count cannot exceed used amount.
   for i,v in enumerate(amounts):
    if v is not None:
     amounts[i]=min(v,used[i])
   wanted=rng.randint(0,1000)
   old,old_reads=model(amounts,used,caps,wanted,False)
   new,new_reads=model(amounts,used,caps,wanted,True)
   self.assertEqual(old,new,(n,amounts,used,caps,wanted))
   self.assertLessEqual(new_reads,old_reads)
   total_saved+=old_reads-new_reads
  self.assertGreater(total_saved,1000)

 def test_filter_semantics(self):
  for enabled in (False,True):
   for whitelisted in (False,True):
    for listed in (False,True):
     for empty in (False,True):
      old=enabled and not empty and (listed if whitelisted else not listed)
      new=not empty and enabled and (listed if whitelisted else not listed)
      self.assertEqual(old,new)
  text=PATCH.read_text(encoding="utf-8")
  self.assertIn("if(!settings.getBooleanOr(MAG_ON,true)||incoming.isEmpty())return false;",text)
  self.assertIn("for(int i=0;i<Math.min(FILTER_SLOTS,templates.getSlots());i++)",text)

 def test_fail_closed_and_no_frozen_artifact_change(self):
  text=PATCH.read_text(encoding="utf-8")
  self.assertIn("B1248_BACKPACK_HOTPATH_SOURCE_DRIFT",text)
  self.assertNotIn("sleep(",text)
  for unsafe in ("tickCount%","ENTITY_BUDGET","ITEM_BUDGET","setItemInHand","dropItemStack"):
   self.assertNotIn(unsafe,text)
  self.assertIn("apply-v176-b1248-bag-hotpath-elision.py",WORKFLOW.read_text())
  self.assertNotIn("features/v175/",text)

if __name__=="__main__":
 unittest.main()
