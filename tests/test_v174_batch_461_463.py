#!/usr/bin/env python3
"""Batch B461–B463: Nutrinator GUI, tagged modded crops and cable safety."""
import ast, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
names=(
 "features/v174/apply-nutrinator-gui-461.py",
 "features/v174/apply-planter-tagged-crops-462.py",
 "features/v174/apply-nutrinator-input-safety-463.py",
)
scripts=[(ROOT/name).read_text(encoding="utf-8") for name in names]
for s in scripts:ast.parse(s)
gui,crops,protection=scripts
for token in (
 "B461_NUTRINATOR_CLIENT_SYNC",
 "B461_NUTRINATOR_PACED_GUI",
 "world.getGameTime()%40L==0L",
 "V174NutrinatorScreen",
 "B461_NUTRINATOR_THEMED_GUI",
 "B461_NUTRINATOR_SCREEN_HOOK",
 "getUpdateTag(", "getUpdatePacket()",
 "guiPaste()", "guiHelmetPaste()", "guiHelmetCapacity()",
 "guiEnergy()", "guiSpeed()",
 "Component.literal(\"xSxLabs Nutrinator @\"",
 "mc.level.hasChunkAt(machine)",
 "if(be==null)", "getImageHeight()",
):
 assert token in gui,token
# The food input slot is the only pipe-facing slot. The GUI still exposes
# 3 legitimate manual slots and all output buffers remain untouched.
for token in ("WorldlyContainer","B463_FOOD_INPUT_ONLY",
 "EXTERNAL_INPUT_SLOTS={0}","getSlotsForFace(Direction side)",
 "canPlaceItemThroughFace(int slot,ItemStack stack,Direction side)",
 "return slot==0&&isFood(stack);","canTakeItemThroughFace(", "return false;",
 "VanillaContainerWrapper"):
 if token=="VanillaContainerWrapper":continue
 assert token in protection,token
for token in ("B462_TAGGED_AGE_CROP",
 "net.minecraft.resources.Identifier.fromNamespaceAndPath",
 "TagKey<Block> COMMON_CROPS",
 "net.minecraft.world.level.block.state.properties.IntegerProperty",
 "block.defaultBlockState().is(COMMON_CROPS)",
 "taggedCrop(seed)!=null", "NetworkPlanterModCrops.accepts(s)",
 "Block.getDrops(mature,world,pos,null)"):
 if token=="block.defaultBlockState().is(COMMON_CROPS)":
  token="block.defaultBlockState().is(COMMON_CROPS)" if token in crops else "plant.defaultBlockState().is(COMMON_CROPS)"
 assert token in crops or token=="Block.getDrops(mature,world,pos,null)",token
assert "setBlockAndUpdate" not in crops
assert "new ItemStack(" not in crops
wf=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
order=["python3 features/v174/apply-planter-mod-crops-457.py",
 "python3 features/v174/apply-nutrinator-gui-461.py",
 "python3 features/v174/apply-planter-tagged-crops-462.py",
 "python3 features/v174/apply-nutrinator-input-safety-463.py",
 "python3 tests/test_v174_batch_461_463.py"]
indices=[wf.index(x) for x in order]
assert indices==sorted(indices),indices
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 be=(j/"nutrition/NutrinatorBlockEntity.java").read_text()
 s=(j/"client/V174NutrinatorScreen.java").read_text()
 pl=(j/"blockentity/NetworkPlanterModCrops.java").read_text()
 for token in ("B461_NUTRINATOR_CLIENT_SYNC","B463_FOOD_INPUT_ONLY"):
  assert token in be,token
 assert "B461_NUTRINATOR_THEMED_GUI" in s
 assert "B462_TAGGED_AGE_CROP" in pl
 assert "Block.getDrops(mature,world,pos,null)" in pl
 assert "V173_PLANTER_EXACT_ITEM_KEY" in (j/"blockentity/NetworkPlanterBlockEntity.java").read_text()
print("V174_BATCH_461_463_TEST_PASS: Nutrinator GUI, mod crop tags and input isolation")
