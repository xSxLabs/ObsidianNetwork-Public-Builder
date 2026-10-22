#!/usr/bin/env python3
"""v1.7: keep ALL currently available autocraft inputs out of terminal stock.

Build on the validated v1.6 deferred-reservation implementation. Reservations
stay physically extracted and persisted per job, not merely hidden client-side.
Unfilled future inputs stay pending until produced/inserted; return buffered
inputs on cancellation through the existing capacity-checked restore path.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/platform/MinecraftAutocraftingService.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_AUTOCRAFT_EAGER_PRIVATE_RESERVATIONS_V17"
assert marker not in s,"Reservation patch must only be applied once"
old_queue="long taken = this.runtime.storage().extract(e.getKey(), Math.min(e.getValue(),perCraftNeeds.getOrDefault(e.getKey(),0L)));"
new_queue="""// XSXLABS_AUTOCRAFT_EAGER_PRIVATE_RESERVATIONS_V17
            // Take ALL currently available inputs for this queued request.
            // Storage and the terminal therefore expose only unreserved stock.
            long available = Math.max(0L, this.runtime.storage().index().amount(e.getKey()));
            long taken = available == 0L ? 0L :
                this.runtime.storage().extract(e.getKey(), Math.min(e.getValue(), available));"""
assert s.count(old_queue)==1,"Deferred queue reservation anchor drift"
s=s.replace(old_queue,new_queue,1)
old_refill="""long missing = Math.max(0L, Math.min(b.perCraft() - b.buffered(), b.target() - b.buffered()));
         long taken = missing > 0L ? this.runtime.storage().extract(b.descriptor().key(), missing) : 0L;"""
new_refill="""// Hold any newly available input for the WHOLE outstanding job,
         // not just its next craft. Pending dependencies remain unreserved
         // until produced; the next service tick can acquire them.
         long missing = Math.max(0L, b.target() - b.buffered());
         long stock = missing > 0L ? Math.max(0L,
             this.runtime.storage().index().amount(b.descriptor().key())) : 0L;
         long taken = stock > 0L
             ? this.runtime.storage().extract(b.descriptor().key(), Math.min(missing, stock)) : 0L;"""
assert s.count(old_refill)==1,"Deferred refill reservation anchor drift"
s=s.replace(old_refill,new_refill,1)

# Restoration MUST remain capacity-guarded and exact; no rollback item may
# silently spill into a player's inventory, vanish or be given twice.
for required in (
    "this.canRestoreReserved(c.reserved())",
    "this.restoreReserved(c.reserved());",
    "it.remove();",
    "this.runtime.storage().previewInsertExact(",
    "this.runtime.storage().insertExact(",
    "if (restored != b.buffered()) throw new IllegalStateException(",
    "out.writeLong(b.perCraft());",
    "out.writeLong(b.buffered());",
    "version >= 6 ? in.readLong() : 0L",
    "this.queueMissingDependencies(level, t, needs, reserved);",
):
    assert required in s,"Missing safety contract: "+required
assert "this.craftInstant(level, t, 1L, stone)" not in s
p.write_text(s,encoding="utf-8")
print(marker+" PASS: physical whole-request reservation, eager refill, cancel restore/persistence preserved")
