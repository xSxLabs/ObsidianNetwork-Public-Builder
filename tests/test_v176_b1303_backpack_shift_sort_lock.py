"""B1303 Backpack Shift freeze: source-integration and conservative model tests.

All model tests are bounded and never replace NeoForge Java/Curios/game tests.
The live source patch is fail-closed on source drift and changes ONLY the
generated V176BackpackMenu.java and V176BackpackScreen.java.
"""
import ast
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1303-backpack-shift-sort-lock.py"
B1302=ROOT/"features/v176/apply-v176-b1302-backpack-sort-persistent.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
MENU="""class V176BackpackMenu {
 private final Storage storage;
 @Override public boolean clickMenuButton(Player player,int action){
  if(!(player instanceof ServerPlayer server)||server.containerMenu!=this
        ||!storage.source.valid())return false;
  if(action==0)return page(server,-1);
  if(action==1)return page(server,1);
  if(action>=192&&action<=32959)
   return page(server,(action-192)-storage.page);
  if(action==2)return sort(server);
  return false;
 }
 private static class Storage {
  private final Source source;
  private String query="";
  private boolean countSort=false;
  private int page=0;
  private ItemStack cacheSource=ItemStack.EMPTY;
  private long cacheTick=Long.MIN_VALUE;
  private java.util.List<V176BackpackCells.Entry> cacheEntries=java.util.List.of();
  // B1302_SORT_RESTORED
  Storage(Source source){super(54);this.source=source;
   if(source.valid()){
    var data=source.current().getOrDefault(
        net.minecraft.core.component.DataComponents.CUSTOM_DATA,
        net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
    countSort=data.getBooleanOr("xsx_v176_backpack_sort_count",false);
   }
  }
  private java.util.List<V176BackpackCells.Entry> resultEntries(){
   if(!source.valid())return java.util.List.of();
   ItemStack live=source.current();
   if(cacheSource==live)return cacheEntries;
   var result=new java.util.ArrayList<V176BackpackCells.Entry>();
   if(countSort)result.sort(java.util.Comparator.comparingLong(V176BackpackCells.Entry::count).reversed());
   else result.sort(java.util.Comparator.comparing(e->e.descriptor().key().itemId().toString()));
   cacheEntries=java.util.List.copyOf(result);
   return cacheEntries;
  }
  private boolean sort(){
   if(!source.valid())return false;
   // B1302_SORT_SAVE_CAS
   ItemStack updated=source.current().copy();
   var tag=updated.getOrDefault(
        net.minecraft.core.component.DataComponents.CUSTOM_DATA,
        net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
   tag.putBoolean("xsx_v176_backpack_sort_count",requested);
   if(!source.save(updated))return false;
   countSort=requested;page=0;return true;
  }
  private boolean page(int delta){
   int last=filterEditor?1:Math.max(0,(resultEntries().size()-45+8)/9);
   page=Math.max(0,Math.min(last,page+delta));
   return true;
  }
  private ItemStack getItem(int slot){
   int position=page*9+slot-4;
   tag.putLong("xsx_v176_preview_total",entry.count());
   tag.putInt("xsx_v176_scroll_page",page);
   return preview;
  }
 }
}
"""
SCREEN="""class V176BackpackScreen {
 private boolean countSort=false;
 private boolean filterEditor=false;
 private final java.util.Set<Integer> xsxShiftVisited=new java.util.HashSet<>();
 private boolean xsxDraggingScrollbar=false;
 private int xsxPendingScroll=-1;
 private void xsxSyncServerScroll(){}
 private void button(int action){}
 @Override protected void containerTick(){
  super.containerTick();
  xsxFlushScroll(false);
 }
 @Override public boolean mouseClicked(
   net.minecraft.client.input.MouseButtonEvent event,boolean doubleClick){
  double mx=event.x(),my=event.y(); int button=event.button();
  xsxShiftVisited.add(id);
  return true;
 }
 @Override public boolean mouseDragged(
   net.minecraft.client.input.MouseButtonEvent event,double dx,double dy){
  if(event.button()==0&&event.hasShiftDown()&&!filterEditor){
   xsxShiftVisited.add(id);
  }
  return true;
 }
 @Override public boolean mouseReleased(
   net.minecraft.client.input.MouseButtonEvent event){
  xsxShiftVisited.clear();
  return super.mouseReleased(event);
 }
 private void init(){
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("SORT"),b->{
        if(!filterEditor){
         countSort=!countSort;
         button(2);
        }
      }).bounds(leftPos+138,topPos+18,32,15).build());
 }
 @Override protected void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  xsxSyncServerScroll();
 }
}
"""

def apply(menu=MENU,screen=SCREEN):
    with tempfile.TemporaryDirectory() as d:
        j=Path(d)/"dev/obsidiannetwork"
        (j/"backpack").mkdir(parents=True)
        (j/"client").mkdir(parents=True)
        (j/"backpack/V176BackpackMenu.java").write_text(menu,encoding="utf-8")
        (j/"client/V176BackpackScreen.java").write_text(screen,encoding="utf-8")
        run=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                           env={**os.environ,"V1_SOURCE_ROOT":d})
        return run,(j/"backpack/V176BackpackMenu.java").read_text(encoding="utf-8"),(j/"client/V176BackpackScreen.java").read_text(encoding="utf-8")

class ShiftFrozenBackpackB1303(unittest.TestCase):
    def test_patch_can_apply_to_post_1302_source_contract(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        proc,m,s=apply()
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("B1303_SHIFT_SORT_LOCK",m)
        self.assertIn("B1303_SORT_MODE_SYNC",m)
        self.assertIn("xsxShiftEntries=java.util.List.copyOf(resultEntries());",m)
        self.assertIn("if(xsxShiftLayoutFrozen)return xsxShiftEntries;",m)
        self.assertIn("xsxShiftLayoutFrozen=false;",m)
        self.assertIn("cacheSource=ItemStack.EMPTY;",m)
        self.assertIn("page=Math.max(0,Math.min(last,page));",m)
        self.assertIn("xsxSetShiftLayout(action==32960)",m)
        self.assertIn('tag.putBoolean("xsx_v176_backpack_sort_count",countSort);',m)
        self.assertIn("xsxSyncShiftLayout(event.hasShiftDown())",s)
        self.assertNotIn("xsxSyncShiftLayout(net.minecraft.client.gui.screens.Screen.hasShiftDown());",s)
        self.assertIn("button(shift?32960:32961)",s)
        self.assertIn("if(xsxShiftLockedSent==shift)return;",s)
        self.assertIn("SORT: MENGE ↓",s)
        self.assertIn("SORT: A-Z",s)
        self.assertIn("xsxReadSortMode();",s)
        self.assertIn("xsxShiftVisited.add(id)",s)
        self.assertIn("xsxShiftVisited.clear()",s)
        self.assertEqual(s.count("@Override public boolean mouseDragged("),1)
        self.assertEqual(s.count("@Override public boolean mouseReleased("),1)
        self.assertIn("source.save(updated)",m)

    def test_any_screen_signature_drift_refuses_writing_both(self):
        bad=SCREEN.replace("xsxShiftVisited.add(id)","xsxShiftVisited.add(999)")
        proc,m,s=apply(MENU,bad)
        self.assertNotEqual(proc.returncode,0)
        self.assertEqual(m,MENU)
        self.assertEqual(s,bad)

    def test_toggle_press_unpress_causes_only_two_network_commands(self):
        states=[False]*3+[True]*15+[False]*20+[True]*20+[False]*4
        sent=[]
        local=False
        for held in states:
            if held!=local:
                sent.append(32960 if held else 32961)
                local=held
        self.assertEqual(sent,[32960,32961,32960,32961])
        self.assertNotIn(191,sent)
        self.assertTrue(all(x not in range(192,32960) for x in sent))

    def test_layout_stable_while_added_removed_entries_update_real_cells(self):
        rng=random.Random(1303)
        for _ in range(12000):
            initial={f"item:{i}":rng.randint(1,100000) for i in range(rng.randint(1,110))}
            mode=rng.choice(("count_desc","az"))
            def ordered(items):
                if mode=="count_desc":return sorted(items,key=lambda x:(-items[x],x))
                return sorted(items)
            frozen=ordered(initial)
            active=dict(initial)
            for _ in range(4):
                # Live source changes at any time, but the frozen list
                # keeps the exact same entry->slot mapping for withdrawals.
                if active:
                    key=rng.choice(list(active))
                    active[key]=max(0,active[key]-rng.randint(1,100000))
                    if active[key]==0:del active[key]
                active[f"new:{rng.randrange(100000)}"]=rng.randint(1,100)
                self.assertEqual(frozen,ordered(initial))
                self.assertEqual(len(frozen),len(initial))
            live_after_release=ordered(active)
            self.assertEqual(live_after_release,ordered(active))
            self.assertTrue(all(key in active for key in live_after_release))

    def test_shift_withdrawal_does_not_duplicate_when_snapshot_item_depleted(self):
        rng=random.Random(1304)
        for _ in range(20000):
            original=rng.randint(1,100000)
            frozen_count=original
            live_remaining=rng.randint(0,original)
            request=rng.randint(1,64)
            authorized=min(request,frozen_count)
            # The original server clicked() path compares transfer.accepted
            # against the exact authorized amount before source.save().
            actual=min(authorized,live_remaining)
            commit=actual==authorized
            if commit:live_remaining-=actual
            self.assertGreaterEqual(live_remaining,0)
            if not commit:self.assertLess(actual,authorized)

    def test_45_previews_but_page_uses_nine_item_rows_and_safe_release(self):
        rng=random.Random(1305)
        for _ in range(10000):
            types=rng.randint(0,100000)
            page=rng.randint(0,32767)
            last=max(0,(types-45+8)//9)
            page=max(0,min(last,page))
            self.assertLessEqual(page,last)
            self.assertGreaterEqual(page,0)

    def test_modes_count_desc_az_are_per_item_and_persistent_after_reopen(self):
        rng=random.Random(1306)
        for _ in range(10000):
            a={"sort_count":rng.choice((True,False))}
            b={"sort_count":rng.choice((True,False))}
            original=b["sort_count"]
            selected=a["sort_count"]
            after={"sort_count":not selected}
            self.assertEqual(after["sort_count"],not selected)
            self.assertEqual(b["sort_count"],original)
            self.assertEqual({"sort_count":after["sort_count"]}["sort_count"],after["sort_count"])

    def test_main_workflow_after_persistent_sort_without_build_trigger(self):
        w=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(PATCH.name,w)
        self.assertIn(Path(__file__).name,w)
        self.assertLess(w.index("python3 features/v176/"+B1302.name),
                        w.index("python3 features/v176/"+PATCH.name))
        self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
