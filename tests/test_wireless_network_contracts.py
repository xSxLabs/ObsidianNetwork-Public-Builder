#!/usr/bin/env python3
"""Source-regression contracts for the wireless FE core and five category GUI.

Compilation, actual FE/GameTests and dedicated-server runs remain mandatory.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"features/wireless-energy"
CORE=(ROOT/"apply-wireless-runtime.py").read_text()
UI=(ROOT/"apply-wireless-ui-charging.py").read_text()

class WirelessNetworkContractTests(unittest.TestCase):
 def test_only_two_new_block_ids_and_registry_handlers(self):
  self.assertIn('"network_transmitter"',CORE)
  self.assertIn('"network_receiver"',CORE)
  self.assertIn('NETWORK_TRANSMITTER_ITEM = ITEMS.registerSimpleBlockItem',CORE)
  self.assertIn('NETWORK_RECEIVER_ITEM = ITEMS.registerSimpleBlockItem',CORE)
  self.assertIn('ModBlockEntities.NETWORK_TRANSMITTER.get()',CORE)
  self.assertIn('ModBlockEntities.NETWORK_RECEIVER.get()',CORE)
  self.assertNotIn('WIRELESS_NETWORK_CONTROLLER = BLOCKS',CORE)
 def test_network_saveddata_and_owner_checks(self):
  for needle in ('SavedDataType<WirelessNetworkData>', 'server.getDataStorage().computeIfAbsent(TYPE)',
       'public Entry create(ServerPlayer p,String name)', 'p.getUUID().toString()',
       'public boolean canAccess(ServerPlayer p,String id)', 'setCharging(ServerPlayer p,String id,int mask)',
       'setDirty();', 'INVENTORY=1, CURIOS=2, ARMOR=4, OFFHAND=8, HOTBAR=16'):
   self.assertIn(needle,CORE)
 def test_transactional_energy_prevents_duplicate_and_remote_load(self):
  for needle in ('WeakReference<WirelessNetworkBlockEntity>','TransactionContext tx',
      'private final Journal journal=new Journal()', 'journal.updateSnapshots(tx)',
      'protected void revertToSnapshot(Long before)', 'if(accepted==withdrawn)tx.commit();',
      'server.hasChunkAt(neighbor)', 'level.getCapability(Capabilities.Energy.BLOCK,neighbor',
      'if(wanted<=0||IN_TRANSFER.get()', 'if(transmitter)WirelessEnergyRuntime.unregister(this)',
      'server.getGameTime()%5!=0'):
   self.assertIn(needle,CORE)
  for forbidden in ('forceChunk(', 'getServer().getAllLevels()', 'getChunkSource().getChunk('):
   self.assertNotIn(forbidden,CORE)
 def test_gui_is_server_authoritative_and_named_networks_exist(self):
  for needle in ('clickMenuButton(Player player,int button)', 'if(!(player instanceof ServerPlayer p)||device==null||!stillValid(player))return false;',
       'storage.create(p,"Network "', 'storage.setCharging(p,current.id(),current.chargingMask()^bit)',
       'Commands.literal("wirelessnet")', 'StringArgumentType.greedyString()',
       'WirelessNetworkMenu', 'WirelessNetworkScreen'):
   self.assertIn(needle,UI)
 def test_charging_categories_are_independently_bounded_and_curios_optional(self):
  for needle in ('MAX_PER_PLAYER_TICK=16000','getGameTime()%20!=0',
       'WirelessNetworkData.HOTBAR', 'WirelessNetworkData.INVENTORY',
       'WirelessNetworkData.ARMOR', 'WirelessNetworkData.OFFHAND',
       'WirelessNetworkData.CURIOS', 'ModList.get().isLoaded("curios")',
       'CuriosApi.getCuriosInventory(player)', 'stack.getCapability(Capabilities.Energy.ITEM)',
       'WirelessEnergyRuntime.pull(player.level().getServer(),network,requested,tx)',
       'if(drawn>0&&drawn==received){tx.commit();return received;}'):
   self.assertIn(needle,UI)

if __name__=="__main__":unittest.main()
