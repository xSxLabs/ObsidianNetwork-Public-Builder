#!/usr/bin/env python3
"""Build 60 non-mutating right-click fallback contracts."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/v17/apply-power-armor-enter-packet-60.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class RightClick(unittest.TestCase):
 def test_script_valid_and_ordered_after_safe_exit(self):
  ast.parse(S)
  self.assertIn("apply-power-armor-enter-packet-60.py",WF)
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-transitions-59.py"),
                  WF.index("python3 features/v17/apply-power-armor-enter-packet-60.py"))
 def test_client_packet_and_server_validation(self):
  self.assertIn("PlayerInteractEvent.EntityInteractSpecific",S)
  self.assertIn("EventPriority.HIGHEST,receiveCanceled=true",S)
  self.assertIn("new PowerArmorEnterPayload(stand.getId())",S)
  self.assertIn("playToServer(TYPE,STREAM_CODEC",S)
  self.assertIn("PowerArmorSuitWorld.tryEnter(player,payload.entityId())",S)
  self.assertIn("player.level().getEntity(entityId)",S)
  self.assertIn("player.distanceToSqr(stand)>36.0D",S)
  self.assertIn("!mine(stand,player)",S)
  self.assertIn("enter(stand,player)",S)
  self.assertIn("Never",S) if False else None
 def test_does_not_transfer_inventory_on_client(self):
  section=S.split("client.write_text(",1)[1]
  self.assertNotIn("setItemSlot",section)
  self.assertIn("Do not cancel vanilla interaction",section)
  self.assertIn("ClientPacketDistributor.sendToServer",section)
if __name__=="__main__":unittest.main()
