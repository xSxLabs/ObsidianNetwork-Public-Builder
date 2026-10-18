#!/usr/bin/env python3
"""JEI Crafting Terminal: build item-key candidate list just once per recipe.

The source has up to nine ingredient slots, each of which previously cloned
the *entire* storage index key set on every match scan. No network extraction,
reservation, per-slot player inventory, rollback, or error handling is changed.
During the planning stage the storage index is only read: extraction begins
after all candidates have been matched.
"""
import os
from pathlib import Path

f = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/menu/StorageTerminalMenu.java"
src = f.read_text(encoding="utf-8")
start = "public void applyJeiRecipeGrid("
stop = "private static Ingredient[] recipeIngredients3x3("
assert src.count(start) == src.count(stop) == 1, "JEI section boundary changed"
a = src.index(start)
b = src.index(stop, a)
before, section, after = src[:a], src[a:b], src[b:]
old_start = """                        HashMap<ItemKey, Long> reservedNet = new HashMap<>();
                        int invSize = sp.getInventory().getContainerSize();"""
new_start = """                        HashMap<ItemKey, Long> reservedNet = new HashMap<>();
                        // XSXLABS_JEI_ONCE_PER_RECIPE_KEYS_V1: same ordered index
                        // snapshot for all nine read-only recipe preflight slots.
                        // The original exact-count reservation, extraction
                        // and transactional rollback remain unchanged below.
                        var availableKeys = runtime.storage().index().keysSnapshot();
                        int invSize = sp.getInventory().getContainerSize();"""
old_loop = "for (ItemKey key : runtime.storage().index().keysSnapshot()) {"
new_loop = "for (ItemKey key : availableKeys) {"
for old, new in ((old_start, new_start), (old_loop, new_loop)):
    assert section.count(old) == 1, ("JEI source anchor drift", old[:90], section.count(old))
    section = section.replace(old,new,1)
for token in ("reservedNet.merge(bestKey, 1L, Math::addExact);",
              "runtime.storage().extract(desc[ixx].key(), 1L)",
              "runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L)",
              "this.batchingCraftMutation = false;",
              "ServerTerminalPayloadHandler.flushRuntimeDeltas(level, runtime);"):
    assert section.count(token) == 1, ("JEI conservation guard drift",token)
assert section.count("runtime.storage().index().keysSnapshot()") == 1
f.write_text(before + section + after, encoding="utf-8")
print("JEI_ONCE_PER_RECIPE_KEYS_V1 PASS")
