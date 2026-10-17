#!/usr/bin/env python3
"""Avoid a second equipment-cell decode/attach after an inventory commit.

ItemStacksResourceHandler.onContentsChanged reconciles the runtime when the
transaction commits. insertCellAt used to always reconcile it a second time,
which needlessly re-read large EquipmentCellStore contents and detach/reattach
the cell. If the handler did not reconcile for any reason, fall back to the
original explicit path. Normal StorageCellItem behavior remains unchanged.
"""
from pathlib import Path
import os
import re

root = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
p = root / "dev/obsidiannetwork/blockentity/StorageDriveBlockEntity.java"
s = p.read_text()
start = s.index("public boolean insertCellAt(")
end = s.index("public boolean insertCell(", start)
method = s[start:end]

assert s.count("StorageDriveBlockEntity.this.reconcileRuntimeSlot(index);") == 1, (
    "inventory mutation callback must reconcile the runtime"
)
assert "tx.commit();" in method, "transaction commit anchor changed"
assert method.count("this.reconcileRuntimeSlot(slot);") == 1, (
    "equipment insertion reconciliation anchor changed"
)
assert method.count("this.setChanged();") == 1, "insert mutation marker changed"

pattern = r"(?m)^(\s*)this\.reconcileRuntimeSlot\(slot\);"
replacement = (
    r"\1// Handler onContentsChanged already reconciles committed equipment changes.\n"
    r"\1// Retain the old path when callback reconciliation was not observed.\n"
    r"\1if (!(stack.getItem() instanceof EquipmentCellItem) || this.equipmentCells[slot] == null) {\n"
    r"\1   this.reconcileRuntimeSlot(slot);\n"
    r"\1}"
)
updated, n = re.subn(pattern, replacement, method, count=1)
assert n == 1
s = s[:start] + updated + s[end:]
assert s.count("Handler onContentsChanged already reconciles committed equipment changes.") == 1
p.write_text(s)
print("EQUIPMENT_REDUNDANT_RECONCILE_ELISION_V1 PASS")
