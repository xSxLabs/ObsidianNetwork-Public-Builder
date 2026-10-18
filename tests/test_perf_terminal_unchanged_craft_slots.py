#!/usr/bin/env python3
"""Gate terminal nine-slot no-op transaction elision and contract preservation."""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"patches/perf-terminal-unchanged-craft-slot-elision.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"
BE='''package dev.obsidiannetwork.blockentity;
class TerminalInventoryBlockEntity {
   public ItemStack getCraftItem(int slot) {
      return this.crafting.getResource(slot).toStack(this.crafting.getAmountAsInt(slot));
   }
   public void setCraftItem(int slot, ItemStack stack) {
      if (slot < 0 || slot >= 9) return;
      ItemResource current = (ItemResource)this.crafting.getResource(slot);
      if (!current.isEmpty()) {
         try (Transaction tx = Transaction.openRoot()) {
            this.crafting.extract(slot, current, 10, tx);
            tx.commit();
         }
      }
      if (!stack.isEmpty()) {
         try (Transaction tx = Transaction.openRoot()) {
            this.crafting.insert(slot, ItemResource.of(stack), stack.getCount(), tx);
            tx.commit();
         }
      }
      this.setChanged();
   }
   public void copyFrom(ItemStack[] slots) {}
}
'''
MENU='''package dev.obsidiannetwork.menu;
class StorageTerminalMenu {
   private Object craftSlots;
   public void slotsChanged(Container c) {
      terminal.setCraftItem(i, this.craftSlots.getItem(i));
   }
}
'''

def apply(be=BE,menu=MENU):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/"dev/obsidiannetwork/blockentity/TerminalInventoryBlockEntity.java"
        m=Path(tmp)/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
        p.parent.mkdir(parents=True)
        m.parent.mkdir(parents=True)
        p.write_text(be)
        m.write_text(menu)
        run=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},capture_output=True,text=True)
        return run,p.read_text(),m.read_text()

class TerminalNoopPersistence(unittest.TestCase):
    def test_full_transaction_body_preserved(self):
        result,after,menu=apply()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(menu,MENU)
        self.assertIn("XSXLABS_TERMINAL_UNCHANGED_CRAFT_SLOT_ELISION_V1",after)
        self.assertIn("if (slot >= 0 && slot < 9 && ItemStack.matches(this.getCraftItem(slot), stack)) return;",after)
        for token in ("this.crafting.extract(", "this.crafting.insert(", "this.setChanged()", "Transaction.openRoot()"):
            self.assertEqual(after.count(token),BE.count(token),token)
        reapply,unchanged,_=apply(after)
        self.assertNotEqual(reapply.returncode,0)
        self.assertEqual(unchanged,after)
    def test_fail_closed_on_source_shape_change(self):
        for old,new in (
            ("public void setCraftItem(int slot, ItemStack stack)", "public void setCraftItem(int slot, Resource newValue)"),
            ("this.crafting.extract(", "this.crafting.fastRemove("),
            ("this.crafting.insert(", "this.crafting.fastAdd("),
            ("Transaction.openRoot()", "Transaction.openNested()"),
            ("this.setChanged()", "this.sendDirty()"),
            ("public ItemStack getCraftItem(int", "private ItemStack getCraftItem(int"),
        ):
            broken=BE.replace(old,new)
            self.assertNotEqual(broken,BE,old)
            r,after,_=apply(broken)
            self.assertNotEqual(r.returncode,0,old)
            self.assertEqual(after,broken,old)
    def test_exact_equality_not_item_only_or_ignore_count(self):
        # Model the intended Minecraft ItemStack.matches contract:
        # item identity + full components + amount.
        rnd=random.Random(212)
        writes=0
        noops=0
        slots=[None]*9
        def equal(x,y):
            return x==y
        for _ in range(30000):
            slot=rnd.randrange(9)
            before=slots[slot]
            if rnd.randrange(4)==0:
                incoming=before
            else:
                incoming=(rnd.randrange(12),rnd.randrange(1,65),rnd.randrange(10000)) if rnd.randrange(4)!=0 else None
            optimized_writes=0 if equal(before,incoming) else 1
            baseline_writes=1
            self.assertEqual(slots[slot] if optimized_writes==0 else incoming,
                             incoming, "No-op must only skip a truly identical content/count/components stack")
            self.assertLessEqual(optimized_writes,baseline_writes)
            slots[slot]=incoming
            writes+=optimized_writes
            noops+=1-optimized_writes
        self.assertGreater(writes,0)
        self.assertGreater(noops,0)
        self.assertFalse(equal(("diamond_sword",1,123),("diamond_sword",2,123)))
        self.assertFalse(equal(("diamond_sword",1,123),("diamond_sword",1,124)))
    def test_workflow_includes_gate_before_compile(self):
        text=WORKFLOW.read_text()
        self.assertEqual(text.count("python3 patches/perf-terminal-unchanged-craft-slot-elision.py"),1)
        self.assertIn("test_perf_terminal_unchanged_craft_slots.py",text)
        patch_idx=text.index("python3 patches/perf-terminal-unchanged-craft-slot-elision.py")
        self.assertLess(patch_idx,text.index("gradle --no-daemon --no-configuration-cache",patch_idx))

if __name__=="__main__":
    unittest.main()
