#!/usr/bin/env python3
"""Index exact vanilla crafting recipes by occupied slot count per recipe map.

Build 346 guarded recipe.matches with a count prefilter, but still looped
through every single recipe for every result-slot Shift click. A single click
may craft dozens of results, and Spark 345 identified this full scan.
Here we build up to 10 ordered candidate lists lazily per Terminal menu.

Only concrete vanilla ShapedRecipe/ShapelessRecipe are count-filtered.
Every custom, subclassed, dynamic or non-placeable recipe is retained in every
candidate list and matches(input,level) is always called on each candidate.
Output deduction, recipe ordering, components and result selection are untouched.
Recipe-map identity invalidates all lists and counts after datapack reload.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_VANILLA_RECIPE_CARDINALITY_FASTPATH_V1"
marker2="XSXLABS_VANILLA_RECIPE_CANDIDATE_BUCKETS_V2"
assert marker not in s and marker2 not in s
sig="private List<RecipeHolder<CraftingRecipe>> matchingCraftRecipes(ServerLevel level, CraftingInput input) {"
assert s.count(sig)==1 and s.count("import net.minecraft.world.item.crafting.ShapedRecipe;")==1
start=s.index(sig)
end=s.index("private void rebuildRecipeChoice(",start)
body=s[start:end]
assert "XSXLABS_RECIPE_OUTPUT_BUCKETS_V1" in body
oldloop="for (RecipeHolder<CraftingRecipe> holder : level.recipeAccess().recipeMap().byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {"
assert body.count(oldloop)==1
oldmatch="CraftingRecipe recipe = holder.value();\n         if (!recipe.matches(input, level)) continue;"
assert body.count(oldmatch)==1
assert body.count("recipe.assemble(input)")==1

fields="""
   // XSXLABS_VANILLA_RECIPE_CARDINALITY_FASTPATH_V1
   // XSXLABS_VANILLA_RECIPE_CANDIDATE_BUCKETS_V2
   private Object xsxVanillaRecipeMapIdentity;
   private final java.util.IdentityHashMap<CraftingRecipe,Integer> xsxVanillaRecipeRequired =
       new java.util.IdentityHashMap<>();
   private final java.util.HashMap<Integer, List<RecipeHolder<CraftingRecipe>>> xsxRecipeCountCandidates =
       new java.util.HashMap<>();

"""
s=s.replace(sig,fields+"   "+sig,1)
start=s.index(sig)
end=s.index("private void rebuildRecipeChoice(",start)
body=s[start:end]
pre="""var xsxRecipeMap = level.recipeAccess().recipeMap();
      if (this.xsxVanillaRecipeMapIdentity != xsxRecipeMap) {
         this.xsxVanillaRecipeMapIdentity = xsxRecipeMap;
         this.xsxVanillaRecipeRequired.clear();
         this.xsxRecipeCountCandidates.clear();
      }
      int xsxOccupied = input.ingredientCount();
      List<RecipeHolder<CraftingRecipe>> xsxCandidates = this.xsxRecipeCountCandidates.get(xsxOccupied);
      if (xsxCandidates == null) {
         xsxCandidates = new java.util.ArrayList<>();
         // Preserve the original recipe registry iteration order in this list.
         for (RecipeHolder<CraftingRecipe> candidate : xsxRecipeMap.byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {
            CraftingRecipe candidateRecipe = candidate.value();
            // Dynamic and modded recipes ALWAYS remain candidates.
            if (candidateRecipe.getClass() == ShapedRecipe.class
                || candidateRecipe.getClass() == net.minecraft.world.item.crafting.ShapelessRecipe.class) {
               Integer expected = this.xsxVanillaRecipeRequired.get(candidateRecipe);
               if (expected == null) {
                  PlacementInfo placement = candidateRecipe.placementInfo();
                  int count = -1; // Not-placeable => do not skip its matches method.
                  if (!placement.isImpossibleToPlace()) {
                     count = 0;
                     IntList indices = placement.slotsToIngredientIndex();
                     for (int i = 0; i < indices.size(); ++i) {
                        int idx = indices.getInt(i);
                        if (idx >= 0 && !placement.ingredients().get(idx).isEmpty()) ++count;
                     }
                  }
                  this.xsxVanillaRecipeRequired.put(candidateRecipe, count);
                  expected = count;
               }
               if (expected >= 0 && expected != xsxOccupied) continue;
            }
            xsxCandidates.add(candidate);
         }
         this.xsxRecipeCountCandidates.put(xsxOccupied, xsxCandidates);
      }
      for (RecipeHolder<CraftingRecipe> holder : xsxCandidates) {"""
body=body.replace(oldloop,pre,1)
# Existing matching logic remains identical and is executed every time, even
# when the candidate list was indexed earlier in this menu session.
assert body.count(oldmatch)==1
s=s[:start]+body+s[end:]
assert s.count(marker)==1 and s.count(marker2)==1
assert s.count("if (!recipe.matches(input, level)) continue;")==1
assert s.count("xsxRecipeCountCandidates.clear();")==1
assert s.count("this.xsxRecipeCountCandidates.put(xsxOccupied, xsxCandidates);")==1
assert s.count("xsxCandidates.add(candidate);")==1
p.write_text(s,encoding="utf-8")
print("VANILLA_RECIPE_CANDIDATE_BUCKETS_V2 PASS: lazily indexed, map-reload-safe, original order and dynamic matching retained")
