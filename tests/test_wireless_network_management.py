#!/usr/bin/env python3
"""Fail-closed network-management regression contracts for code generation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"features/wireless-energy"
PATCH=(ROOT/"apply-wireless-network-management.py").read_text()
CORE=(ROOT/"apply-wireless-runtime.py").read_text()

class NamedNetworkManagementContracts(unittest.TestCase):
 def test_owner_and_main_immutability(self):
  for marker in (
   'DEFAULT_ID.equals(id)', 'old.owner().equals(player.getUUID().toString())',
   'old.name().equals(name)', 'networks.put(id,new Entry(id,name,old.owner(),old.chargingMask()))',
   'networks.remove(id);setDirty();return true;',
   'old.owner().equals(player.getUUID().toString())',
   '&&e.name().equalsIgnoreCase(name)',
  ):self.assertIn(marker,PATCH)
 def test_server_validated_chat_commands_and_stable_ids(self):
  for marker in ('Commands.literal("rename")','Commands.literal("delete")',
     'StringArgumentType.greedyString()', '.rename(player,id,name)',
     '.delete(player,id)', 'WirelessNetworkData.Entry created=null',
     'ids.add(buf.readUtf(80))', 'b.writeUtf(network.id(),80)',
     'new net.minecraft.client.gui.components.EditBox',
     'Commands.literal("rename")','sendNamed("rename")',
     'sendNamed("delete")','sendNamed("create")',
     'minecraft.getConnection().sendCommand(command)',
     'id.equals(deletionConfirmation)',
     'deletionConfirmation=id;return;',
     'deletionConfirmation="";',
     'Click Delete again to confirm'):
   self.assertIn(marker,PATCH)
 def test_deletion_is_fail_closed_without_losing_block_buffer(self):
  self.assertIn('WirelessNetworkData.get(server).find(id)==null',CORE)
  self.assertIn('WirelessNetworkData.get(server.getServer()).find(be.networkId)==null',CORE)
  self.assertIn('out.putLong("wireless_fe",stored)',CORE)
  self.assertNotIn('stored=0',PATCH)
 def test_persisted_masks_are_bounded(self):
  self.assertIn('e.chargingMask()&~ALL_CATEGORIES',PATCH)

if __name__=="__main__":unittest.main()
