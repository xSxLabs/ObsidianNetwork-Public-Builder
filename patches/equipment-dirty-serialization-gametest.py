#!/usr/bin/env python3
"""Add a test-only regression for the equipment dirty-serialization cache.

Runs in both the before-final-patches and post-final-patches GameTest passes.
This patch must not change production Java or the published JAR.
"""
from pathlib import Path
import os

root = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
p = root / "dev/obsidiannetwork/build103/Build103GameTests.java"
source = p.read_text()
# YAML block scalars remove their own indentation before writing the Java
# heredoc. Match source tokens, not indentation copied from the workflow.
anchor = 'System.out.println("FULL_EQUIPMENT_CELL_REINSERT_NS "+elapsed+" cycles=25 count=64000 types=257");'
assert source.count(anchor) == 1, "64k GameTest anchor changed; fail closed"
after_anchor = source.split(anchor, 1)[1]
import re
assert re.match(r'\s*h\.succeed\(\);', after_anchor), "GameTest success anchor moved"
injection = """                // Test-only: a committed snapshot must remain correct across live
                // mutations and repeated materialization. This guards against
                // stale NBT / lost items from the dirty-serialization optimization.
                try {
                  if (!drive.insertCellAt(0, stack))
                    throw new IllegalStateException("Dirty cache fixture reinsertion failed");
                  var equipmentField = dev.obsidiannetwork.blockentity.StorageDriveBlockEntity.class.getDeclaredField("equipmentCells");
                  equipmentField.setAccessible(true);
                  var cells = (dev.obsidiannetwork.core.EquipmentCellStore[])equipmentField.get(drive);
                  var attached = cells[0];
                  if (attached == null || attached.amount(key) != 63744L || attached.free() != 0L)
                    throw new IllegalStateException("Dirty cache fixture runtime mismatch");
                  var first = drive.cellStack(0);
                  if (item.readStore(first).amount(key) != 63744L)
                    throw new IllegalStateException("Initial materialized snapshot mismatch");
                  if (!net.minecraft.world.item.ItemStack.matches(first, drive.cellStack(0)))
                    throw new IllegalStateException("Clean materialization changed stack");
                  if (attached.extract(key, 7L) != 7L)
                    throw new IllegalStateException("Live equipment extract failed");
                  var reduced = item.readStore(drive.cellStack(0));
                  if (reduced.amount(key) != 63737L || reduced.types() != 257)
                    throw new IllegalStateException("Dirty snapshot stale after extract");
                  if (attached.insertExact(key, new byte[0], 7L) != 7L)
                    throw new IllegalStateException("Live equipment restore failed");
                  var restored = item.readStore(drive.cellStack(0));
                  if (restored.amount(key) != 63744L || restored.free() != 0L || restored.types() != 257)
                    throw new IllegalStateException("Dirty snapshot stale after restore");
                  var returned = drive.removeCellAt(0);
                  if (returned.isEmpty() || item.readStore(returned).amount(key) != 63744L)
                    throw new IllegalStateException("Dirty snapshot lost on cell removal");
                  System.out.println("EQUIPMENT_DIRTY_SERIALIZATION_MUTATION_GAMETEST PASS");
                } catch (ReflectiveOperationException error) {
                  throw new IllegalStateException("Test-only equipment reflection failed", error);
                }
"""
updated = source.replace(anchor, anchor + '\n' + injection, 1)
assert updated.count("EQUIPMENT_DIRTY_SERIALIZATION_MUTATION_GAMETEST PASS") == 1
p.write_text(updated)
print("EQUIPMENT_DIRTY_SERIALIZATION_MUTATION_TEST_FIXTURE_V1 PASS")
