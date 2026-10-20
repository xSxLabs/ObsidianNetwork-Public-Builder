#!/usr/bin/env python3
"""Persist one 3x3 terminal grid update in one atomic NeoForge transaction.

The previous menu loop calls setCraftItem up to nine times; each changed slot
opens separate extraction and insertion root transactions. Keep that setter
for other callers, but persist the menu's complete grid in one transaction.
"""
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
menu=root/"menu/StorageTerminalMenu.java"
be=root/"blockentity/TerminalInventoryBlockEntity.java"
s=menu.read_text(encoding="utf-8")
t=be.read_text(encoding="utf-8")
marker="XSXLABS_TERMINAL_BULK_GRID_PERSISTENCE_V1"
assert marker not in s and marker not in t
def close(src,pos):
    assert src[pos]=="{"
    depth=0
    for i in range(pos,len(src)):
        if src[i]=="{":depth+=1
        elif src[i]=="}":
            depth-=1
            if not depth:return i
    raise AssertionError("Unbalanced Java block")
m=list(re.finditer(r"\bpublic\s+void\s+slotsChanged\s*\(\s*Container\s+\w+\s*\)\s*\{",s))
assert len(m)==1,("slotsChanged drift",len(m))
start=m[0].end()-1
end=close(s,start)
body=s[start+1:end]
setters=list(re.finditer(r"(?P<target>(?:this\.)?[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.setCraftItem\(\s*(?P<idx>[A-Za-z_]\w*)\s*,\s*(?P<value>[^;]+?)\s*\);",body))
assert len(setters)==1,("Expected one craft grid setter loop",len(setters))
setter=setters[0]
assert "craftSlots.getItem(" in setter.group("value") and "getCraftItem(" in body
loops=[]
for loop in re.finditer(r"\bfor\s*\(\s*int\s+(?P<idx>[A-Za-z_]\w*)\s*=\s*0\s*;\s*(?P=idx)\s*<\s*9\s*;\s*(?:(?P=idx)\s*\+\+|\+\+\s*(?P=idx))\s*\)\s*\{",body):
    stop=close(body,loop.end()-1)
    if loop.start()<setter.start()<stop:loops.append((loop,stop))
assert len(loops)==1,("Nine-slot loop drift",len(loops))
loop,stop=loops[0]
old=body[loop.start():stop+1]
assert old.count("setCraftItem(")==1 and old.count("getCraftItem(")==1
assert old.count("craftSlots.getItem(")>=1 and setter.group("idx")==loop.group("idx")
assert not re.search(r"\b(?:break|continue|return|throw)\b",old)
calls=re.findall(r"([A-Za-z_]\w*)\s*\(",old)
assert set(calls)<=set(("for","if","matches","getCraftItem","getItem","setCraftItem")),("Unexpected grid loop side effects",calls)
replacement=("// "+marker+"\n"
    "         ItemStack[] xsxCraftGrid = new ItemStack[9];\n"
    "         for (int xsxSlot = 0; xsxSlot < 9; xsxSlot++)\n"
    "            xsxCraftGrid[xsxSlot] = this.craftSlots.getItem(xsxSlot);\n"
    "         "+setter.group("target")+".setCraftGrid(xsxCraftGrid);")
body=body[:loop.start()]+replacement+body[stop+1:]
s=s[:start+1]+body+s[end:]
methods=list(re.finditer(r"\bpublic\s+void\s+setCraftItem\s*\(\s*int\s+\w+\s*,\s*ItemStack\s+\w+\s*\)\s*\{",t))
assert len(methods)==1,("Terminal BE setter drift",len(methods))
set_end=close(t,methods[0].end()-1)
oldsetter=t[methods[0].end():set_end]
for required in ("this.crafting.getResource(","this.crafting.extract(","this.crafting.insert(","Transaction.openRoot()","this.setChanged()"):
    assert required in oldsetter,("BE persistence drift",required)
new_method="""

   // One root transaction for the entire nine-slot crafting grid.
   // On any partial extraction/insertion, close without committing (rollback).
   public void setCraftGrid(ItemStack[] stacks) {
      if (stacks == null || stacks.length != 9)
         throw new IllegalArgumentException("Craft grid must have exactly nine slots");
      boolean changed = false;
      for (int slot = 0; slot < 9; slot++) {
         if (stacks[slot] == null)
            throw new IllegalArgumentException("Null craft stack at slot " + slot);
         if (!ItemStack.matches(this.getCraftItem(slot), stacks[slot])) changed = true;
      }
      if (!changed) return;
      try (Transaction transaction = Transaction.openRoot()) {
         for (int slot = 0; slot < 9; slot++) {
            ItemStack before = this.getCraftItem(slot);
            ItemStack after = stacks[slot];
            if (ItemStack.matches(before, after)) continue;
            ItemResource oldResource = (ItemResource)this.crafting.getResource(slot);
            if (!oldResource.isEmpty()) {
               int amount = this.crafting.getAmountAsInt(slot);
               int extracted = this.crafting.extract(slot, oldResource, amount, transaction);
               if (extracted != amount)
                  throw new IllegalStateException("Craft grid extraction failed at slot " + slot);
            }
            if (!after.isEmpty()) {
               int amount = after.getCount();
               int inserted = this.crafting.insert(slot, ItemResource.of(after), amount, transaction);
               if (inserted != amount)
                  throw new IllegalStateException("Craft grid insertion failed at slot " + slot);
            }
         }
         transaction.commit();
      }
      this.setChanged();
   }
"""
t=t[:set_end+1]+new_method+t[set_end+1:]
assert s.count(marker)==1 and t.count("public void setCraftGrid(")==1
assert s.count("setCraftItem(")==menu.read_text(encoding="utf-8").count("setCraftItem(")-1
assert t.count("public void setCraftItem(")==1
assert t.count("Transaction.openRoot()")==be.read_text(encoding="utf-8").count("Transaction.openRoot()")+1
menu.write_text(s,encoding="utf-8")
be.write_text(t,encoding="utf-8")
print("TERMINAL_BULK_GRID_PERSISTENCE_V1 PASS one_atomic_transaction_per_grid")
