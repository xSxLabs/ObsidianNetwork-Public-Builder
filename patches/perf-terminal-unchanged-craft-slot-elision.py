#!/usr/bin/env python3
"""Do not re-write identical server Crafting Terminal inventory slots.

In the compiled prepatch TerminalInventoryBlockEntity.setCraftItem every call
extracts the old resource and inserts the new one inside separate NeoForge
Transaction.openRoot() calls, then dirties the BE. SlotsChanged writes *all*
nine slots for a one-slot crafting-grid change. An EXACT existing/new stack
match (item, components, count) makes those transactions observationally
redundant. No batching, NBT rewrite, changed-slot storage, recipe, FE, or
rollback semantics are altered.

Fail closed if the precise setter + its transaction body are not recognized.
"""
from pathlib import Path
import os
import re

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"blockentity/TerminalInventoryBlockEntity.java"
menu=root/"menu/StorageTerminalMenu.java"
s=p.read_text(encoding="utf-8")
m=menu.read_text(encoding="utf-8")
marker="XSXLABS_TERMINAL_UNCHANGED_CRAFT_SLOT_ELISION_V1"
assert marker not in s
assert "this.craftSlots" in m and "setCraftItem(" in m and "slotsChanged(" in m
start_re=re.compile(
    r'(?P<head>public\s+void\s+setCraftItem\s*\(\s*int\s+(?P<slot>[a-zA-Z_]\w*)\s*,'
    r'\s*ItemStack\s+(?P<stack>[a-zA-Z_]\w*)\s*\)\s*\{)'
)
matches=list(start_re.finditer(s))
assert len(matches)==1, ("TerminalInventoryBlockEntity setter signature drift",len(matches))
match=matches[0]
start=match.end()
next_method=re.search(r'\n\s+(?:public|protected|private)\s+(?:static\s+)?'
    r'(?:void|ItemStack|boolean|int|long|[A-Z]\w*)\s+\w+\s*\(', s[start:])
assert next_method, "Cannot bound craft-slot setter"
section=s[start:start+next_method.start()]
for guard in ("this.crafting.getResource(", "this.crafting.extract(", "this.crafting.insert(",
              "Transaction.openRoot()", "this.setChanged()"):
    assert guard in section, "Craft-slot persistence code drift: "+guard
# This setter alone owns nine slots. The getter is the authoritative handler
# view and returns the reconstructed full ItemStack with count + components.
assert "public ItemStack getCraftItem(int" in s
assert "ItemStack.matches(" not in section, "Craft slot setter already has equality logic"
guard=(
    "\n      // XSXLABS_TERMINAL_UNCHANGED_CRAFT_SLOT_ELISION_V1\n"
    "      // Preserve all writes for count/component changes; avoid only exact no-ops.\n"
    f"      if ({match.group('slot')} >= 0 && {match.group('slot')} < 9 && "
    f"ItemStack.matches(this.getCraftItem({match.group('slot')}), {match.group('stack')})) return;"
)
updated=s[:start]+guard+s[start:]
assert updated.count(marker)==1
assert updated.count("Transaction.openRoot()")==s.count("Transaction.openRoot()")
assert updated.count("this.crafting.extract(")==s.count("this.crafting.extract(")
assert updated.count("this.crafting.insert(")==s.count("this.crafting.insert(")
assert updated.count("this.setChanged()")==s.count("this.setChanged()")
p.write_text(updated,encoding="utf-8")
print("TERMINAL_UNCHANGED_CRAFT_SLOT_TRANSACTIONS_ELIDED_V1 PASS")
