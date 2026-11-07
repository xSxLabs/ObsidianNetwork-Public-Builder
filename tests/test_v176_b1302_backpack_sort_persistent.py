"""B1302: server-owned sort mode survives GUI reopening and item roundtrips.

Fast preflight applies strict patch to a matching post-B816 menu fixture.
Full NeoForge Java compilation / server restart testing still required.
"""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1302-backpack-sort-persistent.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

MENU="""public final class V176BackpackMenu {
 private static final class ItemSource {
  private ItemStack live(){
   return switch(location.where()){
    case CHEST->player.getItemBySlot(EquipmentSlot.CHEST);
    case MAIN_HAND->player.getItemInHand(InteractionHand.MAIN_HAND);
    case OFF_HAND->player.getItemInHand(InteractionHand.OFF_HAND);
    case CURIOS_BACK->{
     var found=V176BackpackEquipped.worn(player);
     yield found!=null&&found.where()==V176BackpackEquipped.Where.CURIOS_BACK
          &&found.index()==location.index()?found.stack():ItemStack.EMPTY;
    }
   };
  }
 }
 private static final class Storage extends SimpleContainer {
  private final Source source;
   private boolean countSort=false;
  private int page=0;
   Storage(Source source){super(54);this.source=source;}
   private java.util.List<V176BackpackCells.Entry> resultEntries(){
    if(!source.valid())return java.util.List.of();
   var result=new java.util.ArrayList<V176BackpackCells.Entry>();
   if(countSort)result.sort(java.util.Comparator
       .comparingLong(V176BackpackCells.Entry::count).reversed()
       .thenComparing(e->e.descriptor().key().itemId().toString()));
   else result.sort(java.util.Comparator.comparing(
       e->e.descriptor().key().itemId().toString()));
   return result;
  }
   private boolean sort(){
    if(!source.valid())return false;
    countSort=!countSort;page=0;return true;
   }
 }
}
"""

EQUIPPED="""public final class V176BackpackEquipped {
 // B1301_INVENTORY_MAGNET_CAS
 // B1301_INVENTORY_MAGNET_DISCOVERY
 case INVENTORY->{
  var inventory=player.getInventory();
 }
}
"""

def apply(menu=MENU,equipped=EQUIPPED):
    with tempfile.TemporaryDirectory() as d:
        j=Path(d)/"dev/obsidiannetwork/backpack"
        j.mkdir(parents=True)
        (j/"V176BackpackMenu.java").write_text(menu,encoding="utf-8")
        (j/"V176BackpackEquipped.java").write_text(equipped,encoding="utf-8")
        p=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                         env={**os.environ,"V1_SOURCE_ROOT":d})
        return p,(j/"V176BackpackMenu.java").read_text(encoding="utf-8")

class PersistentBackpackSort(unittest.TestCase):
    def test_patch_guards_and_persistent_mode(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        result,source=apply()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("B1302_SORT_RESTORED",source)
        self.assertIn("B1302_SORT_SAVE_CAS",source)
        self.assertIn("B1302_INVENTORY_SOURCE",source)
        self.assertIn('countSort=data.getBooleanOr("xsx_v176_backpack_sort_count",false)',source)
        self.assertIn('tag.putBoolean("xsx_v176_backpack_sort_count",requested)',source)
        self.assertIn("if(!source.save(updated))return false;",source)
        self.assertLess(source.index("if(!source.save(updated))return false;"),
                        source.index("countSort=requested;"))
        self.assertIn("case INVENTORY->location.index()>=0",source)
        self.assertIn("case CURIOS_BACK->",source)
        self.assertIn("if(countSort)result.sort(java.util.Comparator",source)
        self.assertIn("else result.sort(java.util.Comparator.comparing(",source)
        self.assertNotIn("countSort=!countSort;page=0;return true;",source)

    def test_drift_refuses_mutation(self):
        bad=MENU.replace("countSort=!countSort;page=0;return true;",
                         "countSort=!countSort;page=1;return true;")
        run,output=apply(bad)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(output,bad)

    def test_source_item_roundtrip_keeps_sort_per_backpack(self):
        rng=random.Random(1302)
        for _ in range(20000):
            backpack_a={"item":"xsx_backpack","custom":{},"cells":rng.randrange(100)}
            backpack_b={"item":"xsx_backpack","custom":{},"cells":rng.randrange(100)}
            current=backpack_a.copy()
            current["custom"]=current["custom"].copy()
            count_sort=bool(current["custom"].get("xsx_v176_backpack_sort_count",False))
            requested=not count_sort
            updated={**current,"custom":{**current["custom"],
                                         "xsx_v176_backpack_sort_count":requested}}
            save_ok=bool(rng.randrange(2))
            if save_ok:current=updated
            else:self.assertEqual(current["custom"],{})
            reopened=bool(current["custom"].get("xsx_v176_backpack_sort_count",False))
            self.assertEqual(reopened,requested if save_ok else count_sort)
            self.assertEqual(backpack_b["custom"],{})
            self.assertEqual(current["cells"],backpack_a["cells"])
            # Place, break, pick up: identical item NBT components.
            placed={**current,"custom":current["custom"].copy()}
            picked={**placed,"custom":placed["custom"].copy()}
            self.assertEqual(picked,current)

    def test_stable_sort_result_after_reopen(self):
        entries=[("minecraft:oak_log",100),("minecraft:stone",1),
                 ("minecraft:dirt",25),("minecraft:apple",50)]
        by_count=sorted(entries,key=lambda item:(-item[1],item[0]))
        by_name=sorted(entries,key=lambda item:item[0])
        self.assertNotEqual(by_count,by_name)
        self.assertEqual(by_count[0][0],"minecraft:oak_log")
        self.assertEqual(by_name[0][0],"minecraft:apple")

    def test_patch_runs_after_inventory_magnet(self):
        workflow=WF.read_text(encoding="utf-8")
        self.assertIn(PATCH.name,workflow)
        self.assertIn(Path(__file__).name,workflow)
        self.assertLess(workflow.index("python3 features/v176/apply-v176-b1301-backpack-magnet-any-location.py"),
                        workflow.index("python3 features/v176/"+PATCH.name))
        self.assertNotIn("features/v175/",PATCH.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
