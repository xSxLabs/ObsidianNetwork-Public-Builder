#!/usr/bin/env python3
"""B975 Cell Terminal regression contracts: network safety, transfer, visuals."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"features/v176/apply-v176-b975-cell-terminal.py"

class CellTerminalContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=SOURCE.read_text(encoding="utf-8")

 def test_actual_16_slot_drives_not_synthetic_storage(self):
  s=self.source
  self.assertIn('change("menu/DriveMenu.java"',s)
  self.assertIn("return new DriveContainer(drive);",s)
  self.assertIn("for(int i=0;i<16;i++)",s)
  self.assertIn("new V176CellTerminalMenu(id,inv,terminal)",s)
  self.assertIn("backing.setItem(targetSlot,one);",s)
  self.assertNotIn("new StorageCellStore(",s)

 def test_item_conservation_and_full_network(self):
  s=self.source
  self.assertIn("if(destination==null)break;",s)
  self.assertIn("if(!ItemStack.matches(inserted,one)){",s)
  self.assertIn("backing.removeItemNoUpdate(targetSlot)",s)
  self.assertIn("if(transferred<=0)return ItemStack.EMPTY;",s)
  self.assertIn("carried.shrink(transferred);",s)
  self.assertLess(s.index("backing.setItem(targetSlot,one);"),s.index("carried.shrink(transferred);"))
  self.assertIn("clickedSlot<54",s)
  self.assertIn("if(slotId>=0&&slotId<54)return;",s)

 def test_network_is_loaded_only_and_identity_verified(self):
  s=self.source
  self.assertIn("private static final int MAX_CABLES=16_384;",s)
  self.assertIn("private static final int MAX_DRIVES=2048;",s)
  self.assertIn("world.hasChunkAt(at)",s)
  self.assertIn("WorldTopologyBridge.runtimeForAccessory(world,node)!=identity",s)
  self.assertIn("world.getBlockEntity(next) instanceof StorageDriveBlockEntity",s)
  self.assertIn("network!=null&&network.powered()",s)

 def test_balanced_shifting_and_no_inventory_loss(self):
  s=self.source
  self.assertIn(".comparingInt(StorageDriveBlockEntity::occupiedSlots)",s)
  self.assertIn("while(transferred<original.getCount())",s)
  self.assertIn("original.copyWithCount(1)",s)
  self.assertIn("if(drives.size()>=MAX_DRIVES)",s)

 def test_matching_look_no_occlusion(self):
  s=self.source
  self.assertIn(".noOcclusion()",s)
  self.assertIn('base=json.loads((A/"models/block/power_terminal.json")',s)
  self.assertIn("ImageDraw",s)
  self.assertIn("cell_terminal_front.png",s)
  self.assertIn("parent",s)
  self.assertIn('{"texture":"#"+face}',s)
  self.assertIn('assert \'"cullface"\' not in',s)
  self.assertIn("textures[\"north\"]=\"obsidiannetwork:block/cell_terminal_front\"",s)

 def test_gui_inventory_slots_unaffected(self):
  s=self.source
  self.assertIn("for(int i=0;i<54;i++)",s)
  self.assertIn("for(int i=0;i<36;i++)",s)
  self.assertIn("SH IFT-CLICK".replace(" ",""),s)
  self.assertIn("if(!chest.getTitle().getString().startsWith",s)

if __name__=="__main__":
 unittest.main()
