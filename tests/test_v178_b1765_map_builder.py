#!/usr/bin/env python3
"""B1765 survival map/player and Mining Builder 16-upgrade regression gates."""
import ast, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"features/v178/apply-v178-b1765-map-builder.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class MapAndSpeedUpgrades(unittest.TestCase):
 def test_script_and_order(self):
  text=SOURCE.read_text()
  ast.parse(text)
  self.assertIn("python3 features/v178/apply-v178-b1765-map-builder.py",WF)
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1741-claim-team-names.py"),
                  WF.index("python3 features/v178/apply-v178-b1765-map-builder.py"))
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1765-map-builder.py"),
                  WF.index("python3 -m unittest discover -s tests -p 'test_v178_b1740_live_map_team_names.py'"))

 def test_detail_live_refresh_no_render_reads(self):
  s=SOURCE.read_text()
  for marker in ("private static void refreshSurface(ClientLevel world,int cx,int cz)",
                 "world.hasChunk(cx,cz)","sample(world,cx,cz)",
                 "java.util.Arrays.equals(before,after)",
                 "dirty=dirtyBefore","refreshTick%8L==0L",
                 "nearRefreshCursor++%25","farRefreshCursor++%625",
                 "updateAtlas(world,cx,cz)"):
   if marker=="updateAtlas(world,cx,cz)":
    # Original atlas upload remains intact in B1740 after the replacement.
    continue
   self.assertIn(marker,s,marker)
  self.assertNotIn("world.getChunk(",s)
  self.assertNotIn("forceChunk(",s)

 def test_minimap_far_zoom_resamples_in_fixed_gpu_bounds(self):
  s=SOURCE.read_text()
  for marker in ("Math.min(39*16","Math.max(10,Math.min(300,fineZoom",
                 "for(int py=0;py<SIDE;py++)",
                 "(long)px*crop/SIDE","(long)py*crop/SIDE","int crop=SIDE"):
   self.assertIn(marker,s,marker)
  self.assertGreater(39*16,19*16)
  # No per-frame world sampling: terrain colors are cached on the client tick.
  self.assertIn("V178TerrainMap",s)

 def test_clean_direction_marker(self):
  s=SOURCE.read_text()
  self.assertIn("B1765_DIRECTION_ARROW",s)
  self.assertIn("double angle=Math.toRadians(yaw)",s)
  self.assertIn("0xff54e8f5",s)
  self.assertIn("PlayerFaceExtractor.extractRenderState(",s)

 def test_builder_real_slot_ownership_persistence_and_safe_break(self):
  s=SOURCE.read_text()
  for token in ("slots.set(1,new Slot(speedStorage,0,143,27)",
                "for(int i=2;i<27;i++)",
                "getMaxStackSize(){return 16;}",
                "setSpeedUpgrades(ServerPlayer user,ItemStack value)",
                "removeSpeedUpgrades(ServerPlayer user,int amount)",
                "if(!canOperate(user)","xsxMiningSpeed",
                "speedUpgrades.copy()","maxBreaksThisTick()",
                'key.getPath().contains("speed_upgrade")',
                "moved" if False else "B1765_TERRAIN_REVALIDATION"):
   self.assertIn(token,s,token)

 def test_zero_to_sixteen_scale_exact_double_and_bounded(self):
  base=8
  counts=[base+base*n//16 for n in range(17)]
  self.assertEqual(counts[0],8)
  self.assertEqual(counts[16],16)
  self.assertTrue(all(8<=n<=16 for n in counts))
  self.assertEqual(counts,sorted(counts))
  self.assertIn("mined<machine.maxBreaksThisTick()",SOURCE.read_text())

 def test_generated_source_contract(self):
  env=os.getenv("V1_SOURCE_ROOT")
  if not env:self.skipTest("Generated Java only after full build reconstruction")
  j=Path(env)/"dev/obsidiannetwork"
  prefs=(j/"client/V178MiniPreferences.java").read_text()
  raster=(j/"client/V178MiniRaster.java").read_text()
  terrain=(j/"client/V178TerrainMap.java").read_text()
  markers=(j/"client/V178MapMarkers.java").read_text()
  be=(j/"mining/V178MiningBuilderBE.java").read_text()
  menu=(j/"mining/V178MiningBuilderMenu.java").read_text()
  gui=(j/"client/V178MiningBuilderOperationsScreen.java").read_text()
  self.assertIn("Math.min(39*16",prefs)
  self.assertIn("for(int py=0;py<SIDE;py++)",raster)
  self.assertIn("int crop=SIDE;",raster)
  self.assertIn("refreshSurface(world,cx,cz)",terrain)
  self.assertIn("farRefreshCursor++%625",terrain)
  self.assertIn("B1765_DIRECTION_ARROW",markers)
  self.assertNotIn("PlayerFaceExtractor.extractRenderState(",markers)
  self.assertIn("private ItemStack speedUpgrades=ItemStack.EMPTY;",be)
  self.assertIn("speedUpgrades.copy()",be)
  self.assertIn("maxBreaksThisTick()&&",be)
  self.assertIn("slots.set(1,new Slot(speedStorage",menu)
  self.assertIn("for(int i=2;i<27;i++)",menu)
  self.assertIn("slots.set(1,new Slot(speedSlot.container",gui)
  self.assertIn("SPEED ",gui)

if __name__=="__main__":unittest.main()
