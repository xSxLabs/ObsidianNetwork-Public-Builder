#!/usr/bin/env python3
"""Full v1.7.7 regression compatibility + v1.7.8 feature safeguards."""
import ast,os,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
P=("apply-v178-jarvis-hud.py","apply-v178-jei-terminal-session.py","apply-v178-global-perf.py")
class V178Regression(unittest.TestCase):
 def test_scripts_and_workflow(self):
  for name in P:
   s=(R/"features/v178"/name).read_text()
   ast.parse(s)
   self.assertIn("V178_",s)
   self.assertIn("python3 features/v178/"+name,W)
  self.assertLess(W.index("apply-v177-jarvis-voice.py"),W.index("apply-v178-jarvis-hud.py"))
  self.assertLess(W.index("apply-v177-jarvis-sethome-bridge.py"),W.index("apply-v178-jei-terminal-session.py"))
  self.assertIn("apply-v177-solid-fuel-generator-occlusion.py",W)
  self.assertIn("V178_JEI_HUD_GLOBAL_HOTPATH_JAR_GATE_PASS",W)
 def test_client_no_packets_or_unloaded_chunks(self):
  s=(R/"features/v178/apply-v178-jarvis-hud.py").read_text()
  for q in ("hud_radar","hud_hostiles","hud_players","hud_distance",
   "hud_altitude","hud_speed","hud_compass","hud_health",
   "hud_energy","hud_integrity","hud_warnings","SCAN_PERIOD=10",
   "MAX_DOTS=64","List.copyOf(found)","V177JarvisClient.available()"):
   self.assertIn(q,s)
  self.assertNotIn("sendCommand(",s)
  self.assertNotIn("getChunk(",s)
 def test_jei_real_menu_identity(self):
  s=(R/"features/v178/apply-v178-jei-terminal-session.py").read_text()
  for q in ("xsxTerminalMenu","xsxJeiQuery","ScreenEvent.Opening",
    "menu==xsxTerminalMenu","getIngredientFilter().getFilterText()",
    "getIngredientFilter().setFilterText(text)","xsxTerminalMenu=menu;"):
   self.assertIn(q,s)
  self.assertNotIn("getRecipeManager()",s)
 def test_whole_mod_perf_safe_changes(self):
  s=(R/"features/v178/apply-v178-global-perf.py").read_text()
  for q in ("V178_PERF_GRAPH_FACES","pathLoaded(world,adjoining)",
    "V178_PERF_STATION_PROXIMITY_FIRST","V178_PERF_IDLE_SCAN_SKIP",
    "V178_PERF_ENTITY_TYPE_PREFILTER","if(!PowerArmorRuntime.full(player))continue;"):
   self.assertIn(q,s)
  for forbidden in ("storage().extract(","storage().insert(","v177ConsumeFe(","setEnergy("):
   self.assertNotIn(forbidden,s)
 def test_reconstructed_java(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  self.assertIn("V178_PERF_GRAPH_FACES",(root/"power/V176PowerNetworkGraph.java").read_text())
  self.assertIn("V178_PERF_ENTITY_TYPE_PREFILTER",(root/"client/V177JarvisClient.java").read_text())
  self.assertIn("xsxJeiQuery=V177JeiSearchFocusBridge.filterText();",
    (root/"client/V177GuiInventoryKeyFocus.java").read_text())
  self.assertIn("MAX_DOTS=64",(root/"client/V178JarvisHud.java").read_text())
if __name__=="__main__": unittest.main()
