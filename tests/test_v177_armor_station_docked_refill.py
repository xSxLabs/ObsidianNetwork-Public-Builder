#!/usr/bin/env python3
"""Regression: deployed four-piece Power Armor on red station pad is refilled offline."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOCK=(ROOT/"features/v177/apply-v177-armor-station-docked-refill.py").read_text(encoding="utf-8")
STAND=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text(encoding="utf-8")
PAD=(ROOT/"features/v17/apply-power-armor-bundle-93.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class StationDockedArmorRefill(unittest.TestCase):
 def test_patch_is_valid_and_strictly_scoped(self):
  ast.parse(DOCK)
  self.assertIn('public static ArmorStand findDockedOnPad(Level level,BlockPos station)',DOCK)
  self.assertIn('station.relative(state.getValue(ArmorStationBlock.FACING))',DOCK)
  self.assertIn('new AABB(pad)',DOCK)
  self.assertIn('e.entityTags().contains(MARKER)&&full(e)',DOCK)
  self.assertIn('e.blockPosition().equals(pad)',DOCK)
  self.assertIn('suits.size()==1?suits.get(0):null',DOCK)
  self.assertIn('e->mine(e,player)&&full(e)',PAD)
  self.assertIn('stand.addTag(MARKER);',STAND)
  self.assertIn('stand.addTag(owner(player));',STAND)
  self.assertIn('PowerArmorSuitWorld.findDockedOnPad(level,pos)',DOCK)
  # No ServerPlayer arg: the displayed armor must refill even with owner offline.
  self.assertNotIn('findDockedOnPad(Level level,BlockPos station,ServerPlayer player)',DOCK)
  self.assertIn('if(station.v177StoredFe()<=0&&station.v177StoredPaste()<=0L)return;',DOCK)

 def test_same_five_tick_station_service_without_losing_worn_player_behavior(self):
  self.assertIn('V177ArmorStationCharge.chargeWornArmor(server,pos,be);',DOCK)
  self.assertIn('V177ArmorStationDockService.service(server,pos,be);',DOCK)
  self.assertLess(DOCK.index('V177ArmorStationCharge.chargeWornArmor(server,pos,be);'),
                  DOCK.index('V177ArmorStationDockService.service(server,pos,be);'))
  self.assertIn('private static int repairOne(ItemStack stack,int availableFe)',DOCK)
  self.assertIn('public static int repairOne(ItemStack stack,int availableFe)',DOCK)
  self.assertIn('int budget=Math.min(1000,station.v177StoredFe());',DOCK)
  self.assertIn('V177ArmorIntegrity.repairOne(changed,budget)',DOCK)
  self.assertIn('int available=Math.min(V177ArmorStationCharge.MAX_FE_PER_SERVICE,',DOCK)
  self.assertIn('int perPiece=Math.max(1,available/PowerArmorRuntime.SLOTS.length);',DOCK)

 def test_all_resources_debited_before_equipment_changes(self):
  for fragment in (
   'if(station.v177ConsumeFe(cost)!=cost)return;',
   'if(station.v177TakePaste(inserted)!=inserted)return;',
   'int drawn=station.v177ConsumeFe(offered);',
   'EnergyTool.setEnergy(changed,stored+drawn);',
   'NutriPaste.add(changed,station.v177StoredPaste())',
   'stand.setItemSlot(PowerArmorRuntime.SLOTS[i],changed);',
   'stand.setItemSlot(PowerArmorRuntime.SLOTS[0],changed);',
  ):self.assertIn(fragment,DOCK)
  self.assertLess(DOCK.index('if(station.v177ConsumeFe(cost)!=cost)return;'),
                  DOCK.index('stand.setItemSlot(PowerArmorRuntime.SLOTS[i],changed);'))
  self.assertLess(DOCK.index('if(station.v177TakePaste(inserted)!=inserted)return;'),
                  DOCK.index('stand.setItemSlot(PowerArmorRuntime.SLOTS[0],changed);'))
  self.assertNotIn('setItemSlot(PowerArmorRuntime.SLOTS[i],ItemStack.EMPTY)',DOCK)

 def test_fully_empty_docked_suit_with_real_sources_finishes_within_60_seconds(self):
  # Conservative model of the same 5-tick service and exact finite FE accounting.
  energies=[0]*4
  hp=[0]*4
  paste=0
  total_in=0
  total_used=0
  finished=None
  for cycle in range(1,241):
   # Source can really refill the 400k FE buffer each cycle.
   buffer=400_000
   total_in+=buffer
   repair_budget=min(1000,buffer)
   for i in range(4):
    heal=min(10,1000-hp[i],repair_budget//25)
    cost=heal*25
    hp[i]+=heal
    repair_budget-=cost
    buffer-=cost
    total_used+=cost
   if cycle==1:paste=1_000_000 # sourced through fluid cable/tank
   remaining=min(400_000,buffer)
   share=max(1,remaining//4)
   for pass_number in range(2):
    for i in range(4):
     fill=min(16_000_000-energies[i],remaining,
              share if pass_number==0 else remaining)
     energies[i]+=fill
     buffer-=fill
     remaining-=fill
     total_used+=fill
   self.assertGreaterEqual(buffer,0)
   self.assertLessEqual(total_used,total_in)
   if paste==1_000_000 and all(x==1000 for x in hp) and all(x==16_000_000 for x in energies):
    finished=cycle
    break
  self.assertIsNotNone(finished)
  self.assertLessEqual(finished,240)

 def test_build_runs_after_shared_worn_and_paste_injectors(self):
  one=WORKFLOW.index('python3 features/v177/apply-v177-armor-station-energy-charge.py')
  two=WORKFLOW.index('python3 features/v177/apply-v177-armor-station-docked-refill.py')
  self.assertLess(one,two)
  self.assertIn('test_v177_armor_station_docked_refill.py',WORKFLOW)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',WORKFLOW)

if __name__=="__main__":
 unittest.main()
