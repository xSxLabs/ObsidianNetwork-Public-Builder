#!/usr/bin/env python3
"""v1.7.2: owner-only original-source recall across dimensions."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v172/apply-power-armor-recall.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class PowerArmorRecall172(unittest.TestCase):
 def test_syntax(self):ast.parse(PATCH)
 def test_any_distance_and_dimensions(self):
  for m in ("V172_UNLIMITED_CROSS_DIM_RECALL","V172_DURABLE_SUIT_INDEX",
   "PowerArmorRecallTickets.ticket(world,player.getUUID()",
   "ServerStartedEvent","isVisualActive(getUUID())",
   "PlayerTickEvent.Post","RegisterTicketControllersEvent",
   "PowerArmorSuitWorld.recallEquip(stand,player)",
   "locate(player,visual)","V172_TRUE_16_BLOCK_LIMIT",
   "noCollision(visual,visual.getBoundingBox().move(move))",
   "finishEntering(stand,player)"):
   self.assertIn(m,PATCH,m)
  recall=PATCH.split("core=r'''",1)[1].split("'''.replace(",1)[0]
  self.assertNotIn("MAX_RANGE",recall)
 def test_safe_ownership_and_single_source(self):
  for s in ("stand.entityTags().contains(OWNER+owner)",
   "PowerArmorSuitWorld.full(stand)","matches.size()!=1",
   "ArmorLoadoutData.get(player.level().getServer()).has(player)",
   "PowerArmorRecallIndex.get(player.level().getServer()).remove(stand.getUUID())"):
   self.assertIn(s,PATCH,s)
  recall=PATCH.split("core=r'''",1)[1].split("'''.replace(",1)[0]
  self.assertNotIn("setItemSlot(",recall)
  self.assertNotIn("addFreshEntity(stand)",recall)
 def test_normal_entry_does_not_leave_stale_index(self):
  # A normal (non-recall) interaction discards a complete suit.
  # Destroyed stands must be unindexed; chunk-unloaded stands kept.
  self.assertIn("V172_STALE_INDEX_GUARD",PATCH)
  self.assertIn("reason.shouldDestroy()",PATCH)
  self.assertNotIn("stand.entityTags().contains(MARKER)&&!PowerArmorSuitWorld.full(stand)",PATCH)
  self.assertIn("stand.getRemovalReason()",PATCH)
 def test_strict_16_block_3d_teleport(self):
  self.assertIn("double radius=Math.sqrt(256D-(double)height*height)-0.25D;",PATCH)
  self.assertIn("dest.distanceToSqr(p.position())>256D",PATCH)
  self.assertNotIn("dir.scale(16D)",PATCH)
 def test_restart_and_portal_cleanup(self):
  self.assertIn("V172_SERVER_RESTART_GUARD",PATCH)
  self.assertIn("ACTIVE.clear();",PATCH)
  self.assertIn("V172_DIMENSION_CLEANUP",PATCH)
  self.assertIn("for(ServerLevel dimension:player.level().getServer().getAllLevels())",PATCH)
  self.assertIn("dimension.getEntity(flight.visual())",PATCH)
 def test_branch_pipeline(self):
  self.assertIn("branches: [v1.7, v1.7.2]",WF)
  self.assertLess(WF.index("apply-power-armor-subtle-shield-125.py"),WF.index("apply-power-armor-recall.py"))
  self.assertIn("V172_UNLIMITED_CROSS_DIM_RECALL PASS",WF)
if __name__=="__main__":unittest.main()
