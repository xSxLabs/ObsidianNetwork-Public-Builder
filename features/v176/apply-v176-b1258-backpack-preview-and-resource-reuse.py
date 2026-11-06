#!/usr/bin/env python3
"""B1258: reuse only exact unchanged Backpack cable resources and GUI previews.

Installed after B1234's immutable-component and committed-revision guards.
Never cache the actual inventory or mutate real cell data; only transient
read-only UI ItemStacks and NeoForge ItemResource representations are reused.
Bound preview cache to the 45 on-screen item slots. No tick skips or rate caps.
All anchors are checked before either Java file is written (fail closed).
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
be = root / "backpack/NetworkBackpackBlockEntity.java"
menu = root / "backpack/V176BackpackMenu.java"

be_src = be.read_text(encoding="utf-8")
menu_src = menu.read_text(encoding="utf-8")

def exactly_once(source: str, old: str, new: str, label: str) -> str:
    n = source.count(old)
    assert n == 1, ("B1258_BACKPACK_SOURCE_DRIFT", label, n)
    return source.replace(old, new, 1)

# B1234 correctly invalidates the cable snapshot on every committed change.
# On amount-only changes it must still rebuild counts, but ItemResource itself
# only depends on the exact descriptor and is safe to reuse. This avoids
# deserializing every type for every single cable transfer.
be_src = exactly_once(be_src,
'''   for(var entry:entries)
    resources.add(net.neoforged.neoforge.transfer.item.ItemResource.of(
        codec.recreate(entry.descriptor(),1)));''',
'''   for(int idx=0;idx<entries.size();idx++){
    var entry=entries.get(idx);
    boolean sameDescriptor=idx<xsxCableEntries.size()
       &&idx<xsxCableResources.size()
       &&entry.descriptor().key().itemId().equals(
           xsxCableEntries.get(idx).descriptor().key().itemId())
       &&java.util.Arrays.equals(entry.descriptor().canonicalPayload(),
           xsxCableEntries.get(idx).descriptor().canonicalPayload());
    resources.add(sameDescriptor?xsxCableResources.get(idx):
        net.neoforged.neoforge.transfer.item.ItemResource.of(
            codec.recreate(entry.descriptor(),1)));
   }''', "cable resource loop")

# The B1234 GUI list cache already detects immutable CONTAINER changes, cable
# commit revision, search and sort. Cache only the decoded *visible* 45
# preview stacks and invalidate when the backing list or page changes.
menu_src = exactly_once(menu_src,
'''  private V176BackpackCells.Entry viewed(int slot){''',
'''  // Read-only virtual previews, never owned inventory items.
  private java.util.List<V176BackpackCells.Entry> xsxPreviewEntryCache=null;
  private int xsxPreviewPageCache=-1;
  private final ItemStack[] xsxPreviewStacks=new ItemStack[45];
  private V176BackpackCells.Entry viewed(int slot){''', "preview cache fields")

menu_src = exactly_once(menu_src,
'''   var entry=viewed(slot);
   if(entry==null)return ItemStack.EMPTY;
   var world=source instanceof ItemSource item?item.player.level()
        :((BlockSource)source).player.level();''',
'''   var entry=viewed(slot);
   if(entry==null)return ItemStack.EMPTY;
   var entries=resultEntries();
   if(xsxPreviewEntryCache!=entries||xsxPreviewPageCache!=page){
    java.util.Arrays.fill(xsxPreviewStacks,null);
    xsxPreviewEntryCache=entries;
    xsxPreviewPageCache=page;
   }
   int previewIndex=slot-4;
   ItemStack cachedPreview=xsxPreviewStacks[previewIndex];
   if(cachedPreview!=null)return cachedPreview.copy();
   var world=source instanceof ItemSource item?item.player.level()
        :((BlockSource)source).player.level();''', "live preview read")

menu_src = exactly_once(menu_src,
'''   preview.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.of(tag));
   return preview;''',
'''   preview.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.of(tag));
   xsxPreviewStacks[previewIndex]=preview.copy();
   return preview;''', "preview population")

# B1230 protects placed GUI + cable CAS, and B1234 protects the exact views.
for token in ("xsxCableCommitRevision", "xsxCableCacheContainer==container",
              "cableJournal.updateSnapshots(tx)", "backpack=before.copy()"):
    assert token in be_src, ("B1258_CABLE_SAFETY_MISSING", token)
for token in ("cacheContainer==content",
              "cacheCableRevision==liveCableRevision",
              "ItemStack.matches(snapshot,be.getBackpack())"):
    assert token in menu_src, ("B1258_GUI_SAFETY_MISSING", token)
assert "xsxPreviewStacks[previewIndex]=preview.copy()" in menu_src
assert "cachedPreview.copy()" in menu_src
assert "xsxPreviewStacks=new ItemStack[45]" in menu_src
be.write_text(be_src, encoding="utf-8")
menu.write_text(menu_src, encoding="utf-8")
print("B1258_BACKPACK_EXACT_CABLE_RESOURCE_REUSE_45_SLOT_GUI_PREVIEWS_PASS")
