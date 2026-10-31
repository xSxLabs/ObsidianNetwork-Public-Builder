#!/usr/bin/env python3
"""B531 missing-model regression for reactor and powerbank casing/glass."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PATCH=Path(__file__).resolve().parents[1]/"features/v174/apply-multiblock-lit-blockstates-531.py"
SKINS=("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass")

class LitModelRegression(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.assets=self.root/"assets/obsidiannetwork"
        for name in SKINS:
            (self.assets/"blockstates").mkdir(parents=True,exist_ok=True)
            (self.assets/"models/block").mkdir(parents=True,exist_ok=True)
            data={"variants":{
                "formed=false":{"model":"obsidiannetwork:block/"+name},
                "formed=true":{"model":"obsidiannetwork:block/"+name+"_formed"}}}
            (self.assets/"blockstates"/(name+".json")).write_text(json.dumps(data))
            for suffix in ("","_formed"):
                (self.assets/"models/block"/(name+suffix+".json")).write_text("{}")
    def run_patch(self):
        return subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_RESOURCE_ROOT=str(self.root)),
                              capture_output=True,text=True,check=False)
    def test_all_four_states_preserve_formed_texture(self):
        r=self.run_patch()
        self.assertEqual(r.returncode,0,r.stderr)
        for name in SKINS:
            v=json.loads((self.assets/"blockstates"/(name+".json")).read_text())["variants"]
            self.assertEqual(len(v),4)
            for formed in ("false","true"):
                for lit in ("false","true"):
                    self.assertEqual(v[f"formed={formed},lit={lit}"]["model"],
                      "obsidiannetwork:block/"+name+("_formed" if formed=="true" else ""))
    def test_missing_model_fails_closed(self):
        (self.assets/"models/block/reactor_glass_formed.json").unlink()
        r=self.run_patch()
        self.assertNotEqual(r.returncode,0)
        self.assertIn("B531_MISSING_SKIN_MODEL",r.stderr)
    def test_bad_old_state_fails_closed(self):
        (self.assets/"blockstates/reactor_casing.json").write_text('{"variants":{}}')
        r=self.run_patch()
        self.assertNotEqual(r.returncode,0)
        self.assertIn("B531_UNEXPECTED_PRE_LIGHT_SKIN",r.stderr)

if __name__=="__main__":
    unittest.main()
