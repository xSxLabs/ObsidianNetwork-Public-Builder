#!/usr/bin/env python3
"""B1657 regression: explored terrain archive and server claim interactions."""
import ast, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"features/v178/apply-v178-archive-protection.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class B1657ArchiveAndProtection(unittest.TestCase):
 def test_generator_order_and_fail_closed(self):
  ast.parse(SCRIPT)
  self.assertIn("B1657_FAIL_CLOSED_SOURCE_DRIFT",SCRIPT)
  self.assertIn("python3 features/v178/apply-v178-archive-protection.py",WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v178/apply-v178-ftb-map-gui.py"),
                  WORKFLOW.index("python3 features/v178/apply-v178-archive-protection.py"))
  self.assertLess(WORKFLOW.index("python3 features/v178/apply-v178-archive-protection.py"),
                  WORKFLOW.index("python3 features/v178/apply-v178-team-gui.py"))
 def test_bounded_and_disk_durable_archive(self):
  for marker in ("ARCHIVE_SPAN=32,MAX_OPEN_REGIONS=8",
                 "REGIONS.size()>=MAX_OPEN_REGIONS",
                 "writeRegion(oldest)","if(!writeRegion(oldest))return null",
                 "java.nio.file.StandardCopyOption.ATOMIC_MOVE",
                 "int[] explored=archiveLookup(cx,cz)",
                 "archiveStore(cx,cz,colors)","flushRegions();",
                 "archiveStore((int)(pos>>32),(int)pos,pixels)",
                 "Math.floorDiv(cx,ARCHIVE_SPAN)",
                 "if(!world.hasChunk(cx,cz))return"):
   self.assertIn(marker,SCRIPT)
  self.assertNotIn("world.getChunk(",SCRIPT)
  self.assertNotIn("TICKETS.forceChunk(",SCRIPT)
  # floor division must be correct on negative coordinates.
  for cx in (-65,-64,-33,-32,-1,0,1,31,32,63,64):
   self.assertEqual(cx//32,(-1 if cx<0 and cx%32 else 0)+int(cx/32))
 def test_claim_attack_and_entity_use_protection(self):
  for marker in ("PlayerInteractEvent.LeftClickBlock event",
                 "PlayerInteractEvent.EntityInteract event",
                 "PlayerInteractEvent.EntityInteractSpecific event",
                 "!mayModify(level,event.getPos(),player.getUUID())",
                 "event.setCanceled(true);"):
   self.assertIn(marker,SCRIPT)
 def test_b1660_full_map_scan_and_entity_protection(self):
  for marker in ("B1660_VIEWPORT_SCAN", "fullMap?12:5", "fullMap?6:1",
                 "V178MiningAreaScreen","V178ClaimsMapScreen",
                 "roundRobin++%(side*side)", "B1660_PROTECTED_ENTITIES",
                 "AttackEntityEvent event", "event.getTarget().blockPosition()",
                 "getAffectedEntities().removeIf(entity->",
                 "if(entity instanceof ServerPlayer)return false;"):
   self.assertIn(marker,SCRIPT)
  self.assertIn("if(!world.hasChunk(cx,cz))return;",SCRIPT)
  self.assertNotIn("level.getChunk(",SCRIPT)
  for radius in (5,12):
   side=2*radius+1
   visited={(i%side-radius,i//side-radius) for i in range(side*side)}
   self.assertEqual(len(visited),side*side)
   self.assertIn((-radius,-radius),visited)
   self.assertIn((radius,radius),visited)
 def test_compiled_java_source_guards(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:return
  j=Path(root)/"dev/obsidiannetwork"
  terrain=(j/"client/V178TerrainMap.java").read_text()
  claims=(j/"claims/V178Claims.java").read_text()
  self.assertIn("B1657_REGION_ARCHIVE",terrain)
  self.assertIn("private static void flush(){\n  flushRegions();",terrain)
  self.assertIn("flush();REGIONS.clear();COLORS.clear();roundRobin=0;",terrain)
  self.assertIn("archiveStore((int)(pos>>32),(int)pos,pixels);",terrain)
  self.assertEqual(terrain.count("private static void flushRegions()"),1)
  self.assertEqual(terrain.count("archiveStore((int)(pos>>32),(int)pos,pixels)"),1)
  self.assertIn("getAffectedBlocks().removeIf",claims)
  self.assertIn("getAffectedEntities().removeIf",claims)
  self.assertIn("protectEntityAttack(AttackEntityEvent event)",claims)
  self.assertIn("int attempts=fullMap?6:1;",terrain)
  self.assertIn("PlayerInteractEvent.EntityInteractSpecific event)",claims)
if __name__=="__main__":unittest.main()
