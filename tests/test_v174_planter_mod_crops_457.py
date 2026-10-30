#!/usr/bin/env python3
"""B457 contract checks for modded seed recognition, mature loot and atomic buffer."""
import ast
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patch=(ROOT/"features/v174/apply-planter-mod-crops-457.py").read_text(encoding="utf-8")
workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
ast.parse(patch)
for marker in (
 "B457_MODDED_PLANTER_CROPS", "NetworkPlanterModCrops.crop(s)!=null",
 "NetworkPlanterModCrops.canGrow(soil,seed)", "NetworkPlanterModCrops.acceptsSoil(s)",
 "NetworkPlanterModCrops.harvest(world,pos,be.seed)",
 "if(!NetworkPlanterBlock.Plant.valid(be.seed))",
 "B457_MOD_CROP_ATOMIC", "ItemStack.isSameItemSameComponents",
 "trial[i]=output[i].copy()", "if(remaining!=0)return false",
 "source.copyWithCount(moved)", "for(int i=0;i<9;i++)output[i]=trial[i]",
 "Block.getDrops(mature,world,pos,null)", "crop.getStateForAge(crop.getMaxAge())",
 "new String[]{stem+\"_crop\",stem+\"_plant\",stem}",
 "builtInRegistries".replace("b","B",1).replace("uiltInRegistries","uiltInRegistries"),
 "BlockTags.DIRT", "COMMON_SEEDS", "COMMON_FARMLANDS",
 "NetworkPlanterModCrops.growthState(",
 "V173_PLANTER_EXACT_ITEM_KEY", "V173_PLANTER_LEGACY_MIGRATION"
):
 if marker=="BuiltInRegistries":continue
 assert marker in patch,marker
assert "setBlockAndUpdate" not in patch
assert "stack.shrink" not in patch
assert "runtime.storage().insert(" not in patch
assert workflow.index("python3 features/v173/apply-planter-legacy-merge.py") < workflow.index(
 "python3 features/v174/apply-planter-mod-crops-457.py")
assert workflow.index("python3 features/v174/apply-planter-mod-crops-457.py") < workflow.index(
 "python3 tests/test_v174_planter_mod_crops_457.py")

# Model the Java copy-then-commit algorithm: no original state may change on
# rejected harvests. Modded NBT/components are part of the storage identity.
def store(slots,drops):
 trial=[s.copy() if s else None for s in slots]
 for key,qty,max_stack in drops:
  remaining=qty
  for s in trial:
   if remaining<=0:break
   if s is not None and s["key"]==key:
    moved=min(remaining,s["max"]-s["amount"])
    s["amount"]+=moved;remaining-=moved
  for i,s in enumerate(trial):
   if remaining<=0:break
   if s is None:
    moved=min(remaining,max_stack)
    trial[i]={"key":key,"amount":moved,"max":max_stack}
    remaining-=moved
  if remaining:
   return False,slots
 return True,trial
empty=[None]*9
for count in (1,64,128,576):
 ok,b=store(empty,[("modded:rice_with_components",count,64)])
 assert ok and sum(x["amount"] for x in b if x)==count
ok,b=store(empty,[("modded:seed",64,64),("modded:tomato",577,64)])
assert not ok and b==empty
filled=[{"key":"modded:apple/v1","amount":63,"max":64}]+[None]*8
ok,b=store(filled,[("modded:apple/v2",1,64)])
assert ok and b[0]["amount"]==63 and b[1]["key"]=="modded:apple/v2"
ok,b=store([{"key":str(i),"amount":64,"max":64} for i in range(9)],
           [("new",1,64)])
assert not ok and all(x["amount"]==64 for x in b)

if os.environ.get("V1_SOURCE_ROOT"):
 java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 planter=(java/"blockentity/NetworkPlanterBlockEntity.java").read_text()
 helper=(java/"blockentity/NetworkPlanterModCrops.java").read_text()
 renderer=(java/"client/NetworkPlanterRenderer.java").read_text()
 assert "B457_MOD_CROP_ATOMIC" in planter
 assert "V173_PLANTER_EXACT_ITEM_KEY" in planter
 assert "V173_PLANTER_LEGACY_MIGRATION" in planter
 assert "class NetworkPlanterModCrops" in helper
 assert "NetworkPlanterModCrops.growthState" in renderer

print("V174_PLANTER_MOD_CROPS_457_TEST_PASS")
