#!/usr/bin/env python3
"""v1.7.4 B438: conservation and first-hunger-point feeding acceptance gate."""
import ast,os,json
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
s=(repo/"features/v174/apply-nutrition-438.py").read_text()
w=(repo/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(s)
for x in ("PowerArmorFeeding","NutriPaste.consume(helm,NutriPaste.HUNGER_COST)",
 "hunger.getFoodLevel()>=20","hunger.setFoodLevel(Math.min(20,hunger.getFoodLevel()+1))",
 "helm.get(ModDataComponents.POWER_ARMOR_UPGRADES.get())",
 "PASTE_CAPACITY=1_000_000_000L","HELMET_CAPACITY=1_000_000L",
 "DataComponents.FOOD","props.nutrition()","be.food.shrink(1)",
 "be.energy-=100L","be.paste+=made","NutriPaste.add(be.helmet,offer)",
 "be.paste-=inserted","Math.min(16,speed.getCount())",
 "Capabilities.Item.BLOCK","Capabilities.Energy.BLOCK"):
 assert x in s,x
assert s.count("HUNGER_COST=1_000L")==1
for x in ("python3 features/v174/apply-nutrition-438.py",
          "python3 tests/test_v174_nutrition_438.py"):
 assert x in w,x
assert w.index("python3 features/v174/apply-multiblock-animations-437.py")<w.index("python3 features/v174/apply-nutrition-438.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 for filename in ("NutriPaste","PowerArmorFeeding","NutrinatorBlock",
                  "NutrinatorBlockEntity","NutrinatorMenu","NutrinatorCapabilities"):
  assert (j/"nutrition"/(filename+".java")).is_file()
 a=(j/"powerarmor/PowerArmorCards.java").read_text()
 assert 'case "feeding"' in a
 p=Path(os.environ["V1_RESOURCE_ROOT"])
 for name in ("nutrinator","power_card_feeding"):
  assert (p/f"data/obsidiannetwork/recipe/{name}.json").is_file()
print("V174_NUTRITION_438_REGRESSION_PASS")
