#!/usr/bin/env python3
"""B1662 visual refresh contract: HUD corners, claim UI, built-in 3D textures."""
import ast, json, os, struct, unittest, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[
 "features/v178/apply-v178-mining-builder-model.py",
 "features/v178/apply-v178-hud-corners.py",
 "features/v178/apply-v178-claim-ui.py",
]
SRC=[(ROOT/p).read_text(encoding="utf-8") for p in FILES]
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class VisualRefresh1662(unittest.TestCase):
 def test_batch_wiring_compiles(self):
  for name,script in zip(FILES,SRC):
   ast.parse(script,filename=name)
   self.assertIn("python3 "+name,WORKFLOW)
  chain=[
   "python3 features/v178/apply-v178-jarvis-hud.py",
   "python3 features/v178/apply-v178-mining-builder.py",
   "python3 features/v178/apply-v178-ftb-map-gui.py",
   "python3 features/v178/apply-v178-mining-map-gui.py",
   *["python3 "+name for name in FILES],
   "python3 -m unittest discover -s tests -p 'test_v178_visual_refresh.py' -v",
  ]
  indexes=[WORKFLOW.index(item) for item in chain]
  self.assertEqual(indexes,sorted(indexes))
  self.assertIn("B1662_HUD_SOURCE_DRIFT",SRC[1])
  self.assertIn("B1662_MINING_BLOCK_SOURCE_DRIFT",SRC[0])
  self.assertIn("B1662_GUI_SOURCE_DRIFT",SRC[2])

 def test_model_is_static_and_uses_custom_textures(self):
  script=SRC[0]
  for token in ("BlockStateProperties.HORIZONTAL_FACING",
                "registerDefaultState(stateDefinition.any()",
                "context.getHorizontalDirection().getOpposite()",
                'assert len(parts)==20',
                'mining_builder_"+name+".png"',
                'zlib.compress(bytes(rows),9)',
                '"north",0','"east",90','"south",180','"west",270'):
   self.assertIn(token,script)
  self.assertNotIn("BlockEntityRenderer",script)
  self.assertNotIn("tick(",script)
  self.assertNotIn("getChunk(",script)

 def test_hud_independent_corners_and_no_render_io(self):
  script=SRC[1]
  for token in ("radar_corner","text_corner",
                "public static int radarCorner()",
                "public static int textCorner()",
                "cycleRadar()","cycleText()",
                "case 0->","case 1->","case 2->",
                "V178HudLayout.radarCorner()",
                "V178HudLayout.textCorner()",
                "if(on(\"hud_radar\")&&radarCorner==textCorner)"):
   self.assertIn(token,script)
  self.assertIn("StandardCopyOption.ATOMIC_MOVE",script)

 def test_claim_minimap_and_screen_styling_no_server_mutation(self):
  script=SRC[2]
  for token in ("V178UiTheme.java",
                "V178UiTheme.panel(g",
                "V178UiTheme.miniFrame",
                "busy[V178HudLayout.radarCorner()]",
                "busy[V178HudLayout.textCorner()]",
                "client/V178ClaimsMapScreen.java",
                "client/V178MapSettingsScreen.java",
                "client/V178MiningAreaScreen.java"):
   self.assertIn(token,script)
  self.assertNotIn("TICKETS.forceChunk",script)
  self.assertNotIn("ServerLevel",script)

 def test_generated_resources_and_java(self):
  java_root=os.environ.get("V1_SOURCE_ROOT")
  resource_root=os.environ.get("V1_RESOURCE_ROOT")
  if not java_root or not resource_root:return
  j=Path(java_root)/"dev/obsidiannetwork"
  assets=Path(resource_root)/"assets/obsidiannetwork"
  block=(j/"mining/V178MiningBuilderBlock.java").read_text(encoding="utf-8")
  self.assertIn("BlockStateProperties.HORIZONTAL_FACING",block)
  self.assertIn("getStateForPlacement(BlockPlaceContext context)",block)
  model=json.loads((assets/"models/block/mining_builder.json").read_text())
  state=json.loads((assets/"blockstates/mining_builder.json").read_text())
  self.assertEqual(set(state["variants"]),{
   "facing=north","facing=south","facing=west","facing=east"})
  self.assertEqual(len(model["elements"]),1)
  # B1810 v15 intentionally replaces the older multi-part model and
  # its material dictionary with one baked cube and two original materials.
  self.assertEqual(set(model["textures"]),{"case","front","particle"})
  texture_names=("case","front")
  for name in texture_names:
   self.assertEqual(model["textures"][name],
     "obsidiannetwork:block/mining_builder_"+name+"_v15")
   png=(assets/"textures/block"/("mining_builder_"+name+"_v15.png")).read_bytes()
   self.assertEqual(png[:8],b"\x89PNG\r\n\x1a\n")
   self.assertEqual(struct.unpack(">II",png[16:24]),\n    (32,32) if name=="front" else (16,16))
   self.assertEqual(png[25],6) # RGBA 8-bit
   self.assertGreater(len(zlib.decompress(png[41:-16])),1024)
  hud=(j/"client/V178JarvisHud.java").read_text()
  layout=(j/"client/V178HudLayout.java").read_text()
  settings=(j/"client/V177JarvisSettingsScreen.java").read_text()
  self.assertIn("int textCorner=V178HudLayout.textCorner();",hud)
  self.assertIn("V178HudLayout::cycleRadar",settings)
  self.assertIn("V178HudLayout::cycleText",settings)
  self.assertIn("hud2-layout.properties",layout)
  self.assertNotIn("Files.read",hud)
  for rel in ("V178ClaimsMapScreen","V178MiningAreaScreen",
              "V178MapSettingsScreen","V178ClaimsTeamScreen"):
   self.assertIn("V178UiTheme.panel(",(j/"client"/(rel+".java")).read_text())

if __name__=="__main__":unittest.main()
