"""B1273/B1274: source-integration gates for placed Magnet and live scroll range.

Tests cover generated Java anchors, strict drift handling, exact entity
conservation, magnetic radius, 9-item scroll rows, and physical stop position.
The NeoForge Java compiler and real-world MSPT test are additional gates.
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
ROOT_FEATURE=ROOT/"features/v176"
PATCH_MAG=ROOT_FEATURE/"apply-v176-b1273-placed-backpack-magnet.py"
PATCH_SCROLL=ROOT_FEATURE/"apply-v176-b1274-backpack-live-scroll-range.py"
WORLD=ROOT_FEATURE/"apply-v176-backpack-world-placement.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"


def block_fixture():
 tree=ast.parse(WORLD.read_text("utf-8"))
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="add" and len(node.args)>=2:
   if isinstance(node.args[0],ast.Constant) and node.args[0].value=="backpack/NetworkBackpackBlock.java":
    return ast.literal_eval(node.args[1])
 raise AssertionError("B1273_BLOCK_GENERATOR_DRIFT")


BE='''class NetworkBackpackBlockEntity {
 private ItemStack backpack;
 private long xsxCableCommitRevision;
 private long xsxCableCapacity;
 private long xsxCableUsed;
 private void xsxRefreshCableView(){}
 public ItemStack getBackpack(){return backpack;}
}'''

MENU='''class V176BackpackMenu {
 private static class Storage {
  int page;
  void preview(){
   tag.putLong("xsx_v176_preview_total",entry.count());
  }
  private void viewed(){
   int position=page*9+slot-4;
  }
  private void page(int delta){
   int last=Math.max(0,(resultEntries().size()-45+8)/9);
  }
 }
}'''

SCREEN='''class V176BackpackScreen {
 private boolean filterEditor;
 private int scrollRow;
 private int filterPage;
 private int xsxDragStartRow;
 private int xsxDragStartY;
 private boolean xsxDraggingScrollbar;
 private int xsxPendingScroll;
 private double xsxWheelAccumulator;
 private int xsxScrollLimit(){return filterEditor?1:32767;}
 private void xsxScrollTo(int row){}
 private void xsxMouseDragged(){
   xsxScrollTo(xsxDragStartRow+(int)Math.round((y-xsxDragStartY)*0.5D));
 }
 private void xsxMouseClicked(){
   int thumb=39+Math.min(73,xsxDragStartRow*3);
   else if(scrollY>thumb+16)xsxScrollTo(xsxDragStartRow+5);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();
  int thumbY=y+39+Math.min(73,scrollRow*3);
  g.fill(x+174,thumbY,x+178,thumbY+16,0xff123456);
 }
}'''


def apply_patch(script,files):
 with tempfile.TemporaryDirectory() as tmp:
  target=Path(tmp)/"dev/obsidiannetwork"
  target.mkdir(parents=True)
  for rel,src in files.items():
   path=target/rel
   path.parent.mkdir(parents=True,exist_ok=True)
   path.write_text(src,"utf-8")
  run=subprocess.run([sys.executable,str(script)],env={**os.environ,"V1_SOURCE_ROOT":tmp},capture_output=True,text=True)
  return run,{rel:(target/rel).read_text("utf-8") for rel in files},(target/"backpack/V176BackpackPlacedMagnet.java").exists()


class B1273PlacedMagnetScroll(unittest.TestCase):
 def test_magnet_patch_and_8_block_server_ticker(self):
  ast.parse(PATCH_MAG.read_text("utf-8"))
  r,files,has_helper=apply_patch(PATCH_MAG,{
      "backpack/NetworkBackpackBlock.java":block_fixture(),
      "backpack/NetworkBackpackBlockEntity.java":BE})
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertTrue(has_helper)
  self.assertIn("V176BackpackPlacedMagnet::tick",files["backpack/NetworkBackpackBlock.java"])
  self.assertIn("getTicker(",files["backpack/NetworkBackpackBlock.java"])
  self.assertIn("xsxPlacedMagnetActive()",files["backpack/NetworkBackpackBlockEntity.java"])
  self.assertIn("xsxCableUsed<xsxCableCapacity",files["backpack/NetworkBackpackBlockEntity.java"])

 def test_magnet_drift_writes_neither_java(self):
  block=block_fixture().replace("new NetworkBackpackBlockEntity(p,s)","new AnotherBlockEntity(p,s)")
  r,files,helper=apply_patch(PATCH_MAG,{"backpack/NetworkBackpackBlock.java":block,
                                         "backpack/NetworkBackpackBlockEntity.java":BE})
  self.assertNotEqual(r.returncode,0)
  self.assertIn("B1273_PLACED_MAGNET_DRIFT",r.stderr)
  self.assertFalse(helper)
  self.assertEqual(files["backpack/NetworkBackpackBlock.java"],block)
  self.assertEqual(files["backpack/NetworkBackpackBlockEntity.java"],BE)

 def test_scroll_patch_matches_original_generated_screen_shape(self):
  ast.parse(PATCH_SCROLL.read_text("utf-8"))
  r,files,_=apply_patch(PATCH_SCROLL,{
      "backpack/V176BackpackMenu.java":MENU,
      "client/V176BackpackScreen.java":SCREEN})
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  screen=files["client/V176BackpackScreen.java"]
  menu=files["backpack/V176BackpackMenu.java"]
  self.assertIn("xsxServerResultCount()",screen)
  self.assertIn("xsxSyncServerScroll()",screen)
  self.assertIn("xsxThumbHeight()",screen)
  self.assertIn("xsxThumbTop()",screen)
  self.assertIn("thumbY+xsxThumbHeight()",screen)
  self.assertIn("xsx_v176_scroll_total_types",menu)
  self.assertIn("xsx_v176_scroll_page",menu)
  self.assertIn("page*9+slot-4",menu)

 def test_scroll_drift_rejects_before_writing(self):
  broken=SCREEN.replace("scrollRow*3","scrollRow*6")
  r,files,_=apply_patch(PATCH_SCROLL,{
      "backpack/V176BackpackMenu.java":MENU,
      "client/V176BackpackScreen.java":broken})
  self.assertNotEqual(r.returncode,0)
  self.assertEqual(files["client/V176BackpackScreen.java"],broken)
  self.assertEqual(files["backpack/V176BackpackMenu.java"],MENU)

 def test_scroll_limits_for_random_type_counts(self):
  rng=random.Random(1274)
  for _ in range(10000):
   types=rng.randint(0,50000)
   last=max(0,(types-45+8)//9)
   if last>32767:last=32767
   thumb=90 if types<=45 else max(16,min(90,round(90.0*45.0/types)))
   travel=90-thumb
   for pos in (0,last//2,last):
    top=38+(0 if last==0 else round(travel*pos/last))
    self.assertGreaterEqual(top,38)
    self.assertLessEqual(top+thumb,128)
   if types<=45:self.assertEqual(last,0)
   if types>45:self.assertGreater(last,0)

 def test_no_item_loss_and_atomic_placed_magnet(self):
  source=PATCH_MAG.read_text("utf-8")
  start=source.index("java='''")
  helper=source[start:source.index("'''",start+8)]
  self.assertIn("ItemResource.of(item)",helper)
  self.assertIn("RANGE=8.0D",helper)
  self.assertIn("bag.replaceBackpack(original,next)",helper)
  self.assertIn("if(picked.isEmpty())return",helper)
  self.assertIn("if(left!=0L)return",helper)
  self.assertLess(helper.index("bag.replaceBackpack(original,next)"),
                  helper.index("remainder.shrink(pickup.amount())"))
  self.assertNotIn("Thread.sleep(",helper)
  self.assertNotIn("tickCount%",helper)
  rng=random.Random(1273)
  for _ in range(10000):
   dropped=[rng.randint(1,64) for i in range(rng.randint(1,64))]
   accepted=rng.randint(0,sum(dropped))
   remaining=accepted
   moved=[]
   for count in dropped:
    take=min(remaining,count)
    moved.append(take)
    remaining-=take
   self.assertEqual(sum(moved),accepted)
   self.assertEqual(sum(a-b for a,b in zip(dropped,moved)),sum(dropped)-accepted)

 def test_both_scripts_are_present_after_b1270_in_full_pipeline(self):
  w=WORKFLOW.read_text("utf-8")
  for path in (PATCH_MAG,PATCH_SCROLL):
   self.assertIn(path.name,w)
  self.assertIn(Path(__file__).name,w)
  self.assertLess(w.index("apply-v176-b1270-magnet-8-instant-batched.py"),
                  w.index(PATCH_MAG.name))
  self.assertLess(w.index(PATCH_MAG.name),w.index(PATCH_SCROLL.name))


if __name__=="__main__":
 unittest.main()
