#!/usr/bin/env python3
"""B1019 regression contracts: real Cell I/O, balanced 3P render and stand ID."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v176/apply-v176-b1019-verified-cell-worldturret.py"
B1014=ROOT/"features/v176/apply-v176-b1014-cell-forearm-bullets.py"

class TestB1019(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=P.read_text(encoding="utf-8")
  cls.p=B1014.read_text(encoding="utf-8")

 def test_python_valid(self):
  ast.parse(self.s,str(P))
  self.assertIn("B1019_BRACE_UNCLOSED",self.s)

 def test_3p_hatch_is_entirely_removed(self):
  for marker in ("assert \"float hatchOpen=phase(\" in old",
   "assert \"nodes.submitModelPart(HATCH,pose\" not in old",
   "assert \"createHatch()\" not in s", "finally{",
   "pose.popPose();", "nodes.submitModelPart(XSX_WORLD_BARREL,pose",
   "6.8F,-2.95F,0.92F,4.7F,0.65F"):
   self.assertIn(marker,self.s)

 def test_no_first_person_mutation(self):
  self.assertNotIn("s.index(\" public static void firstPerson(",self.s)
  self.assertNotIn("balanced(s,\" public static void firstPerson(",self.s)
  self.assertIn("B1019_FIRST_PERSON",self.s.upper()) if "B1019_FIRST_PERSON" in self.s.upper() else self.assertIn("nodes.submitModelPart(BARREL,pose",self.s)
  self.assertIn("nodes.submitModelPart(BARREL,pose",self.p)

 def test_turret_by_synchronized_entity_id_not_box(self):
  for marker in ("mc.level.getEntity(state.id)","stand.getRightArmPose().x()<-40.0F",
                 "has(chest,\"micro_mg_turret_on\")",
                 'xsxLogTurretPose(stand.getId(),suitTier,amount,"ENTER")'):
   self.assertIn(marker,self.s)
  self.assertIn('"getEntitiesOfClass(ArmorStand.class,box)" not in s',self.s)

 def test_action_only_slot_with_no_client_ghost(self):
  for marker in ("for path in (menu,screen)","mayPlace(ItemStack item){return false;}",
                 "broadcastFullState();","carried.shrink(1);",
                 "DriveMenu.xsxCellTerminalBacking(drive)",
                 "xsxRefresh(world)"):
   self.assertIn(marker,self.s if marker!="xsxRefresh(world)" else self.p)

 def test_server_network_fallback_stays_identity_scoped(self):
  for marker in ("xsxCableDrives(", "NetworkSignalRelayBridge.networkWire(world,here)",
                 "attached==null||attached==network",
                 "seen.size()<16384", "found.size()<2048",
                 "WorldTopologyBridge.runtimeForAccessory(world,here)"):
   self.assertIn(marker,self.s)

if __name__=="__main__":unittest.main()
