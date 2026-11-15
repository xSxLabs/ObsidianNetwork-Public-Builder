#!/usr/bin/env python3
"""v1.7.8 claim minimap and map overlay controls regression contracts."""
import os
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SOURCE=(R/"features/v178/apply-v178-claims.py").read_text()
class ClaimOverlayControls(unittest.TestCase):
 def test_minimap_key_registered_and_consumed(self):
  for token in ('GLFW.GLFW_KEY_N','event.register(TOGGLE_MINIMAP)','while(TOGGLE_MINIMAP.consumeClick())minimap=!minimap;'):
   self.assertIn(token,SOURCE)
 def test_independent_overlays(self):
  for token in ('showGrid=true,showForceLoaded=true,showCoordinates=true','toggleGrid()','toggleForceLoaded()','toggleCoordinates()','gridEnabled()','forceLoadedEnabled()','coordinatesEnabled()','GLFW.GLFW_KEY_1','GLFW.GLFW_KEY_2','GLFW.GLFW_KEY_3'):
   self.assertIn(token,SOURCE)
  self.assertIn('if(showForceLoaded&&(s&4)!=0)',SOURCE)
  self.assertIn('if(V178ClaimsClient.forceLoadedEnabled()&&(state&4)!=0)',SOURCE)
 def test_no_additional_server_requests_for_toggles(self):
  self.assertNotIn('request(cx,cz);return true;',SOURCE)
 def test_generated_client_controls(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:return
  client=(Path(root)/"dev/obsidiannetwork/client/V178ClaimsClient.java").read_text()
  screen=(Path(root)/"dev/obsidiannetwork/client/V178ClaimsMapScreen.java").read_text()
  self.assertIn('event.register(TOGGLE_MINIMAP)',client)
  self.assertIn('toggleCoordinates()',screen)
if __name__=="__main__":unittest.main()
