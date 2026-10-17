#!/usr/bin/env python3
"""Only serialize a live equipment cell when its contents have changed.

The serialized ItemStack is kept as the last committed snapshot. Mutations
invalidate that snapshot through the EquipmentCellStore mutation listener.
"""
from pathlib import Path
import os
p=Path(os.environ.get("V1_SOURCE_ROOT","work/src/main/java"))/"dev/obsidiannetwork/blockentity/StorageDriveBlockEntity.java"
s=p.read_text()
field="private final EquipmentCellStore[] equipmentCells = new EquipmentCellStore[StorageDriveRuntime.SLOTS];"
assert s.count(field)==1,"equipment cell field changed"
s=s.replace(field,field+"\n    private final boolean[] equipmentSerializationDirty = new boolean[StorageDriveRuntime.SLOTS];",1)
# Slot replacements must never inherit a previous cell's clean state.
anchor="StorageDriveBlockEntity.this.reconcileRuntimeSlot(index);"
assert s.count(anchor)==1,"inventory slot replacement hook changed"
s=s.replace(anchor,"StorageDriveBlockEntity.this.equipmentSerializationDirty[index]=true;\n          "+anchor,1)
# Runtime reconstruction starts from deserialized snapshots; the first save can
# conservatively rewrite them, but later saves need not encode unchanged data.
anchor="this.drive = new StorageDriveRuntime(this::setChanged);"
assert s.count(anchor)==1,"runtime reconstruction anchor changed"
s=s.replace(anchor,"java.util.Arrays.fill(this.equipmentSerializationDirty,true);\n       "+anchor,1)
# Attach invalidation to every equipment store mutation, including mutations
# performed by network operations after the cell is inserted.
import re
pattern=r'(this\.equipmentCells\[(\w+)\]\.setMutationListener\()this::setChanged(\);)'
hits=list(re.finditer(pattern,s))
assert len(hits)>=1,"equipment mutation listener not found"
assert s.count("setMutationListener(")==len(hits),"untracked equipment mutation listener: unsafe cache"
s=re.sub(pattern,lambda m:m.group(1)+"() -> { this.equipmentSerializationDirty["+m.group(2)+"]=true; this.setChanged(); });",s)
# Avoid expensive component encoding when the last materialized stack still
# represents the live cell. The mutation listener guarantees invalidation.
needle="if (equipment != null && !shell.isEmpty() && shell.getItem() instanceof EquipmentCellItem item) {"
assert s.count(needle)==1,"materialization guard changed"
s=s.replace(needle,needle+"\n             if (!StorageDriveBlockEntity.this.equipmentSerializationDirty[index]) return;",1)
needle="item.writeStore(copy,equipment); this.stacks.set(index,copy);"
assert s.count(needle)==1,"equipment writeStore instrumentation anchor changed"
s=s.replace(needle,needle+" StorageDriveBlockEntity.this.equipmentSerializationDirty[index]=false;",1)
p.write_text(s)
print("EQUIPMENT_DIRTY_SERIALIZATION_V1 PASS listener_sites=",len(hits))
