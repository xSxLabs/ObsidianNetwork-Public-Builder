#!/usr/bin/env python3
"""B1666 v1.7.8 map/Builder regression contracts (static and generated sources)."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=(
 "features/v178/apply-v178-builder-control-gui.py",
 "features/v178/apply-v178-map-controls.py",
 "features/v178/apply-v178-card-builder-visuals.py",
)
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class TestB1666(unittest.TestCase):
 def test_patch_order_and_syntax(self):
  for script in SCRIPTS:
   source=(ROOT/script).read_text(encoding="utf8")
   ast.parse(source,filename=script)
   self.assertEqual(WORKFLOW.count("python3 "+script),1)
  steps=[WORKFLOW.index("python3 features/v178/apply-v178-claim-ui.py")]
  steps.extend(WORKFLOW.index("python3 "+s) for s in SCRIPTS)
  self.assertEqual(steps,sorted(steps))
 def test_not_replacing_server_claim_rules(self):
  sources=[(ROOT/s).read_text() for s in SCRIPTS]
  self.assertNotIn("TICKETS.forceChunk",str(sources))
  self.assertIn("hasNeighborSignal",sources[0])
  self.assertIn("getAmountAsLong()",sources[0])
  self.assertIn("V178Claims.owner(world,target)",sources[0])
  self.assertIn("V178MapMobCache",sources[1])
  self.assertIn("V178MiniPreferences",sources[1])
  self.assertIn("0x58535838",sources[1])
  self.assertIn("0x58535839",sources[1])
  self.assertIn("mining_shape_card",sources[2])
 def test_generated_assets_and_java_contracts(self):
  src=os.getenv("V1_SOURCE_ROOT")
  res=os.getenv("V1_RESOURCE_ROOT")
  if not src or not res:return
  j=Path(src)/"dev/obsidiannetwork"
  r=Path(res)/"assets/obsidiannetwork"
  for file in (
   "mining/V178MiningBuilderControl.java",
   "mining/V178MiningBuilderStatus.java",
   "client/V178MiningBuilderClient.java",
   "client/V178MiningBuilderScreen.java",
   "client/V178MiniPreferences.java",
   "client/V178MapMobCache.java",
  ):self.assertTrue((j/file).is_file(),file)
  be=(j/"mining/V178MiningBuilderBE.java").read_text()
  self.assertIn("xsxMiningRedstoneMode",be)
  self.assertIn("hasNeighborSignal",be)
  self.assertIn("workState(ServerLevel world)",be)
  self.assertIn("V178Claims.mayMachineMine(world,target,owner)",be)
  mini=(j/"client/V178ClaimsClient.java").read_text()
  self.assertIn("V178MapMobCache.drawMini",mini)
  self.assertIn("V178MiniPreferences.visible",mini)
  terrain=(j/"client/V178TerrainMap.java").read_text()
  self.assertIn("public static final int RES=16;",terrain)
  self.assertIn("format==0x58535838",terrain)
  self.assertIn("world.hasChunk(cx,cz)",terrain)
  import json,struct
  card=json.loads((r/"models/item/mining_shape_card.json").read_text())
  self.assertEqual(card["textures"]["layer0"],"obsidiannetwork:item/mining_shape_card")
  cardpng=(r/"textures/item/mining_shape_card.png").read_bytes()
  self.assertEqual(struct.unpack(">II",cardpng[16:24]),(64,64))
  builder=json.loads((r/"models/block/mining_builder.json").read_text())
  self.assertGreaterEqual(len(builder["elements"]),20)
if __name__=="__main__":unittest.main()
