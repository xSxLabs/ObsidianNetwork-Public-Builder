#!/usr/bin/env python3
"""B633 source + generated-code checks; no Gradle or game startup required."""
import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "features/v175/apply-v175-exit-back-to-player-633.py"
WORKFLOW = ROOT / ".github/workflows/networkstorage-v1.7-clean.yml"
class ExitBackToPlayer633(unittest.TestCase):
    def test_python_parses_and_is_v175_only(self):
        source = PATCH.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("V175_B633_EXIT_BACK_TO_PLAYER", source)
        self.assertIn("player.getDirection().getOpposite().toYRot()", source)
        self.assertIn("player.getDirection().toYRot()", source)
        self.assertNotIn("PowerArmorRecall.java", source)
    def test_workflow_runs_after_legacy_yaw_and_preserves_buildlock(self):
        wf = WORKFLOW.read_text(encoding="utf-8")
        self.assertLess(wf.index("apply-power-armor-exit-facing-117.py"),
                        wf.index("apply-v175-exit-back-to-player-633.py"))
        self.assertLess(wf.index("apply-v175-worn-shell-geometry-632.py"),
                        wf.index("apply-v175-exit-back-to-player-633.py"))
        self.assertLess(wf.index("apply-v175-exit-back-to-player-633.py"),
                        wf.index("apply-v175-uranium-enchant-veinminer.py"))
        push_branches = next(line for line in wf.splitlines() if "branches: [" in line)
        self.assertNotIn("v1.7.5", push_branches,
                         "B633 MUST NOT trigger a build without the user's build command")
        self.assertIn("workflow_dispatch:", wf)
    def test_patch_only_yaw_and_keeps_front_placement(self):
        # Minimal generated Java fixture: match B117 source, and include
        # transaction safety anchors that may never be removed.
        fixture = (
            "class PowerArmorSuitWorld {\n"
            " // BUILD117_EXIT_FRONT_FACING\n"
            " BlockPos p=player.blockPosition().relative(player.getDirection());\n"
            " if(!clearSuitVolume(level,pos))return null;\n"
            " ArmorStand stand=spawn(player,worn);\n"
            " for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){}\n"
            " stand.discard();\n"
            "   // BUILD117_STAND_LOOKS_AT_OWNER: opposite horizontal look, all 4 facings.\n"
            "   float faceOwner=player.getDirection().getOpposite().toYRot();\n"
            "   stand.setYRot(faceOwner);\n"
            "   stand.setYBodyRot(faceOwner);\n"
            "   stand.setYHeadRot(faceOwner);\n"
            "}\n"
        )
        with tempfile.TemporaryDirectory() as d:
            j = Path(d) / "dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java"
            j.parent.mkdir(parents=True)
            j.write_text(fixture, encoding="utf-8")
            result = subprocess.run([sys.executable, str(PATCH)],
                env={**os.environ, "V1_SOURCE_ROOT": d},
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = j.read_text(encoding="utf-8")
            self.assertIn("BlockPos p=player.blockPosition().relative(player.getDirection());", after)
            self.assertIn("if(!clearSuitVolume(level,pos))return null;", after)
            self.assertIn("ArmorStand stand=spawn(player,worn);", after)
            self.assertIn("for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)", after)
            self.assertIn("stand.discard();", after)
            self.assertNotIn("getOpposite().toYRot()", after)
            for yaw in ("setYRot", "setYBodyRot", "setYHeadRot"):
                self.assertIn("stand." + yaw + "(faceAway);", after)
            # Fail closed: a second pass cannot silently corrupt fresh sources.
            repeated = subprocess.run([sys.executable, str(PATCH)],
                env={**os.environ, "V1_SOURCE_ROOT": d},
                capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
    def test_generated_world_when_present(self):
        if os.environ.get("V175_B633_VERIFY_GENERATED") != "1":
            return
        java = (Path(os.environ["V1_SOURCE_ROOT"]) /
                "dev/obsidiannetwork/powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
        self.assertIn("V175_B633_EXIT_BACK_TO_PLAYER", java)
        self.assertEqual(java.count("player.getDirection().toYRot()"), 1)
        self.assertNotIn("player.getDirection().getOpposite().toYRot()", java)
        self.assertIn("BlockPos p=player.blockPosition().relative(player.getDirection());", java)
        for yaw in ("setYRot", "setYBodyRot", "setYHeadRot"):
            self.assertIn("stand." + yaw + "(faceAway);", java)

if __name__ == "__main__":
    unittest.main()
