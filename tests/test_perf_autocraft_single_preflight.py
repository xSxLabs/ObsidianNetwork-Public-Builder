#!/usr/bin/env python3
"""Synthetic fail-closed safety tests for double-preflight elimination.

Real Java compilation, full GameTests and an ingame Spark A/B comparison are
required before shipping; this file does not trigger a JAR.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"patches/perf-autocraft-single-exact-insert-preflight.py"
STORAGE="""public class StorageNetwork {
   public long insertExact(ItemKey key, byte[] canonicalPayload, long requested) {
      if (requested <= 0L) {
         return 0L;
      } else {
         long planned = this.previewInsertExact(key, canonicalPayload, requested);
         if (planned <= 0L) {
            return 0L;
         } else {
            long remaining = planned;
            long insertedTotal = 0L;
            if (EquipmentEligibility.isEquipment(key)) {
               for (EquipmentCellStore cell : this.equipmentCells) {
                  if (remaining == 0L) break;
                  long accepted = cell.insertExact(key, canonicalPayload, remaining);
                  if (accepted > 0L) { remaining -= accepted; insertedTotal += accepted; this.index.applyDelta(key, accepted); }
               }
            }

            try {
               LinkedHashSet<StorageCellStore> existing = this.sources.get(key);
               if (existing != null) {
                  for (StorageCellStore cell : List.copyOf(existing)) {
                     if (remaining == 0L) {
                        break;
                     }
                     long accepted = cell.insertExact(key, canonicalPayload, remaining);
                     if (accepted > 0L) {
                        remaining -= accepted;
                        insertedTotal = Math.addExact(insertedTotal, accepted);
                        this.index.applyDelta(key, accepted);
                     }
                  }
               }
               for (StorageCellStore cell : this.cells) {
                  if (remaining == 0L) {
                     break;
                  }
                  if (cell.amount(key) == 0L) {
                     long accepted = cell.insertExact(key, canonicalPayload, remaining);
                     if (accepted > 0L) {
                        remaining -= accepted;
                        insertedTotal = Math.addExact(insertedTotal, accepted);
                        this.index.applyDelta(key, accepted);
                        this.sources.computeIfAbsent(key, ignored -> new LinkedHashSet<>()).add(cell);
                     }
                  }
               }
               if (remaining != 0L) {
                  throw new IllegalStateException("exact insertion violated successful preflight");
               } else {
                  return insertedTotal;
               }
            } catch (RuntimeException var17) {
               if (insertedTotal > 0L) {
                  try {
                     long rolledBack = this.extract(key, insertedTotal);
                     if (rolledBack != insertedTotal) {
                        throw new IllegalStateException("exact insertion rollback incomplete");
                     }
                  } catch (RuntimeException var16) {
                     var17.addSuppressed(var16);
                  }
               }
               throw var17;
            }
         }
      }
   }

   public long extract(ItemKey key, long requested) {return 0;}
}
"""
SERVICE="""public class MinecraftAutocraftingService {
   private MinecraftAutocraftingService.CraftJob consumeReservedCraft(MinecraftAutocraftingService.CraftJob j, AutocraftTemplate t) {
      if (j.remainingCrafts() <= 0L) return j;
      long output = j.outputCount();
      if (this.runtime.storage().previewInsertExact(j.output().key(), j.output().canonicalPayload(), output) != output) return j;
      ArrayList<MinecraftAutocraftingService.BufferedInput> next = new ArrayList<>();
      for (MinecraftAutocraftingService.BufferedInput b : j.reserved()) {
         long perCraft = b.perCraft();
         if (perCraft <= 0L || b.buffered() < perCraft) return j;
         next.add(new MinecraftAutocraftingService.BufferedInput(b.descriptor(), perCraft, b.target() - perCraft, b.buffered() - perCraft));
      }
      this.runtime.descriptors().registerKnown(j.output().key(), j.output().canonicalPayload());
      long inserted = this.runtime.storage().insertExact(j.output().key(), j.output().canonicalPayload(), output);
      if (inserted != output) {
         if (inserted > 0L) this.runtime.storage().extract(j.output().key(), inserted);
         return j;
      }
      return new MinecraftAutocraftingService.CraftJob(j.id(), j.output(), j.outputCount(), j.remainingCrafts() - 1L, List.copyOf(next));
   }

   private void rollbackInputs(List<?> removed) {}
}
"""

def prepare(root,storage=STORAGE,service=SERVICE):
    for filename,text in (
        ("core/StorageNetwork.java",storage),
        ("platform/MinecraftAutocraftingService.java",service)
    ):
        p=root/"dev/obsidiannetwork"/filename
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text)

def run(root):
    return subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True,
                          env={**os.environ,"V1_SOURCE_ROOT":str(root)})

class AutocraftSinglePreview(unittest.TestCase):
    def test_two_calls_become_one_and_all_storage_rollback_remains(self):
        ast.parse(SCRIPT.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            prepare(root)
            result=run(root)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            ss=(root/"dev/obsidiannetwork/core/StorageNetwork.java").read_text()
            cc=(root/"dev/obsidiannetwork/platform/MinecraftAutocraftingService.java").read_text()
            self.assertEqual(ss.count("public long insertExact("),1)
            self.assertEqual(ss.count("public long insertExactFollowingPreview("),1)
            self.assertEqual(ss.count("private long insertExactChecked("),1)
            self.assertIn("insertExactChecked(key, canonicalPayload, requested, false)",ss)
            self.assertIn("insertExactChecked(key, canonicalPayload, requested, true)",ss)
            self.assertIn("fullPreflightAlreadyPassed ? requested : this.previewInsertExact(",ss)
            self.assertIn("this.sources.computeIfAbsent(key, ignored -> new LinkedHashSet<>()).add(cell)",ss)
            self.assertIn("long rolledBack = this.extract(key, insertedTotal)",ss)
            self.assertIn('throw new IllegalStateException("exact insertion rollback incomplete")',ss)
            self.assertIn("this.index.applyDelta(key, accepted)",ss)
            self.assertIn("this.runtime.storage().insertExactFollowingPreview(",cc)
            self.assertEqual(cc.count("this.runtime.storage().previewInsertExact("),1)
            self.assertIn("if (perCraft <= 0L || b.buffered() < perCraft) return j",cc)
            self.assertIn("if (inserted > 0L) this.runtime.storage().extract(",cc)
            self.assertIn("List.copyOf(next)",cc)
            self.assertNotEqual(run(root).returncode,0,"double patching must fail closed")

    def test_any_intervening_storage_write_must_prevent_the_fast_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            modified=SERVICE.replace(
                "this.runtime.descriptors().registerKnown(j.output().key(), j.output().canonicalPayload());",
                "this.runtime.storage().extract(j.output().key(), 1L);\n"
                "      this.runtime.descriptors().registerKnown(j.output().key(), j.output().canonicalPayload());")
            prepare(root,service=modified)
            before=(root/"dev/obsidiannetwork/core/StorageNetwork.java").read_text()
            r=run(root)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual((root/"dev/obsidiannetwork/core/StorageNetwork.java").read_text(),before)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prepare(root,storage=STORAGE.replace("long rolledBack = this.extract","long lost = this.extract"))
            self.assertNotEqual(run(root).returncode,0)

    def test_no_changes_to_unrelated_item_storage(self):
        script=SCRIPT.read_text()
        self.assertIn("this.index.applyDelta(key, accepted);",script)
        self.assertIn("throw var17;",script)
        self.assertNotIn("ThreadLocal",script)
        self.assertNotIn("forceLoad",script)
        self.assertNotIn("setChunkForced",script)

if __name__=="__main__":
    unittest.main()
