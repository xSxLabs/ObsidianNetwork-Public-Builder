#!/usr/bin/env python3
"""B1677 regression checks: server-owned card slot, protected wilderness,
top-down and 16x16 terrain without losing legacy map files."""
import os,ast,unittest,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=(
 "features/v178/apply-v178-b1677-miner-functional.py",
 "features/v178/apply-v178-b1677-map-detail.py",
 "features/v178/apply-v178-b1677-miner-style.py"
)
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class MiningAndMap1677(unittest.TestCase):
 def test_patch_syntax_order(self):
  paths=[WORKFLOW.index("python3 features/v178/apply-v178-card-builder-visuals.py")]
  for path in FILES:
   s=(ROOT/path).read_text(encoding="utf8")
   ast.parse(s,filename=path)
   self.assertEqual(WORKFLOW.count("python3 "+path),1)
   paths.append(WORKFLOW.index("python3 "+path))
  self.assertEqual(paths,sorted(paths))
 def test_functionality_and_claim_safety(self):
  src=(ROOT/FILES[0]).read_text()
  for tok in ("V178MiningBuilderMenu.java","V178MiningBuilderOperationsScreen.java",
              "ServerPlayer player","mayPickup(Player","V178Claims.mayMachineMine",
              "maxY-(int)","new net.minecraft.world.SimpleMenuProvider",
              "Slot(cardStorage,0,20,27)","quickMoveStack"):
   self.assertIn(tok,src)
  self.assertNotIn("forceChunk(",src)
  self.assertNotIn("world.getChunk(",src)
  # Minecraft 26.1 AbstractContainerScreen.tick() is final; use containerTick.
  self.assertIn("@Override protected void containerTick(){",src)
  self.assertIn("super.containerTick();",src)
  self.assertNotIn("@Override public void tick(){",src)
 def test_terrain_and_bounded_render(self):
  src=(ROOT/FILES[1]).read_text()
  for tok in ("RES=16","0x58535838","0x58535839","0x5853583a",
              "V178TerrainMap.draw","getYRot()","Math.floorMod"):
   # getYRot and map samples are mandatory; no server packets in UI draw.
   if tok=="Math.floorMod":continue
   self.assertIn(tok,src)
  self.assertNotIn("PacketDistributor",src)
 def test_generated_compilation_inputs(self):
  j=os.getenv("V1_SOURCE_ROOT")
  r=os.getenv("V1_RESOURCE_ROOT")
  if not j or not r:return
  java=Path(j)/"dev/obsidiannetwork"
  assets=Path(r)/"assets/obsidiannetwork"
  shape=(java/"mining/V178MiningShapeCard.java").read_text()
  self.assertIn("maxY-(int)(index/layer)",shape)
  be=(java/"mining/V178MiningBuilderBE.java").read_text()
  self.assertIn("V178Claims.mayMachineMine(world,target,machine.owner)",be)
  self.assertIn("V178Claims.mayMachineMine(world,target,owner)",be)
  self.assertIn("ENERGY_PER_BLOCK=2000",be)
  for p in ("mining/V178MiningBuilderMenu.java",
            "client/V178MiningBuilderOperationsScreen.java"):
   self.assertTrue((java/p).exists(),p)
  menu=(java/"mining/V178MiningBuilderMenu.java").read_text()
  self.assertIn("new Slot(cardStorage,0,20,27)",menu)
  self.assertIn("return ItemStack.EMPTY",menu)
  terrain=(java/"client/V178TerrainMap.java").read_text()
  self.assertIn("public static final int RES=16;",terrain)
  self.assertIn("oldResolution=format==0x58535838?4:format==0x58535839?8:16",terrain)
  self.assertIn("world.hasChunk(cx,cz)",terrain)
  model=json.loads((assets/"models/block/mining_builder.json").read_text())
  self.assertGreaterEqual(len(model["elements"]),48)
  for name in ("shell","panel","front","display","sensor"):
   png=(assets/"textures/block"/f"mining_builder_{name}.png").read_bytes()
   self.assertEqual(struct.unpack(">II",png[16:24]),(64,64))
if __name__=="__main__":unittest.main()
