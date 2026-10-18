#!/usr/bin/env python3
"""Fail-closed tests for Flux-Point-style wireless blocks, throughput, roster GUI."""
from pathlib import Path
import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
GUI=ROOT/"features/wireless-energy/apply-wireless-point-gui-rate.py"
ASSET=ROOT/"features/wireless-energy/apply-wireless-point-assets.py"

class WirelessPointRefreshTest(unittest.TestCase):
    def test_scripts_are_valid_python(self):
        for file in (GUI,ASSET):
            ast.parse(file.read_text(encoding="utf-8"),filename=str(file))

    def test_bounded_rate_and_authoritative_roster(self):
        src=GUI.read_text(encoding="utf-8")
        for marker in (
            "WIRELESS_HIGH_THROUGHPUT_V2",
            "MAX_TRANSFER=320000",
            "MAX_TRANSFER=16000;",
            "WIRELESS_VISIBLE_ROSTER_V2",
            "button>=32&&button<160",
            "device.selectNetworkFor(p,current.get(choice).id())",
            "ids.get(choice).equals(current.get(choice).id())",
            "names.get(choice).equals(current.get(choice).name())",
            "if(choice>=ids.size()||choice>=current.size())return false;",
            "rosterPage*8+slot",
            "refreshRoster()",
            "Max transfer: 64,000 FE/t",
        ):
            self.assertIn(marker,src)
        self.assertNotIn("world.setChunkForced(",src)
        self.assertNotIn("WirelessEnergyRuntime.register(",src)

    def test_original_point_assets_compile_and_keep_four_direction_states(self):
        src=ASSET.read_text()
        self.assertIn("WIRELESS_POINT_STYLE_V2",src)
        self.assertIn("network_transmitter",src)
        self.assertIn("network_receiver",src)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"assets/obsidiannetwork"
            for slug in ("network_transmitter","network_receiver"):
                for sub in ("models/block","models/item","blockstates"):
                    (root/sub).mkdir(parents=True,exist_ok=True)
                (root/"models/block"/(slug+".json")).write_text("{}")
                (root/"models/item"/(slug+".json")).write_text(
                    json.dumps({"parent":"obsidiannetwork:block/"+slug}))
                (root/"blockstates"/(slug+".json")).write_text(json.dumps({
                    "variants": {direction:{} for direction in
                      ("facing=north","facing=south","facing=east","facing=west")}}))
            env={**os.environ,"V1_RESOURCE_ROOT":d}
            run=subprocess.run([sys.executable,str(ASSET)],env=env,
                               capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            for slug in ("network_transmitter","network_receiver"):
                model=json.loads((root/"models/block"/(slug+".json")).read_text())
                self.assertGreaterEqual(len(model["elements"]),9)
                self.assertIn("core",model["textures"])
                for surface in ("case","trim","core"):
                    path=root/"textures/block"/(slug+"_"+surface+".png")
                    raw=path.read_bytes()
                    self.assertEqual(raw[:8],b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(int.from_bytes(raw[16:20],"big"),16)
                    self.assertEqual(int.from_bytes(raw[20:24],"big"),16)

if __name__=="__main__":
    unittest.main()
