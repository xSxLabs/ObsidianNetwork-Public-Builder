#!/usr/bin/env python3
"""Elide only the duplicate StorageNetwork preflight for a reserved craft.

Actual server hot path:
  consumeReservedCraft: previewInsertExact(output, count)
  validate immutable BufferedInput snapshots, registerKnown descriptor
  StorageNetwork.insertExact: previewInsertExact(output, count) AGAIN
  exact item insertion with index deltas and a strict rollback.

On the same server thread, the intermediate steps do NOT mutate storage.
Keep public insertExact() unchanged for all other callers; expose a separate,
explicitly named method that takes the already-approved full preflight.
The entire old insertion/rollback body stays byte-for-byte the same,
except the source of 'planned'. Refuse unknown source shapes.

This patch MUST be paired with real server compile/GameTests and an A/B spark
before calling the observed MSPT regression repaired.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
storage=root/"core/StorageNetwork.java"
service=root/"platform/MinecraftAutocraftingService.java"
s=storage.read_text(encoding="utf-8")
c=service.read_text(encoding="utf-8")
marker="XSXLABS_AUTOCRAFT_EXACT_SINGLE_PREFLIGHT_V1"

assert marker not in s and marker not in c
begin="   public long insertExact(ItemKey key, byte[] canonicalPayload, long requested) {"
finish="   public long extract(ItemKey key, long requested) {"
assert s.count(begin)==1 and s.count(finish)==1
start=s.index(begin)
end=s.index(finish,start)
body=s[start:end]
needle="long planned = this.previewInsertExact(key, canonicalPayload, requested);"
assert body.count(needle)==1
for token in (
   "if (requested <= 0L)", "if (planned <= 0L)",
   "remaining -= accepted;", "this.index.applyDelta(key, accepted);",
   "this.sources.computeIfAbsent(key, ignored -> new LinkedHashSet<>()).add(cell);",
   'throw new IllegalStateException("exact insertion violated successful preflight");',
   'long rolledBack = this.extract(key, insertedTotal);',
   'throw new IllegalStateException("exact insertion rollback incomplete");',
   "throw var17;",
):
    assert token in body, "Original exact storage insertion/rollback contract changed: "+token
assert body.count("return insertedTotal;")==1
assert body.count("previewInsertExact(")==1
assert body.count("this.equipmentCells")==1
assert body.count("this.sources.get(key)")==1
assert body.count("for (StorageCellStore cell : this.cells)")==1

c_start="private MinecraftAutocraftingService.CraftJob consumeReservedCraft("
c_end="private void rollbackInputs("
assert c.count(c_start)==1 and c.count(c_end)==1
a=c.index(c_start)
b=c.index(c_end,a)
method=c[a:b]
old_call="long inserted = this.runtime.storage().insertExact(j.output().key(), j.output().canonicalPayload(), output);"
preview="if (this.runtime.storage().previewInsertExact(j.output().key(), j.output().canonicalPayload(), output) != output) return j;"
assert method.count(old_call)==1 and method.count(preview)==1
assert method.index(preview)<method.index(old_call)
for token in (
   "if (j.remainingCrafts() <= 0L) return j;",
   "for (MinecraftAutocraftingService.BufferedInput b : j.reserved())",
   "if (perCraft <= 0L || b.buffered() < perCraft) return j;",
   "this.runtime.descriptors().registerKnown(j.output().key(), j.output().canonicalPayload());",
   "if (inserted != output)", "if (inserted > 0L) this.runtime.storage().extract(j.output().key(), inserted);",
   "List.copyOf(next)",
):
    assert method.count(token)==1, "Autocraft atomic reservation/rollback contract changed: "+token
# No other call or storage mutation may appear between the accepted preflight
# and the checked insertion except the validated immutable-buffer processing
# and catalogue-only registration.
between=method[method.index(preview)+len(preview):method.index(old_call)]
assert "storage()." not in between and "runtime.storage(" not in between
assert "registerKnown(j.output().key(), j.output().canonicalPayload())" in between
assert ".extract(" not in between and ".insert(" not in between
assert "this.runtime.storage()." not in between

# Wrapper retains old public insertion behavior; only reserved crafting uses
# the trusted full preflight variant.
new_head="""   // XSXLABS_AUTOCRAFT_EXACT_SINGLE_PREFLIGHT_V1
   public long insertExact(ItemKey key, byte[] canonicalPayload, long requested) {
      return insertExactChecked(key, canonicalPayload, requested, false);
   }

   /** Only for a full exact preview accepted on the same server thread with
       no intervening storage mutations. Never call directly from a GUI. */
   public long insertExactFollowingPreview(ItemKey key, byte[] canonicalPayload, long requested) {
      return insertExactChecked(key, canonicalPayload, requested, true);
   }

   private long insertExactChecked(ItemKey key, byte[] canonicalPayload, long requested, boolean fullPreflightAlreadyPassed) {"""
assert body.startswith(begin)
updated_body=new_head+body[len(begin):]
updated_body=updated_body.replace(needle,
  "long planned = fullPreflightAlreadyPassed ? requested : this.previewInsertExact(key, canonicalPayload, requested);",1)
assert updated_body.count("fullPreflightAlreadyPassed ? requested : this.previewInsertExact(")==1
assert updated_body.count("long rolledBack = this.extract(key, insertedTotal);")==1
assert updated_body.count("this.index.applyDelta(key, accepted);")==body.count("this.index.applyDelta(key, accepted);")
s_new=s[:start]+updated_body+s[end:]
c_new=c[:a]+method.replace(old_call,
  "long inserted = this.runtime.storage().insertExactFollowingPreview(j.output().key(), j.output().canonicalPayload(), output);",1)+c[b:]
assert s_new.count("public long insertExact(")==1
assert s_new.count("public long insertExactFollowingPreview(")==1
assert s_new.count("private long insertExactChecked(")==1
assert c_new.count("insertExactFollowingPreview(")==1
assert c_new.count(preview)==1
assert c_new.count("rollbackInputs(")==c.count("rollbackInputs(")
# Write both only after all checks pass.
storage.write_text(s_new,encoding="utf-8")
service.write_text(c_new,encoding="utf-8")
print("XSXLABS_AUTOCRAFT_EXACT_SINGLE_PREFLIGHT_V1 PASS; general insertExact unchanged; reserved craft preflight once")
