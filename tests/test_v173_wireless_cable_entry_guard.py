#!/usr/bin/env python3
"""Regression: no wireless receiver access without a real NETWORK conductor."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "features/v173/apply-wireless-network-only.py").read_text()
PATCH = ROOT / "features/v173/apply-wireless-cable-entry-guard.py"
SCRIPT = PATCH.read_text()
WORKFLOW = (ROOT / ".github/workflows/networkstorage-v1.7-clean.yml").read_text()

def base_relay_java():
    tree = ast.parse(BASE)
    found = [
        call.args[1].value
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name) and call.func.id == "add"
        and len(call.args) == 2
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "network/NetworkSignalRelayBridge.java"
        and isinstance(call.args[1], ast.Constant)
    ]
    assert len(found) == 1, "must locate exactly one real generated Java source"
    return found[0]

class WirelessCableEntryV173(unittest.TestCase):
    def test_scripts_parse(self):
        ast.parse(BASE)
        ast.parse(SCRIPT)

    def test_actual_generated_java_is_patched(self):
        original = base_relay_java()
        self.assertIn("queue.add(queried);", original)
        with tempfile.TemporaryDirectory() as dirname:
            java = Path(dirname) / "dev/obsidiannetwork/network/NetworkSignalRelayBridge.java"
            java.parent.mkdir(parents=True)
            java.write_text(original)
            env = {**os.environ, "V1_SOURCE_ROOT": dirname}
            result = subprocess.run(
                [sys.executable, str(PATCH)], env=env,
                text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            changed = java.read_text()
            self.assertIn("V173_WIRELESS_CABLE_ENTRY_GUARD", changed)
            self.assertIn("if(networkWire(level,queried))queue.add(queried);", changed)
            self.assertIn("if(networkWire(level,first))queue.addLast(first);", changed)
            self.assertIn("if(queue.isEmpty())return null;", changed)
            self.assertNotIn("   queue.add(queried);", changed)
            self.assertIn("ConduitBundleBlockEntity.Layer.NETWORK", changed)
            self.assertNotIn("ConduitBundleBlockEntity.Layer.ENERGY", changed)
            self.assertIn("if(RESOLVING.get()||queried==null)return null;", changed)
            # Prevent silent double application on a changed source layout.
            duplicate = subprocess.run(
                [sys.executable, str(PATCH)], env=env,
                text=True, capture_output=True
            )
            self.assertNotEqual(duplicate.returncode, 0)

    def test_ci_wires_test_and_patch_before_java_compilation(self):
        test = "python3 -m unittest discover -s tests -p 'test_v173_wireless_cable_entry_guard.py' -v"
        apply = "python3 features/v173/apply-wireless-cable-entry-guard.py"
        self.assertIn(test, WORKFLOW)
        self.assertIn(apply, WORKFLOW)
        self.assertLess(WORKFLOW.index("python3 features/v173/apply-wireless-link-status.py"), WORKFLOW.index(apply))
        self.assertIn("V173_WIRELESS_CABLE_ENTRY_GUARD_PASS", WORKFLOW)

if __name__ == "__main__":
    unittest.main()
