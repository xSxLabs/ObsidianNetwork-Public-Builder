#!/usr/bin/env python3
"""Regression gate for B404 AE2-like JEI hover red + clickable partial transfer."""
import ast
import os
from pathlib import Path

here=Path(__file__).resolve().parents[1]
patch=(here/"features/v173/apply-jei-cosmetic-partial-404.py").read_text(encoding="utf-8")
ast.parse(patch)
for required in (
 "B404_JEI_COSMETIC_MISSING",
 "Type.COSMETIC",
 "getMissingCountHint()",
 "getButtonHighlightColor()",
 "showError(",
 "drawHighlight(graphics,0x99FF3030)",
 "getSlotViews(RecipeIngredientRole.INPUT)",
 "StorageTerminalMenu.CRAFT_START",
 "StorageTerminalMenu.CRAFT_END",
 "getComponentsPatch().isEmpty()",
 "B368_PARTIAL_INGREDIENTS",
 "xsxRecipeIngredientAccepts",
 "JEI rollback incomplete",
):
    assert required in patch, ("B404_REQUIRED_SEMANTIC_MISSING",required)
assert "Type.USER_FACING" not in patch
assert "createUserErrorForMissingSlots" not in patch
assert "if (!doTransfer)" in patch
# This is a regression fixture, not a replacement for the dedicated-server
# and client build's actual JEI integration test.
def missing_for_recipe(stocks, choices):
    stock=[dict(item=k,count=c) for k,c in stocks]
    order=sorted(enumerate(choices),key=lambda pair:len(pair[1]))
    missing=[]
    for original,alts in order:
        selected=None
        for v in alts:
            for s in stock:
                if s["item"]==v and s["count"]>0:
                    selected=s
                    break
            if selected is not None:break
        if selected is None: missing.append(original)
        else: selected["count"]-=1
    return sorted(missing)
assert missing_for_recipe([("minecraft:iron_ingot",1)],
   [["minecraft:iron_ingot"],["minecraft:iron_ingot"],["minecraft:gold_ingot"]])==[1,2]
assert missing_for_recipe([("minecraft:oak_planks",1)],
   [["minecraft:oak_planks","minecraft:birch_planks"],["minecraft:oak_planks"]])==[0]
assert missing_for_recipe([("minecraft:stone",8)],
   [["minecraft:stone"]]*8)==[]
assert missing_for_recipe([], [["minecraft:stone"]])==[0]

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork" if os.environ.get("V1_SOURCE_ROOT") else None
if java:
    handler=(java/"compat/jei/NetworkStorageRecipeTransferHandler.java").read_text(encoding="utf-8")
    screen=(java/"client/StorageTerminalScreen.java").read_text(encoding="utf-8")
    menu=(java/"menu/StorageTerminalMenu.java").read_text(encoding="utf-8")
    assert "B404_JEI_RED_MISSING" in handler and "B404_JEI_COSMETIC_MISSING" in handler
    assert "Type.COSMETIC" in handler and "Type.USER_FACING" not in handler
    assert "ClientPacketDistributor.sendToServer(new JeiCraftTransferPayload(" in handler
    assert "if (!doTransfer)" in handler
    assert "java.util.Collections.unmodifiableMap(this.clientState.snapshot())" in screen
    assert "B368_PARTIAL_INGREDIENTS" in menu
    assert "xsxRecipeIngredientAccepts" in menu
    assert "JEI rollback incomplete" in menu
print("B404_JEI_RED_HOVER_PARTIAL_CLICK_REGRESSION_PASS")
