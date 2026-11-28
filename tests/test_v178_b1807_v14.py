#!/usr/bin/env python3
"""B1807 regression checks for archive precedence, UI slot isolation and throughput."""
import ast,os,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'features/v178/apply-v178-b1807-v14.py'
W=(R/'.github/workflows/networkstorage-v1.7-clean.yml').read_text()

class V14MapAndBuilder(unittest.TestCase):
 def test_patch_order_and_artifact_name(self):
  ast.parse(P.read_text())
  p='python3 features/v178/apply-v178-b1807-v14.py'
  self.assertIn(p,W)
  self.assertLess(W.index('python3 features/v178/apply-v178-b1804-v13.py'),W.index(p))
  self.assertIn("python3 -m unittest discover -s tests -p 'test_v178_b1807_v14.py'",W)
  self.assertIn('xSxLabs-Network-Storage-1.7.8-v21.jar',W)
  self.assertIn('xsxlabs-network-storage-1.7.8-v21',W)
 def test_live_terrain_beats_archive(self):
  s=P.read_text()
  self.assertIn('world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)',s)
  self.assertIn('!java.util.Arrays.equals(previous,colors)',s)
  self.assertIn('r.tiles.put(key,colors)',s)
  self.assertNotIn('forceChunk(',s)
 def test_independent_card_and_speed_slots(self):
  s=P.read_text()
  self.assertIn('new Slot(speedSlot.container,1,143,27)',s)
  self.assertIn('moveItemStackTo(held,0,1,false)',s)
  self.assertIn('moveItemStackTo(held,1,2,false)',s)
  self.assertIn('moveItemStackTo(held,27,63,true)',s)
 def test_batched_transactional_export(self):
  s=P.read_text()
  self.assertIn('movedStacks<32',s)
  self.assertIn('try(Transaction tx=Transaction.openRoot())',s)
  self.assertIn('destination.insert(what,count,tx)',s)
  self.assertIn('output.extract(slot,what,accepted,tx)==accepted',s)
  self.assertIn('tx.commit()',s)
 def test_reconstructed_sources(self):
  root=os.environ.get('V1_SOURCE_ROOT')
  if not root:self.skipTest('requires reconstructed CI Java sources')
  j=Path(root)/'dev/obsidiannetwork'
  terrain=(j/'client/V178TerrainMap.java').read_text()
  gui=(j/'client/V178MiningBuilderOperationsScreen.java').read_text()
  menu=(j/'mining/V178MiningBuilderMenu.java').read_text()
  be=(j/'mining/V178MiningBuilderBE.java').read_text()
  self.assertIn('world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)',terrain)
  self.assertNotIn('r.tiles.putIfAbsent(pos(cx,cz),colors)',terrain)
  self.assertIn('new Slot(speedSlot.container,1,143,27)',gui)
  self.assertIn('moveItemStackTo(held,0,1,false)',menu)
  self.assertIn('moveItemStackTo(held,1,2,false)',menu)
  self.assertNotIn('if(world.getGameTime()%5!=0)return;',be)
  self.assertIn('B1807_BATCHED_OUTPUT',be)

if __name__=='__main__': unittest.main()
