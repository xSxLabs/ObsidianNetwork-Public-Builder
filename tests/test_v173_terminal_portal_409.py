#!/usr/bin/env python3
"""B409 safeguards: don't regress the 1.7.2-fast click/TPS or JEI partial +."""
import ast, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v173/apply-hotfix-terminal-portals-409.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class TerminalPortal409(unittest.TestCase):
 def test_script_parses_and_contains_bounded_lookup(self):
  ast.parse(PATCH)
  for text in ("B409_TERMINAL_BFS_TICK_CACHE","if(RESOLVING.get()||queried==null)return null;",
       "LOOKUPS.computeIfAbsent(level","long tick=level.getGameTime();",
       "if(lookups.tick!=tick)","lookups.results.clear();",
       "lookups.results.containsKey(cachePos)","known!=null&&known.powered()",
       "lookups.results.put(cachePos,null)","lookups.results.put(cachePos,rt)",
       "finally{RESOLVING.set(false);}"):
   self.assertIn(text,PATCH)
  # No persistent cached inventory or stored item descriptors.
  self.assertNotIn("storage().index().keysSnapshot()",PATCH)
  self.assertNotIn("storage().extract(",PATCH)
  self.assertNotIn("storage().insert(",PATCH)
 def test_four_way_portal_state_visual_and_entry(self):
  for direction in ('"north"','"east"','"south"','"west"'):
   self.assertIn(direction,PATCH)
  for token in ("BlockStateProperties.HORIZONTAL_FACING",
                "getHorizontalDirection().getOpposite()",
                "builder.add(FACING)",
                "getAxis()==Direction.Axis.X",
                "B409_PORTAL_RENDER_AXIS",
                "eastWest?centerZ-half:z",
                "eastWest?inner:.034D",
                "setValue(PortalGateBlock.FACING,player.getDirection())"):
   self.assertIn(token,PATCH)
 def test_jei_404_is_preserved(self):
  for token in ("B404_JEI_COSMETIC_MISSING","Type.COSMETIC",
                "JeiCraftTransferPayload(","B368_PARTIAL_INGREDIENTS",
                "xsxRecipeIngredientAccepts"):
   self.assertIn(token,PATCH)
 def test_integration_stage(self):
  for line in ("python3 features/v173/apply-hotfix-terminal-portals-409.py",
               "python3 tests/test_v173_terminal_portal_409.py"):
   self.assertIn(line,WF)
  self.assertLess(WF.index("python3 features/v173/apply-wireless-cable-entry-guard.py"),
                  WF.index("python3 features/v173/apply-hotfix-terminal-portals-409.py"))
  self.assertLess(WF.index("python3 features/v173/apply-jei-cosmetic-partial-404.py"),
                  WF.index("python3 features/v173/apply-hotfix-terminal-portals-409.py"))
 def test_real_reconstructed_java_when_available(self):
  if not os.environ.get("V1_SOURCE_ROOT"): return
  root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  remote=(root/"network/NetworkSignalRelayBridge.java").read_text()
  portal=(root/"portal/PortalGateBlock.java").read_text()
  renderer=(root/"client/V173WorldGhostRenderer.java").read_text()
  self.assertEqual(remote.count("B409_TERMINAL_BFS_TICK_CACHE"),1)
  self.assertIn("LOOKUPS.computeIfAbsent(level",remote)
  self.assertIn("if(lookups.tick!=tick)",remote)
  self.assertIn("FACING=BlockStateProperties.HORIZONTAL_FACING",portal)
  self.assertIn("B409_PORTAL_RENDER_AXIS",renderer)
  for name in ("network_portal_a","network_portal_b"):
   import json
   assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/blockstates"/(name+".json")
   mapping=json.loads(assets.read_text())["variants"]
   self.assertEqual(set(mapping),{"facing=north","facing=east","facing=south","facing=west"})
if __name__=="__main__": unittest.main()
