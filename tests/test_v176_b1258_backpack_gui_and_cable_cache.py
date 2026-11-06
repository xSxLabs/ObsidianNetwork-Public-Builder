"""B1258 Backpack preview and cable-cache regression gates.

The runtime patch applies after all 1.7.6 feature overlays. A source drift
MUST fail before writing either of the two Java targets.
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
PATCH=ROOT/"features/v176/apply-v176-b1258-backpack-preview-and-resource-reuse.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

# Minimal exact post-B1234 anchors. Full Java compilation and item conservation
# gates are handled separately by the actual NeoForge CI workflow.
BE="""class TestBE {
 // xsxCableCommitRevision xsxCableCacheContainer==container
 // cableJournal.updateSnapshots(tx) backpack=before.copy()
 void refresh(){
   for(var entry:entries)
    resources.add(net.neoforged.neoforge.transfer.item.ItemResource.of(
        codec.recreate(entry.descriptor(),1)));
 }
}"""
MENU="""class TestMenu {
 // cacheContainer==content cacheCableRevision==liveCableRevision
 // ItemStack.matches(snapshot,be.getBackpack())
  private V176BackpackCells.Entry viewed(int slot){return null;}
  ItemStack getItem(int slot){
   var entry=viewed(slot);
   if(entry==null)return ItemStack.EMPTY;
   var world=source instanceof ItemSource item?item.player.level()
        :((BlockSource)source).player.level();
   var preview=ItemStack.EMPTY;
   preview.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.of(tag));
   return preview;
  }
}"""

def run_patch(be_source=BE, menu_source=MENU):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/"dev/obsidiannetwork/backpack"
        root.mkdir(parents=True)
        be=root/"NetworkBackpackBlockEntity.java"
        menu=root/"V176BackpackMenu.java"
        be.write_text(be_source,encoding="utf-8")
        menu.write_text(menu_source,encoding="utf-8")
        result=subprocess.run(
            [sys.executable,str(PATCH)],
            env={**os.environ,"V1_SOURCE_ROOT":tmp},
            capture_output=True,text=True)
        return result,be.read_text("utf-8"),menu.read_text("utf-8")

def same_descriptor(a,b):
    # Compare exact item ID AND serialized component payload, never count.
    return a[0]==b[0] and a[1]==b[1]

class BackpackB1258(unittest.TestCase):
    def test_python_source_and_workflow_order(self):
        ast.parse(PATCH.read_text("utf-8"))
        s=WORKFLOW.read_text("utf-8")
        names=[
            "apply-v176-b1230-backpack-live-gui.py",
            "apply-v176-b1234-backpack-cable-perf.py",
            "apply-v176-b1234-backpack-scroll.py",
            "apply-v176-b1248-bag-hotpath-elision.py",
            PATCH.name,
        ]
        self.assertEqual([s.index(n) for n in names],
                         sorted(s.index(n) for n in names))
        self.assertIn("test_v176_b1258_backpack_gui_and_cable_cache.py",s)

    def test_fixture_and_invalidation(self):
        r,be,menu=run_patch()
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("B1258_BACKPACK_EXACT_CABLE_RESOURCE_REUSE_45_SLOT_GUI_PREVIEWS_PASS",r.stdout)
        for token in ("entry.descriptor().canonicalPayload()",
                      "xsxCableEntries.get(idx).descriptor().canonicalPayload()",
                      "xsxCableResources.get(idx)","java.util.Arrays.equals"):
            self.assertIn(token,be)
        for token in ("xsxPreviewEntryCache!=entries",
                      "xsxPreviewPageCache!=page",
                      "java.util.Arrays.fill(xsxPreviewStacks,null)",
                      "new ItemStack[45]","cachedPreview.copy()",
                      "xsxPreviewStacks[previewIndex]=preview.copy()"):
            self.assertIn(token,menu)
        # No removal of transactional and GUI safeguards.
        self.assertIn("cableJournal.updateSnapshots(tx)",be)
        self.assertIn("ItemStack.matches(snapshot,be.getBackpack())",menu)

    def test_fail_closed_drift_leaves_both_java_files_unchanged(self):
        for a,b in ((BE.replace("codec.recreate(entry.descriptor(),1)",
                                "codec.recreate(entry.descriptor(),2)"),MENU),
                    (BE,MENU.replace("if(entry==null)return ItemStack.EMPTY;",
                                     "if(entry==null)return null;"))):
            r,after_be,after_menu=run_patch(a,b)
            self.assertNotEqual(r.returncode,0)
            self.assertIn("B1258_BACKPACK_SOURCE_DRIFT",r.stderr)
            self.assertEqual(after_be,a)
            self.assertEqual(after_menu,b)

    def test_exact_resource_equivalence_and_reuse(self):
        rng=random.Random(1258)
        saved=0
        for _ in range(7000):
            size=rng.randrange(1,120)
            previous=[(f"minecraft:item_{i}",bytes(rng.randrange(256)
                      for _ in range(rng.randrange(0,10)))) for i in range(size)]
            current=list(previous)
            # Changing only quantities must not invalidate ItemResource.
            if rng.random()<0.3:
                i=rng.randrange(size)
                current[i]=(current[i][0],current[i][1]+b"\\x00")
            if rng.random()<0.2:
                i=rng.randrange(size)
                current[i]=(f"minecraft:new_item_{i}",current[i][1])
            reuses=[i<len(previous) and same_descriptor(current[i],previous[i])
                    for i in range(len(current))]
            expected=[(current[i][0],current[i][1]) for i in range(len(current))]
            actual=[previous[i] if reuses[i] else current[i]
                    for i in range(len(current))]
            self.assertEqual(actual,expected)
            saved+=sum(reuses)
        self.assertGreater(saved,100000)

    def test_never_touches_gameplay_or_frozen_versions(self):
        s=PATCH.read_text("utf-8")
        self.assertNotIn("features/v175/",s)
        for fragment in ("writeSlots(", "insertExact(", "store.extract(",
                         "setItemInHand(", "tickCount%", "sleep(",
                         "PowerArmorEntrySequence", "ReactorPower"):
            self.assertNotIn(fragment,s)

if __name__=="__main__":
    unittest.main()
