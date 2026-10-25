#!/usr/bin/env python3
"""Regression: Network devices and remote antennas share strict NETWORK wiring."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"features/v173/apply-machine-network-bundle-compat.py").read_text()
BASE=(ROOT/"features/v173/apply-network-machines.py").read_text()
RELAY=(ROOT/"features/v173/apply-wireless-network-only.py").read_text()
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class NetworkDeviceBundleV173(unittest.TestCase):
 def test_python_patch_syntax(self):
  ast.parse(SCRIPT)
 def test_matches_exact_original_device_code(self):
  self.assertIn("if(!world.hasChunkAt(p)||!world.getBlockState(p).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;",BASE)
  self.assertIn("s.count(old) == 1",SCRIPT)
  self.assertIn('NetworkSignalRelayBridge.networkWire(world,p)',SCRIPT)
 def test_network_only_conduit_bundle_matches_signal_bridge(self):
  self.assertIn("ConduitBundleBlockEntity.Layer.NETWORK",RELAY)
  self.assertIn("ObsidianNetwork.CONDUIT_BUNDLE.get()",RELAY)
  self.assertIn("ObsidianNetwork.NETWORK_CABLE.get()",RELAY)
  self.assertNotIn("ConduitBundleBlockEntity.Layer.ENERGY",RELAY)
  self.assertIn('assert "ConduitBundleBlockEntity.Layer.ENERGY" not in b',SCRIPT)
 def test_ci_applies_after_all_network_related_features(self):
  anchor="python3 features/v173/apply-machine-network-bundle-compat.py"
  self.assertIn(anchor,WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v173/apply-wireless-network-only.py"),WORKFLOW.index(anchor))
  self.assertLess(WORKFLOW.index("python3 features/v173/apply-printer-blueprint-controls.py"),WORKFLOW.index(anchor))
  self.assertIn("V173_MACHINE_NETWORK_BUNDLE_PASS",WORKFLOW)

if __name__=="__main__": unittest.main()
