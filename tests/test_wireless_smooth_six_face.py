#!/usr/bin/env python3
"""Synthetic postpatch regression for six-face nodes and smooth FE charging."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / "features/wireless-energy/apply-wireless-smooth-six-face.py"


class SmoothSixFaceTest(unittest.TestCase):
    def test_generator_syntax_and_scope(self):
        source = PATCH.read_text(encoding="utf-8")
        ast.parse(source)
        for name in ("WirelessNetworkBlock.java", "WirelessNetworkBlockEntity.java",
                     "WirelessPlayerCharging.java", "network_transmitter", "network_receiver"):
            self.assertIn(name, source)
        self.assertNotIn("setChunkForced(", source)
        self.assertNotIn("getAllLevels()", source)
        self.assertNotIn("private source", source)

    def test_real_postpatch_anchors_generate_all_six_facing_and_smooth_transfer(self):
        with tempfile.TemporaryDirectory() as temp:
            source_root = Path(temp) / "java/dev/obsidiannetwork"
            assets = Path(temp) / "resources/assets/obsidiannetwork"
            files = {
                "block/WirelessNetworkBlock.java": "\n".join([
                    "import net.minecraft.world.level.block.HorizontalDirectionalBlock;",
                    "public static final Property<Direction> FACING=HorizontalDirectionalBlock.FACING;",
                    "registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));",
                    "return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());",
                ]),
                "blockentity/WirelessNetworkBlockEntity.java": "\n".join([
                    "private static final int MAX_TRANSFER=320000;",
                    "if(!(level instanceof ServerLevel server)||be.transmitter||server.getGameTime()%5!=0)return;",
                    "int remainingBudget=MAX_TRANSFER;",
                    "remainingSupply=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available(server.getServer(),be.networkId));",
                    "if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}",
                ]),
                "wireless/WirelessPlayerCharging.java": "\n".join([
                    "private static final int MAX_PER_PLAYER_TICK=16000;",
                    "if(!(event.getEntity() instanceof ServerPlayer player)||player.level().getGameTime()%20!=0)return;",
                    "var inventory=player.getInventory().getNonEquipmentItems();",
                    "WirelessCuriosCharging.charge(player,active,remaining);",
                ]),
            }
            for relative, text in files.items():
                file = source_root / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text, encoding="utf-8")
            for slug in ("network_transmitter", "network_receiver"):
                f = assets / "blockstates" / (slug + ".json")
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps({"variants": {
                    "facing=" + d: {"model": "obsidiannetwork:block/" + slug}
                    for d in ("north", "south", "east", "west")
                }}), encoding="utf-8")

            env = {**os.environ, "V1_SOURCE_ROOT": str(source_root.parent.parent),
                   "V1_RESOURCE_ROOT": str(assets.parent.parent)}
            def run():
                return subprocess.run([sys.executable, str(PATCH)], env=env,
                                      capture_output=True, text=True)

            result = run()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for marker in ("WIRELESS_SIX_FACE_V1 PASS", "WIRELESS_SMOOTH_64K_FE_PER_TICK_V1 PASS",
                           "WIRELESS_CHARGE_64K_FE_PER_PLAYER_TICK_V1 PASS"):
                self.assertIn(marker, result.stdout)
            block = (source_root / "block/WirelessNetworkBlock.java").read_text()
            self.assertIn("BlockStateProperties.FACING", block)
            self.assertIn("context.getClickedFace()", block)
            self.assertIn("Direction.UP", block)
            self.assertNotIn("HorizontalDirectionalBlock", block)
            for slug in ("network_transmitter", "network_receiver"):
                variants = json.loads((assets/"blockstates"/(slug+".json")).read_text())["variants"]
                self.assertEqual(set(variants), {
                    "facing=up", "facing=down", "facing=north", "facing=south",
                    "facing=east", "facing=west",
                })
                self.assertEqual(variants["facing=up"]["model"], "obsidiannetwork:block/" + slug)
                self.assertEqual(variants["facing=down"]["x"], 180)
                # User-tested #267: only north/south must invert; other faces stay exact.
                self.assertEqual(variants["facing=north"], {"model": "obsidiannetwork:block/" + slug, "x": 90})
                self.assertEqual(variants["facing=south"], {"model": "obsidiannetwork:block/" + slug, "x": 270})
                self.assertEqual(variants["facing=east"], {"model": "obsidiannetwork:block/" + slug, "x": 90, "y": 90})
                self.assertEqual(variants["facing=west"], {"model": "obsidiannetwork:block/" + slug, "x": 90, "y": 270})
                self.assertEqual(variants["facing=up"], {"model": "obsidiannetwork:block/" + slug})
            be = (source_root / "blockentity/WirelessNetworkBlockEntity.java").read_text()
            self.assertIn("int remainingBudget=Math.min(MAX_TRANSFER,64000);", be)
            self.assertNotIn("server.getGameTime()%5!=0", be)
            self.assertIn("if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}", be)
            player = (source_root / "wireless/WirelessPlayerCharging.java").read_text()
            self.assertIn("MAX_PER_PLAYER_TICK=64000", player)
            self.assertNotIn("player.level().getGameTime()%20!=0", player)
            self.assertIn("WirelessCuriosCharging.charge(player,active,remaining);", player)
            self.assertNotEqual(run().returncode, 0, "must reject duplicate application")


if __name__ == "__main__":
    unittest.main()
