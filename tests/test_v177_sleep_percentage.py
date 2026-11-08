#!/usr/bin/env python3
"""Power Armor sleeping respects vanilla Minecraft 26.1 gamerule semantics."""
from pathlib import Path
import unittest

PATCH=Path("features/v177/apply-v177-power-sleep-fix.py").read_text(encoding="utf-8")
FLOW=Path(".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

# Mirror the Java integer expression with a ceiling and minimum one.
def required_sleepers(eligible: int, percentage: int)->int:
    return max(1,(eligible*percentage+99)//100)

class PowerArmorSleepPercentage(unittest.TestCase):
    def test_percentage_zero_still_requires_one(self):
        self.assertEqual(required_sleepers(6,0),1)
    def test_one_percent_one_sleeper_up_to_100(self):
        for players in (1,2,5,8,50,100):
            self.assertEqual(required_sleepers(players,1),1)
    def test_one_percent_rounds_up_for_101_players(self):
        self.assertEqual(required_sleepers(101,1),2)
    def test_fifty_percent_ceil(self):
        self.assertEqual(required_sleepers(5,50),3)
    def test_100_percent_all_players(self):
        self.assertEqual(required_sleepers(8,100),8)
    def test_more_than_100_percent_impossible(self):
        self.assertGreater(required_sleepers(8,101),8)
    def test_armor_and_vanilla_beds_can_mix(self):
        # Three eligible: two bed sleepers plus one armor sleeper = 3.
        # When 50% is configured, two sleepers are enough.
        self.assertGreaterEqual(2,required_sleepers(3,50))
    def test_actual_java_source_uses_gamerule_and_counts_beds(self):
        for statement in (
            "net.minecraft.world.level.gamerules.GameRules;",
            "world.getGameRules().get(GameRules.PLAYERS_SLEEPING_PERCENTAGE)",
            "eligible*(long)percentage+99L",
            "Math.max(1L,",
            "if(!other.isAlive()||other.isSpectator())continue;",
            "if(other.isSleeping()||SLEEPING.containsKey(other))sleepers++;",
            "if(sleepers<needed)return;",
        ):
            self.assertIn(statement,PATCH)
        # The old all-players loop is retained as a literal replacement
        # anchor in the build patch, but not in its injected Java replacement.
        replacement=PATCH.split("int percentage=world.getGameRules()",1)[1]
        self.assertNotIn(
            "if(other.isAlive()&&!other.isSpectator()&&!SLEEPING.containsKey(other))",
            replacement)
    def test_build_pipeline_keeps_patch_on_v177_only(self):
        self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)
        self.assertIn("python3 features/v177/apply-v177-power-sleep-fix.py",FLOW)

if __name__=="__main__":
    unittest.main()
