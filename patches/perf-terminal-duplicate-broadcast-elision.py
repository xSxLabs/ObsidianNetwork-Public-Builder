#!/usr/bin/env python3
"""Elide the *second* terminal menu packet sync after one crafting-grid update.

The existing slotsChanged path calls rebuildRecipeChoice(), which unconditionally
broadcasts changes on both branches (zero matching recipes / >=1 match),
then immediately calls broadcastChanges() AGAIN. There are no intervening
mutations; the redundant outer call incurs a second full menu diff/sync
under rapid shift-crafting and GUI interaction.

Preserve rebuildRecipeChoice's own broadcasts, including recipe choice button
events, and preserve all storage, crafting inventory, and rollback operations.
Fail closed when method structure / two independent broadcast paths drift.
"""
import os
from pathlib import Path
import re

src=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
s=src.read_text(encoding="utf-8")
marker="XSXLABS_TERMINAL_DUPLICATE_BROADCAST_ELISION_V1"
assert marker not in s
slots_start=re.search(r'\bpublic\s+void\s+slotsChanged\s*\(\s*Container\b',s)
slots_end=re.search(r'\bpublic\s+int\s+recipeChoiceCount\s*\(',s)
recipe_start=re.search(r'\bprivate\s+void\s+rebuildRecipeChoice\s*\(',s)
recipe_end=re.search(r'\bpublic\s+boolean\s+clickMenuButton\s*\(',s)
assert slots_start and slots_end and recipe_start and recipe_end,"Terminal method drift"
assert slots_start.start()<slots_end.start()<recipe_start.start()<recipe_end.start(),"Unexpected menu layout"
body=s[slots_start.start():slots_end.start()]
choice=s[recipe_start.start():recipe_end.start()]
assert choice.count("this.broadcastChanges();")==2, "Recipe choice must broadcast on both branches"
assert choice.count("return;")>=1, "Recipe choice no-match path lost"
assert "this.resultSlots" in choice and "setItem(" in choice, "Recipe result state drift"
assert body.count("this.rebuildRecipeChoice(")==1
assert body.count("this.broadcastChanges();")==1
assert "setCraftItem(" in body, "Expected nine-slot persistence in slotsChanged"
pat=re.compile(r'(?P<recipe>this\.rebuildRecipeChoice\([^;{}]*\);)\s*'
               r'(?P<broadcast>this\.broadcastChanges\(\);)')
match=list(pat.finditer(body))
assert len(match)==1,"Adjacent redundant menu sync anchor drift"
old=match[0].group()
repl=(match[0].group("recipe")+
      "\n         // XSXLABS_TERMINAL_DUPLICATE_BROADCAST_ELISION_V1\n"
      "         // rebuildRecipeChoice already broadcasts on ALL return paths.")
newbody=body.replace(old,repl,1)
assert newbody.count("this.broadcastChanges();")==0
assert newbody.count("this.rebuildRecipeChoice(")==1
assert choice.count("this.broadcastChanges();")==2
snew=s[:slots_start.start()]+newbody+s[slots_end.start():]
assert snew.count("this.broadcastChanges();")==s.count("this.broadcastChanges();")-1
src.write_text(snew,encoding="utf-8")
print("TERMINAL_ONE_BROADCAST_PER_CRAFT_GRID_CHANGE_V1 PASS")
