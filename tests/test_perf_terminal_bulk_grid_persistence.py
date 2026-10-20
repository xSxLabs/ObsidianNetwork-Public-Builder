import os,pathlib,subprocess,tempfile,unittest
PATCH=pathlib.Path(__file__).resolve().parents[1]/"patches/perf-terminal-bulk-grid-persistence.py"
MENU="""public class StorageTerminalMenu {
 public void slotsChanged(Container container) {
   if (container == this.craftSlots) {
      for (int i = 0; i < 9; i++) {
         if (!ItemStack.matches(be.getCraftItem(i), this.craftSlots.getItem(i)))
            be.setCraftItem(i, this.craftSlots.getItem(i));
      }
      this.rebuildRecipeChoice();
   }
 }
}
"""
BE="""public class TerminalInventoryBlockEntity {
 public void setCraftItem(int slot, ItemStack stack) {
   if (slot >= 0 && slot < 9) {
      ItemResource old = (ItemResource)this.crafting.getResource(slot);
      try (Transaction tx = Transaction.openRoot()) {
         this.crafting.extract(slot, old, this.crafting.getAmountAsInt(slot), tx);
         tx.commit();
      }
      try (Transaction tx = Transaction.openRoot()) {
         this.crafting.insert(slot, ItemResource.of(stack), stack.getCount(), tx);
         tx.commit();
      }
      this.setChanged();
   }
 }
}
"""
class BulkGridTests(unittest.TestCase):
 def apply(self,menu=MENU,be=BE):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/"dev/obsidiannetwork"
   (root/"menu").mkdir(parents=True)
   (root/"blockentity").mkdir(parents=True)
   a=root/"menu/StorageTerminalMenu.java"
   b=root/"blockentity/TerminalInventoryBlockEntity.java"
   a.write_text(menu);b.write_text(be)
   env=os.environ.copy();env["V1_SOURCE_ROOT"]=d
   r=subprocess.run(["python3",str(PATCH)],env=env,text=True,capture_output=True)
   return r,a.read_text(),b.read_text()
 def test_atomic_grid_and_legacy_setter(self):
  r,a,b=self.apply()
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn("be.setCraftGrid(xsxCraftGrid);",a)
  self.assertNotIn("be.setCraftItem(",a)
  self.assertIn("try (Transaction transaction = Transaction.openRoot())",b)
  self.assertIn("transaction.commit();",b)
  self.assertIn("ItemStack.matches(before, after)",b)
  self.assertEqual(b.count("public void setCraftItem("),1)
 def test_refuse_extra_loop_side_effect(self):
  changed=MENU.replace("be.setCraftItem(i,","sendPacket(); be.setCraftItem(i,")
  r,a,b=self.apply(menu=changed)
  self.assertNotEqual(r.returncode,0)
  self.assertEqual(a,changed)
  self.assertEqual(b,BE)
 def test_refuse_setter_drift(self):
  changed=BE.replace("this.crafting.extract(","this.crafting.invalid(")
  r,a,b=self.apply(be=changed)
  self.assertNotEqual(r.returncode,0)
  self.assertEqual(a,MENU)
  self.assertEqual(b,changed)
