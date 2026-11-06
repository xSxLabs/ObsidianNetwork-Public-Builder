"""B1225 guards for bidirectional live Backpack cables and spam-free GUI."""
import ast
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1225-backpack-chat.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
CABLE=ROOT/"features/v176/apply-v176-backpack-cables.py"
GUI=ROOT/"features/v176/apply-v176-backpack-magnet-gui-817.py"
CHAT=ROOT/"features/v176/apply-v176-b1189-chat-toggle.py"

class B1225BackpackChat(unittest.TestCase):
 def test_patch_compiles_and_pipeline_applies_last(self):
  source=PATCH.read_text(encoding="utf-8")
  ast.parse(source)
  workflow=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("test_v176_b1225_backpack_chat.py",workflow)
  self.assertIn("python3 features/v176/apply-v176-b1225-backpack-chat.py",workflow)
  self.assertLess(workflow.index("python3 features/v176/apply-v176-backpack-cables.py"),
                  workflow.index("python3 features/v176/apply-v176-b1225-backpack-chat.py"))
  self.assertLess(workflow.index("python3 features/v176/apply-v176-b1189-chat-toggle.py"),
                  workflow.index("python3 features/v176/apply-v176-b1225-backpack-chat.py"))
 def test_both_cable_directions_preserved_and_real_cells_only(self):
  s=PATCH.read_text()
  old=CABLE.read_text()
  self.assertIn("V176BackpackCells.extract(level,backpack,d,max)",old)
  self.assertIn("V176BackpackCells.insert(level,updated,item.toStack(),requested)",s)
  self.assertIn("cableJournal.updateSnapshots(tx)",s)
  self.assertIn("backpack=updated;",s)
  self.assertIn("if(accepted<=0)return 0;",s)
  self.assertIn("V176BackpackCells.capacity(backpack)",s)
  self.assertIn("V176BackpackCells.used(backpack)",s)
  self.assertIn("resource.getItem() instanceof NetworkBackpackItem",s)
  self.assertIn("resource.equals(",s)
  self.assertIn("list().size()+1",s)  # empty backpack still has a valid ingress index
  self.assertNotIn("private ItemStack additionalBackpackInventory",s)
 def test_gui_makes_fixed_inventory_packets_not_chat_commands(self):
  s=PATCH.read_text()
  self.assertIn("handleInventoryButtonClick(menu.containerId,action)",s)
  self.assertIn("clickMenuButton(Player player,int action)",s)
  self.assertIn("mouseScrolled(double mx,double my,double dx,double dy)",s)
  self.assertIn("wheelCooldown=5",s)
  self.assertIn("searchDelay=25",s)
  self.assertIn("String pendingSearch",s)
  self.assertIn("selectedCableFilter",s)
  self.assertIn("button(10+selectedFilter)",s)
  self.assertIn("button((button==1?146:101)+entry)",s)
  self.assertIn("button(4); // B1225_NO_CHAT_COMMAND_FOR_MAGNET",s)
  self.assertIn("button(5); // B1225_NO_CHAT_COMMAND_FOR_FILTER_MODE",s)
  # All actions are <=190 and therefore safe in byte-sized GUI button payloads.
  self.assertIn("action<191",s)
 def test_chat_control_retains_persistence_and_filters_only_mod_system_packets(self):
  s=PATCH.read_text()
  orig=CHAT.read_text()
  self.assertIn("xsxlabs-muted-chat-players.txt",orig)
  self.assertIn("ClientboundSystemChatPacket",orig)
  self.assertIn("ClientboundSetActionBarTextPacket",orig)
  self.assertIn('Commands.literal("modchat")',s)
  self.assertIn('message.startsWith("[xSxLabs]")',s)
  self.assertIn("WALKER.walk",s)
  self.assertIn("CONFIRMATION.get()",orig)
  self.assertNotIn("ClientboundPlayerChatPacket",s)

if __name__=="__main__": unittest.main()
