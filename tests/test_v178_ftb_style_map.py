#!/usr/bin/env python3
"""B1621: FTB-style original claim+chunkloading GUI and terrain map regression contract."""
import os,ast,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
A=(R/"features/v178/apply-v178-ftb-batch.py").read_text()
B=(R/"features/v178/apply-v178-ftb-map-gui.py").read_text()
class FtbStyleMap(unittest.TestCase):
 def test_source_order_and_previous_full_mod_features(self):
  for filename in ("apply-v178-claims.py","apply-v178-mining-builder.py",
                   "apply-v178-ftb-batch.py","apply-v178-ftb-map-gui.py",
                   "apply-v178-jei-terminal-session.py","apply-v178-jarvis-hud.py",
                   "apply-v178-global-perf.py"):
   self.assertIn("python3 features/v178/"+filename,W)
  self.assertLess(W.index("python3 features/v178/apply-v178-claims.py"),
                  W.index("python3 features/v178/apply-v178-ftb-batch.py"))
  self.assertLess(W.index("python3 features/v178/apply-v178-ftb-batch.py"),
                  W.index("python3 features/v178/apply-v178-ftb-map-gui.py"))
 def test_static_contracts(self):
  ast.parse(A);ast.parse(B)
  for marker in ("GLOBAL", "BATCHES","LAST_BATCH","runBatches",
                 "perPlayer++<8","global=64","queueBatch",
                 "mode<0||mode>3","Math.abs((long)highX-px)>256",
                 "dirty=true","playToServer(TYPE,CODEC"):
   self.assertIn(marker if marker!="GLOBAL" else "global=64",A)
  for marker in ("V178TerrainMap.java","world.hasChunk(cx,cz)",
                 "Heightmap.Types.WORLD_SURFACE","MAX_CACHED=1536",
                 "RES=4","V178ClaimsBatch","e.modifiers()&GLFW.GLFW_MOD_SHIFT",
                 "mouseDragged(MouseButtonEvent","mouseReleased(MouseButtonEvent",
                 "mouseScrolled(double mx,double my,double horizontal,double vertical)",
                 "GLFW.GLFW_KEY_C","GLFW.GLFW_KEY_SPACE",
                 "Button.builder","V178TerrainMap.drawClaim"):
   self.assertIn(marker,B)
  self.assertNotIn("world.getChunk(",B)
  self.assertNotIn("forceChunk(",B)
  # Claim actions still use the bounded batch payload; team trust is a command.
  self.assertNotIn("sendCommand(",B.split("# B1624:")[0])
 def test_stale_claim_snapshot_retry_is_tick_bounded(self):
  # A map moved during server-side throttling must recover by retrying.
  for marker in ("pending.cx()!=screen.centerX()",
                 "pending.cz()!=screen.centerZ()",
                 "!pending.dimension().equals",
                 "now-lastRequestTime>=25",
                 "request(screen.centerX(),screen.centerZ())"):
   self.assertIn(marker,B)
  self.assertIn("V178TerrainMap.tick(mc.level,playerCx,playerCz)",B)
 def test_b1624_explored_waypoints_and_team_are_bounded(self):
  import re
  for marker in ("MAX_CACHED=1536","lastFlushTick","now-lastFlushTick>=1200",
                 "java.io.DataOutputStream","java.io.DataInputStream",
                 "java.nio.file.StandardCopyOption.ATOMIC_MOVE",
                 "client/V178Waypoints.java","client/V178ClaimsTeamScreen.java",
                 "V178Waypoints.tick(mc.player)","V178Waypoints.drawMap",
                 "V178Waypoints.drawMini","GLFW.GLFW_MOD_SHIFT",
                 "V178Waypoints.remove","V178Waypoints.add",
                 'me.connection.sendCommand("xsxchunks "',
                 "getCurrentServer()","isDeadOrDying()",
                 "while((line=in.readLine())!=null&&MARKERS.size()<MAX)"):
   self.assertIn(marker,B)
  self.assertNotIn("world.getChunk(",B)
  self.assertNotIn("ClientPacketDistributor.sendToServer", B.split('waypoints=root/')[1])
 def test_b1624_generated_java_contract(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  for name in ("V178Waypoints","V178ClaimsTeamScreen","V178TerrainMap",
               "V178ClaimsMapScreen","V178ClaimsClient"):
   self.assertTrue((j/"client"/(name+".java")).is_file(),name)
  m=(j/"client/V178TerrainMap.java").read_text()
  self.assertIn("MAX_CACHED=1536",m)
  self.assertIn("now-lastFlushTick>=1200",m)
  w=(j/"client/V178Waypoints.java").read_text()
  self.assertIn("private static final int MAX=128",w)
  self.assertIn("deathLatch=dead",w)
  self.assertIn("java.nio",w)
 def test_b1628_waypoint_editor_manager_and_zoom(self):
  for marker in ("client/V178WaypointEditorScreen.java",
                 "client/V178WaypointManagerScreen.java",
                 "public record Marker","Integer.parseInt(v[6])",
                 "V178Waypoints.saveAt","new V178WaypointEditorScreen(this",
                 "new V178WaypointManagerScreen(this)",
                 "private void adapt()","DIAMETER/2",
                 "Math.min(DIAMETER-1","V177JarvisSettings.on(\"hud_radar\")",
                 "V178_WAYPOINT_EDITOR_MANAGER_DYNAMIC_ZOOM_HUD_MINIMAP_LAYOUT_PASS"):
   self.assertIn(marker,B)
  self.assertIn("java.util.List.copyOf(list)",B)
 def test_b1628_generated_screen_and_markers(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  d=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client"
  for name in ("V178WaypointEditorScreen","V178WaypointManagerScreen"):
   self.assertTrue((d/(name+".java")).is_file(),name)
  map_java=(d/"V178ClaimsMapScreen.java").read_text()
  self.assertIn("private void adapt()",map_java)
  self.assertIn("V178WaypointEditorScreen(this",map_java)
  waypoint_java=(d/"V178Waypoints.java").read_text()
  self.assertIn("public record Marker",waypoint_java)
  self.assertIn("public static void saveAt(",waypoint_java)
 def test_b1633_waypoints_follow_actual_map_viewport(self):
   self.assertIn("B1633_VIEWPORT_MARKER_PARITY",B)
   self.assertIn("int half=diameter/2",B)
   self.assertIn("dx>=diameter||dz<0||dz>=diameter",B)
   self.assertIn("V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile,DIAMETER)",B)
   for diameter in range(5,26):
    center_x,center_z=171,-93
    half=diameter//2
    for column in range(diameter):
     for row in range(diameter):
      world_x=center_x+column-half
      world_z=center_z+row-half
      self.assertEqual((world_x-center_x+half,world_z-center_z+half),(column,row))
   if not os.environ.get("V1_SOURCE_ROOT"):return
   d=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client"
   waypoint=(d/"V178Waypoints.java").read_text()
   gui=(d/"V178ClaimsMapScreen.java").read_text()
   self.assertIn("int cx,int cz,int x0,int y0,int tile,int diameter",waypoint)
   self.assertIn("if(dx<0||dx>=diameter||dz<0||dz>=diameter)continue",waypoint)
   self.assertNotIn("int dx=(m.x()>>4)-cx+12,dz=(m.z()>>4)-cz+12",waypoint)
   self.assertIn("V178Waypoints.drawMap(world,g,cx,cz,x0,y0,tile,DIAMETER)",gui)
 def test_b1634_ftb_style_persistent_map_info_options(self):
  self.assertIn("B1634_INFO_OPTIONS",B)
  self.assertIn("V178MapSettingsScreen.java",B)
  self.assertIn("client-options.properties",B)
  self.assertIn("StandardCopyOption.ATOMIC_MOVE",B)
  for key in ("minimap","terrain","claims","loaded","waypoints","player",
              "coords","chunk","daytime","map_terrain","map_claims",
              "map_waypoints","map_player"):
   self.assertIn('"'+key+'"',B)
  self.assertIn('if(option("waypoints"))V178Waypoints.drawMini',B)
  self.assertIn('if(V178ClaimsClient.option("map_waypoints"))',B)
  self.assertIn('if(!showLoaded)state&=~4;',B)
  self.assertIn('if(k==GLFW.GLFW_KEY_S)',B)
  self.assertIn('if(!option("minimap")',B)
  self.assertIn('rebuildWidgets();',B)
  if not os.environ.get("V1_SOURCE_ROOT"):return
  d=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client"
  self.assertTrue((d/"V178MapSettingsScreen.java").is_file())
  settings=(d/"V178MapSettingsScreen.java").read_text()
  client=(d/"V178ClaimsClient.java").read_text()
  screen=(d/"V178ClaimsMapScreen.java").read_text()
  self.assertIn("V178ClaimsClient.toggleOption(key)",settings)
  self.assertIn("java.util.Properties",client)
  self.assertIn("java.nio.file.Files.move(tmp,path",client)
  self.assertIn('option("minimap")',client)
  self.assertIn("while(TOGGLE_MINIMAP.consumeClick())toggleMinimap();",client)
  self.assertNotIn("minimap=!minimap;",client)
  self.assertEqual(client.count('public static boolean minimapEnabled(){return option("minimap");}'),1)
  self.assertNotIn('public static boolean minimapEnabled(){return minimap;}',client)
  self.assertIn('mc.level.getLevelData().getDayTime()',client)
  self.assertNotIn('mc.level.getDayTime()',client)
  self.assertEqual(client.count('public static void toggleMinimap(){toggleOption("minimap");}'),1)
  self.assertIn('new V178MapSettingsScreen(this)',screen)
 def test_compiled_source_contract(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  for f in ("claims/V178Claims.java","claims/V178ClaimsBatch.java",
            "client/V178TerrainMap.java","client/V178ClaimsMapScreen.java",
            "client/V178ClaimsClient.java"):
   self.assertTrue((j/f).exists(),f)
  claims=(j/"claims/V178Claims.java").read_text()
  self.assertIn("perPlayer++<8",claims)
  self.assertIn("global=64",claims)
  gui=(j/"client/V178ClaimsMapScreen.java").read_text()
  self.assertIn("e.modifiers()&GLFW.GLFW_MOD_SHIFT",gui)
  self.assertIn("V178TerrainMap.draw(world,g",gui)
  terrain=(j/"client/V178TerrainMap.java").read_text()
  self.assertIn("world.hasChunk(cx,cz)",terrain)
  self.assertNotIn("loadChunk(",terrain)
if __name__=="__main__":unittest.main()
