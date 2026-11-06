"""B1234 v1.7.6 Backpack cable MSPT, scroll, magnet + no-spam checks."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FEATURE=ROOT/"features/v176"
PERF=FEATURE/"apply-v176-b1234-backpack-cable-perf.py"
SCROLL=FEATURE/"apply-v176-b1234-backpack-scroll.py"
MAGNET=FEATURE/"apply-v176-b1234-magnet-fix.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class PerformanceAndSafetyB1234(unittest.TestCase):
 def test_scripts_parse_and_reconstruct_fail_closed(self):
  for f in (PERF,SCROLL,MAGNET):
   with self.subTest(f=f.name):
    ast.parse(f.read_text("utf-8"))
    self.assertIn("DRIFT",f.read_text("utf-8"))

 def test_order_and_no_freeze_mutation(self):
  w=WORKFLOW.read_text("utf-8")
  scripts=[
   "apply-v176-b1230-backpack-live-gui.py",
   "apply-v176-b1234-backpack-cable-perf.py",
   "apply-v176-b1234-backpack-scroll.py",
   "apply-v176-b1234-magnet-fix.py"
  ]
  for f in scripts:self.assertIn("python3 features/v176/"+f,w)
  self.assertEqual([w.index(f) for f in scripts],sorted(w.index(f) for f in scripts))
  self.assertIn("test_v176_b1234_backpack_performance_scroll_magnet.py",w)
  self.assertNotIn("features/v175/",PERF.read_text()+SCROLL.read_text()+MAGNET.read_text())

 def test_cable_real_cells_and_rollback(self):
  s=PERF.read_text("utf-8")
  for token in (
    "xsxCableCacheStack==backpack",
    "xsxCableCacheContainer==container",
    "xsxCableCacheRevision==xsxCableCommitRevision",
    "xsxCableResources.get(i)",
    "xsxCableCapacity",
    "xsxCableUsed",
    "cableJournal.updateSnapshots(tx)",
    "backpack=before.copy()",
    "cacheContainer==content",
    "cacheCableRevision==liveCableRevision",
    "V176BackpackCells.entries(backpack)",
   ):
   with self.subTest(token=token):self.assertIn(token,s)
  self.assertIn("xsxCableResources=java.util.List.copyOf(resources)",s)

 def test_scroll_no_chat_commands_or_tick_delays(self):
  s=SCROLL.read_text("utf-8")
  for token in (
   "xsxWheelAccumulator",
   "xsxDraggingScrollbar",
   "xsxFlushScroll(false)",
   "xsxLastScrollPacketTick",
   "xsxPendingScroll",
   "action>=192&&action<=32959",
   "page(server,(action-192)-storage.page)",
   "mouseDragged(\n   net.minecraft.client.input.MouseButtonEvent",
   "mouseReleased(net.minecraft.client.input.MouseButtonEvent",
  ):self.assertIn(token,s)
  self.assertNotIn("wheelCooldown=5",s)
  self.assertNotIn("command(delta>0?",s)
  self.assertNotIn("for(int i=0;i<5;i++)",s)

 def test_drag_handlers_keep_existing_shift_drag_no_duplicates(self):
  # B1244 failed Java compilation: B1234 added a second mouseDragged and
  # mouseReleased. B1245 must merge scrollbar logic into B957's existing
  # Shift+drag withdraw handler, never replace or duplicate its behavior.
  tree=ast.parse(SCROLL.read_text("utf-8"))
  strings={}
  for node in tree.body:
   if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
    for target in node.targets:
     if isinstance(target,ast.Name):strings[target.id]=node.value.value
  self.assertEqual(strings["wheel"].count("mouseDragged("),0)
  self.assertEqual(strings["wheel"].count("mouseReleased("),0)
  self.assertIn("mouseScrolled(",strings["wheel"])
  self.assertIn("xsxShiftVisited",SCROLL.read_text("utf-8"))
  self.assertIn("B1245_DUPLICATE_DRAG",SCROLL.read_text("utf-8"))
  self.assertIn("B1245_DUPLICATE_RELEASE",SCROLL.read_text("utf-8"))
  self.assertIn("event.hasShiftDown()&&!filterEditor",SCROLL.read_text("utf-8"))
  self.assertIn("xsxDraggingScrollbar&&event.button()==0",SCROLL.read_text("utf-8"))

 def test_magnet_lossless_and_nonblocking_optional_curios(self):
  s=MAGNET.read_text("utf-8")
  for token in (
   "firstEnabledMagnet",
   "activeMagnet(ServerPlayer player)",
   "V176BackpackEquipped.activeMagnet(player)",
   "magnetData(magnet).getBooleanOr(MAG_ON,true)",
   "V176BackpackCells.capacity(original)<=0L",
   'ModList.get().isLoaded("curios")',
   "location.persist(player,updated);",
   "remainder.shrink(",
   "RANGE=12.0D",
  ):self.assertIn(token,s)
  self.assertNotIn("player.setItemInHand",s)

 def test_unaffected_subsystems_by_scope(self):
  for f in (PERF,SCROLL,MAGNET):
   source=f.read_text("utf-8")
   for key in ("PowerArmorEntrySequence655","PowerArmorExitSequence650",
     "MicroMg", "ReactorPower", "NetworkDriveBlockEntity",
     "StorageTerminalMenu.java"):
    self.assertNotIn(key,source)

if __name__=="__main__":
 unittest.main()
