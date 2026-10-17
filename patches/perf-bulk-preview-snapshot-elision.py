#!/usr/bin/env python3
"""Avoid allocating a cell-source snapshot during read-only exact preflight.

This changes only the previewInsertExact() loop over existing sources.
insertExact()/extract() keep their defensive snapshots because they mutate
cells and/or the source set. Fail closed on changed source or a mutable
StorageCellStore preview implementation.
"""
from pathlib import Path
import os

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/core"
network = root / "StorageNetwork.java"
cell = root / "StorageCellStore.java"
source = network.read_text(encoding="utf-8")
cell_source = cell.read_text(encoding="utf-8")

assert source.count("public long previewInsertExact(") == 1
assert source.count("public long insertExact(") == 1
assert cell_source.count("public long previewInsertExact(") == 1
assert cell_source.count("public long insertExact(") == 1

# Reject mutable preflight logic, instead of changing iteration semantics
# when a cell's preview could indirectly update the source collection.
cell_preview = cell_source.split("public long previewInsertExact(", 1)[1].split("public long insertExact(", 1)[0]
for forbidden in ("this.mutationListener.run(", "this.amounts.put(", "this.amounts.remove(",
                  "this.descriptors.put(", "this.descriptors.remove(", "this.used ="):
    assert forbidden not in cell_preview, "StorageCellStore preflight became mutable: " + forbidden

a = source.index("public long previewInsertExact(")
b = source.index("public long insertExact(", a)
before, preview, after = source[:a], source[a:b], source[b:]
old = "for (StorageCellStore cell : List.copyOf(existing)) {"
new = "for (StorageCellStore cell : existing) { // XSXLABS_BULK_READONLY_PREVIEW_NO_SNAPSHOT_V1"
assert preview.count(old) == 1, "Expected exactly one existing-source preflight loop"
assert "remaining -= cell.previewInsertExact(key, canonicalPayload, remaining);" in preview
assert "this.sources.get(key)" in preview
assert "this.sources.computeIfAbsent(" not in preview
assert "this.sources.remove(" not in preview
assert new not in preview
updated = before + preview.replace(old, new, 1) + after
assert updated[:a] == before and updated.endswith(after)
network.write_text(updated, encoding="utf-8")
print("BULK_READONLY_PREVIEW_SNAPSHOT_ELISION_V1 PASS")
