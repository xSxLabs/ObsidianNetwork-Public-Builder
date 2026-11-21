#!/usr/bin/env python3
"""B1740+B1741 map and persistent team naming non-regression tests."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAP="features/v178/apply-v178-b1740-live-terrain-centered-minimap.py"
TEAM="features/v178/apply-v178-b1741-claim-team-names.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
MAP_SRC=(ROOT/MAP).read_text()
TEAM_SRC=(ROOT/TEAM).read_text()

class LiveMapAndTeamNames(unittest.TestCase):
 def test_overlay_order_and_python_syntax(self):
  ast.parse(MAP_SRC,MAP)
  ast.parse(TEAM_SRC,TEAM)
  for script in (MAP,TEAM):
   self.assertEqual(WORKFLOW.count("python3 "+script),1)
  a=WORKFLOW.index("python3 features/v178/apply-v178-b1730-minimap-wheel-customization.py")
  b=WORKFLOW.index("python3 "+MAP)
  c=WORKFLOW.index("python3 "+TEAM)
  self.assertLess(a,b)
  self.assertLess(b,c)
  self.assertLess(c,WORKFLOW.index("python3 -m unittest discover -s tests -p 'test_v178_b1740_live_map_team_names.py'"))

 def test_no_per_frame_world_reads_and_bounded_refresh(self):
  self.assertIn("world.getGameTime()%10L==0L",MAP_SRC)
  self.assertIn("if(world.hasChunk(rx,rz))",MAP_SRC)
  self.assertIn("java.util.Arrays.equals(previous,refreshed)",MAP_SRC)
  self.assertIn("V178TerrainMap.pixels(world",MAP_SRC)
  self.assertIn("new NativeImage(SIDE,SIDE,false)",MAP_SRC)
  self.assertIn("if(lastTick!=Long.MIN_VALUE&&tick>=lastTick&&tick-lastTick<2)return;",MAP_SRC)
  self.assertNotIn("world.getChunk(",MAP_SRC)
  self.assertNotIn("PacketDistributor",MAP_SRC)
  self.assertNotIn("Minecraft.getInstance().level.getBlockState(",MAP_SRC)
  self.assertIn("Math.min(19*16",MAP_SRC)

 def test_visual_alignment_and_skin(self):
  self.assertIn("int px=ox+4+7*step/2;",MAP_SRC)
  self.assertIn("int py=oy+15+7*step/2;",MAP_SRC)
  self.assertIn("if(miniCorner>=2)oy+=infoRows*lineHeight;",MAP_SRC)
  self.assertIn("miniCorner>=2?oy-infoRows*lineHeight",MAP_SRC)
  self.assertIn('PlayerFaceExtractor.extractRenderState(',MAP_SRC)
  self.assertIn('"Player Pos: "',MAP_SRC)
  self.assertIn('"Biome: "',MAP_SRC)
  self.assertIn('"coords","biome","chunk"',MAP_SRC)

 def test_team_server_permissions_persistence_packet_gui(self):
  for token in ("TEAM_NAMES.clear()",'data.append("N\\t")',
                "StringArgumentType.greedyString()",
                "if(MEMBER_TEAM.containsKey(leader))",
                "teamRename(ServerPlayer p,String name)",
                "if(!clean.matches", "new V178TeamSnapshot(",
                "buf.writeUtf(p.name(),40)",
                "renameTeam()", "data.name()"):
   self.assertIn(token,TEAM_SRC,token)
  self.assertNotIn("CLAIMS.put(",TEAM_SRC)
  self.assertNotIn("forceChunk(",TEAM_SRC)

 def test_generated_java_contract(self):
  root=os.getenv("V1_SOURCE_ROOT")
  if not root:self.skipTest("Only CI reconstructs Java source")
  j=Path(root)/"dev/obsidiannetwork"
  java=(j/"client/V178ClaimsClient.java").read_text()
  terrain=(j/"client/V178TerrainMap.java").read_text()
  raster=(j/"client/V178MiniRaster.java").read_text()
  info=(j/"client/V178MapInfo.java").read_text()
  markers=(j/"client/V178MapMarkers.java").read_text()
  backend=(j/"claims/V178Claims.java").read_text()
  snapshot=(j/"claims/V178TeamSnapshot.java").read_text()
  gui=(j/"client/V178ClaimTeamScreen.java").read_text()
  self.assertIn("V178MiniRaster.draw(g,ox,oy",terrain)
  self.assertIn("Arrays.equals(previous,refreshed)",terrain)
  self.assertIn("V178MiniRaster.tick(world)",terrain)
  self.assertIn("V178MapInfo.tick(world)",terrain)
  self.assertIn("cropPixels()",raster)
  self.assertIn("if(distance>outer2)color=0;",raster)
  self.assertNotIn("getHeight(",raster)
  self.assertIn("V178MapInfo.line",java)
  self.assertNotIn('"X: "+mc.player.blockPosition().getX()',java)
  self.assertIn("g.pose().scale(scale,scale)",info)
  self.assertIn("PlayerFaceExtractor.extractRenderState(",markers)
  self.assertIn("TEAM_NAMES.put(leader,clean)",backend)
  self.assertIn("TEAM_NAMES.clear()",backend)
  self.assertIn("V178TeamSnapshot(String leader,String members,String name)",snapshot)
  self.assertIn("send(\"name \"+name)",gui)

if __name__=="__main__":unittest.main()
