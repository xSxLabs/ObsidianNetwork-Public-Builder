#!/usr/bin/env python3
"""Avoid matching impossible vanilla recipes in the 3x3 terminal.

Only exact vanilla ShapedRecipe/ShapelessRecipe classes are prefitered based
on immutable placement metadata (non-empty ingredient count). Subclassed,
modded and dynamic recipes always run their normal matches(input,level).
Recipe-map identity invalidates the per-menu count cache after datapack reload.
Do not change matching recipe ordering, result-output dedup or exact components.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_VANILLA_RECIPE_CARDINALITY_FASTPATH_V1"
assert marker not in s
sig="private List<RecipeHolder<CraftingRecipe>> matchingCraftRecipes(ServerLevel level, CraftingInput input) {"
assert s.count(sig)==1 and s.count("import net.minecraft.world.item.crafting.ShapedRecipe;")==1
begin=s.index(sig)
end=s.index("private void rebuildRecipeChoice(",begin)
body=s[begin:end]
assert "XSXLABS_RECIPE_OUTPUT_BUCKETS_V1" in body
loop="for (RecipeHolder<CraftingRecipe> holder : level.recipeAccess().recipeMap().byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {"
assert body.count(loop)==1
need="CraftingRecipe recipe = holder.value();\n         if (!recipe.matches(input, level)) continue;"
assert body.count(need)==1
assert "recipe.assemble(input)" in body

fields="""
   // XSXLABS_VANILLA_RECIPE_CARDINALITY_FASTPATH_V1
   // Per-menu identity cache. Never use across a recipe-map/datapack reload.
   private Object xsxVanillaRecipeMapIdentity;
   private final java.util.IdentityHashMap<CraftingRecipe,Integer> xsxVanillaRecipeRequired =
       new java.util.IdentityHashMap<>();

"""
assert s.count(sig)==1
s=s.replace(sig,fields+"   "+sig,1)
begin=s.index(sig)
end=s.index("private void rebuildRecipeChoice(",begin)
body=s[begin:end]
body=body.replace(loop,"""var xsxRecipeMap = level.recipeAccess().recipeMap();
      if (this.xsxVanillaRecipeMapIdentity != xsxRecipeMap) {
         this.xsxVanillaRecipeMapIdentity = xsxRecipeMap;
         this.xsxVanillaRecipeRequired.clear();
      }
      int xsxOccupied = input.ingredientCount();
      for (RecipeHolder<CraftingRecipe> holder : xsxRecipeMap.byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {""",1)
body=body.replace(need,"""CraftingRecipe recipe = holder.value();
         // Only concrete vanilla implementations have fixed ingredient cardinality.
         // Leave all modded/special/dynamic recipes on their original exact path.
         if (recipe.getClass() == ShapedRecipe.class
             || recipe.getClass() == net.minecraft.world.item.crafting.ShapelessRecipe.class) {
            Integer expected = this.xsxVanillaRecipeRequired.get(recipe);
            if (expected == null) {
               PlacementInfo placement = recipe.placementInfo();
               int count = -1; // Unknown placement => do not filter.
               if (!placement.isImpossibleToPlace()) {
                  count = 0;
                  IntList indices = placement.slotsToIngredientIndex();
                  for (int i = 0; i < indices.size(); ++i) {
                     int idx = indices.getInt(i);
                     if (idx >= 0 && !placement.ingredients().get(idx).isEmpty()) ++count;
                  }
               }
               this.xsxVanillaRecipeRequired.put(recipe, count);
               expected = count;
            }
            if (expected >= 0 && expected != xsxOccupied) continue;
         }
         if (!recipe.matches(input, level)) continue;""",1)
s=s[:begin]+body+s[end:]
assert s.count(marker)==1 and s.count("if (!recipe.matches(input, level)) continue;")==1
assert "byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)" in body
p.write_text(s,encoding="utf-8")
print("VANILLA_RECIPE_CARDINALITY_FASTPATH_V1 PASS: exact concrete vanilla only; modded recipe matching unchanged")