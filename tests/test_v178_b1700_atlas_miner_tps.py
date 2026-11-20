#!/usr/bin/env python3
"""B1700: 16x16 cached terrain atlas, low FPS render pressure, TPS-bounded miner."""
import ast
import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT="features/v178/apply-v178-b1700-atlas-and-tps-miner.py"
SOURCE=(ROOT/SCRIPT).read_text(encoding="utf8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf8")

class AtlasAndMiningRegression(unittest.TestCase):
 def test_syntax_and_order(self):
  ast.parse(SOURCE,filename=SCRIPT)
  self.assertEqual(WORKFLOW.count("python3 "+SCRIPT),1)
  self.assertLess(
   WORKFLOW.index("python3 features/v178/apply-v178-b1692-miner-cards-flight-cost.py"),
   WORKFLOW.index("python3 "+SCRIPT))
  self.assertLess(WORKFLOW.index("python3 "+SCRIPT),
   WORKFLOW.index("python3 -m unittest discover -s tests -p 'test_v178_b1700_atlas_miner_tps.py' -v"))

 def test_no_render_time_world_query_or_upload(self):
  for marker in (
   'new net.minecraft.client.renderer.texture.DynamicTexture',
   'new com.mojang.blaze3d.platform.NativeImage',
   'texture.upload();',
   'ATLAS_UPDATE_TICKS=4',
   'updateAtlas(world,cx,cz);',
   'B1707_FULL_PATCH_SOURCE_AUDIT',
   'GUI_TEXTURED',
   'void drawViewport(',
   'drawViewport(mc.level,g,cx,cz,',
   'drawViewport(world,g,cx,cz,',
   'resetAtlas();',
   'if(x==RES-1&&z==RES-1)atlasRevision++;',
   'radius2',
   'case 0->12;case 2->20;default->16;',
  ):self.assertIn(marker,SOURCE,marker)
  # Textures are recomposed only during tick, never within gui rendering.
  block=SOURCE.split("void draw(GuiGraphicsExtractor g,",1)[1].split("private static final Atlas",1)[0]
  self.assertNotIn("world.get",block)
  self.assertNotIn("texture.upload()",block)

 def test_sampling_cpu_and_mining_budget(self):
  for marker in (
   'new int[(RES+1)*(RES+1)]',
   'heights[z*(RES+1)+x]',
   'heights[(z+1)*(RES+1)+x]',
   'GLOBAL_MINER_TIME_BUDGET_NS=1_300_000L',
   'MAX_VISITS=32,MAX_BREAKS=8',
   'GLOBAL_BLOCK_BUDGET',
   'canMineThisTick(world)',
   'System.nanoTime()',
   'if(!budget(world))return;',
  ):
   if marker=='if(!budget(world))return;':
    # Original abort-transaction guard must survive the new budget gate.
    old=(ROOT/"features/v178/apply-v178-mining-builder.py").read_text()
    self.assertIn(marker,old)
   else:self.assertIn(marker,SOURCE,marker)
  self.assertNotIn("forceChunk(",SOURCE)
  self.assertNotIn("world.destroyBlock(target,true)",SOURCE)

 def test_generated_code(self):
  root=os.getenv("V1_SOURCE_ROOT")
  if not root:self.skipTest("Generated Java only exists inside full CI")
  j=Path(root)/"dev/obsidiannetwork"
  terrain=(j/"client/V178TerrainMap.java").read_text()
  machine=(j/"mining/V178MiningBuilderBE.java").read_text()
  for txt in ("new Atlas(7", "new Atlas(25", "drawViewport(", "texture.upload()",
              "atlasRevision++","resetAtlas()","getTextureManager().release"):
   self.assertIn(txt,terrain,txt)
  for txt in ("MAX_BREAKS=8", "GLOBAL_MINER_TIME_BUDGET_NS", "canMineThisTick",
              "Transaction.openRoot()", "world.destroyBlock(target,false)",
              "V178_SHAPE_CARD_FORTUNE_3", "V178_SHAPE_CARD_SILK_TOUCH",
              "machine.effectivePickaxe(world)"):
   self.assertIn(txt,machine,txt)
  for name in ("client/V178ClaimsClient.java",
               "client/V178ClaimsMapScreen.java",
               "client/V178MiningAreaScreen.java"):
   java=(j/name).read_text()
   self.assertIn("V178TerrainMap.drawViewport(",java,name)

if __name__=="__main__":unittest.main()
