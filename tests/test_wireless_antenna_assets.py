#!/usr/bin/env python3
"""Regression tests for antenna-based wireless transmitter/receiver assets."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH=Path(__file__).resolve().parents[1]/"features/wireless-energy/apply-antenna-assets.py"

class AntennaAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"assets/obsidiannetwork"
        for name in ("models/block","models/item","textures/block","items","blockstates","lang"):
            (self.root/name).mkdir(parents=True,exist_ok=True)
        self.model={"textures":{"base":"obsidiannetwork:block/wireless_antenna",
                                "particle":"obsidiannetwork:block/wireless_antenna"},
                    "elements":[{"from":[2,0,2],"to":[14,3,14]} for _ in range(4)]}
        (self.root/"models/block/wireless_antenna.json").write_text(json.dumps(self.model))
        (self.root/"textures/block/wireless_antenna.png").write_bytes(b"original-texture")
        (self.root/"lang/en_us.json").write_text('{"block.obsidiannetwork.wireless_antenna":"Wireless Antenna"}')

    def run_patch(self):
        return subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
               env=dict(os.environ,V1_RESOURCE_ROOT=str(self.root.parent.parent)))

    def test_antenna_body_and_two_distinct_signal_sprites(self):
        result=self.run_patch()
        self.assertEqual(result.returncode,0,result.stderr)
        for slug in ("network_transmitter","network_receiver"):
            model=json.loads((self.root/f"models/block/{slug}.json").read_text())
            self.assertEqual(model["elements"][:4],self.model["elements"])
            self.assertEqual(len(model["elements"]),7)
            states=json.loads((self.root/f"blockstates/{slug}.json").read_text())
            self.assertEqual(set(states["variants"]),{"facing=north","facing=east","facing=south","facing=west"})
            sprite=(self.root/f"textures/block/{slug}_signal.png").read_bytes()
            self.assertTrue(sprite.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(model["textures"]["signal"],f"obsidiannetwork:block/{slug}_signal")
            item=json.loads((self.root/f"items/{slug}.json").read_text())
            self.assertEqual(item["model"]["model"],f"obsidiannetwork:item/{slug}")
        self.assertNotEqual(
            (self.root/"textures/block/network_transmitter_signal.png").read_bytes(),
            (self.root/"textures/block/network_receiver_signal.png").read_bytes())
        self.assertEqual((self.root/"textures/block/wireless_antenna.png").read_bytes(),b"original-texture")

    def test_unknown_original_model_fails_before_mutation(self):
        self.model["elements"].pop()
        p=self.root/"models/block/wireless_antenna.json"
        p.write_text(json.dumps(self.model))
        result=self.run_patch()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.root/"models/block/network_transmitter.json").exists())

if __name__=="__main__":
    unittest.main()
