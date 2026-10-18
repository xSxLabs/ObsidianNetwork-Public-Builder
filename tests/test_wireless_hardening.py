#!/usr/bin/env python3
"""Regression contracts for owner-bound wireless controls and fair FE limits.

Full reconstructed-source compilation and live FE conservation tests also run in CI.
"""
from pathlib import Path
import unittest

PATCH=(Path(__file__).resolve().parents[1]/
       "features/wireless-energy/apply-wireless-hardening.py").read_text()

class WirelessHardeningTests(unittest.TestCase):
    def test_private_antenna_settings_are_owner_bound(self):
        for needle in (
            "wireless_owner",
            "ownerId.equals(player.getUUID().toString())",
            "markPlacedBy(sp)",
            "!device.canConfigure(ownerPlayer)",
            "!device.canConfigure(p)",
            "WirelessNetworkData.get(player.level().getServer()).canAccess(player,id)",
            "device.selectNetworkFor(p,",
        ):
            self.assertIn(needle,PATCH,needle)

    def test_receiver_has_one_budget_across_all_sides(self):
        self.assertIn("int remainingBudget=MAX_TRANSFER;",PATCH)
        self.assertIn("if(remainingBudget<=0)break;",PATCH)
        self.assertIn("Math.min(remainingBudget,WirelessEnergyRuntime.available",PATCH)
        self.assertIn("if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;}",PATCH)

    def test_sender_fairness_preserves_transactions_and_loaded_only_index(self):
        self.assertIn("NEXT_SENDER",PATCH)
        self.assertIn("Math.floorMod(cursors.getOrDefault(id,0),size)",PATCH)
        self.assertIn("group.get((start+offset)%size).get()",PATCH)
        self.assertIn("be.withdraw(remaining,tx)",PATCH)
        self.assertIn("cursors.put(id,(start+1)%size)",PATCH)
        self.assertNotIn("forceChunk(",PATCH)
        self.assertNotIn("getChunkSource().getChunk(",PATCH)

    def test_patch_fails_closed_on_source_drift(self):
        self.assertIn("source.count(before)==1",PATCH)
        self.assertNotIn("except Exception",PATCH)

if __name__=="__main__":
    unittest.main()
