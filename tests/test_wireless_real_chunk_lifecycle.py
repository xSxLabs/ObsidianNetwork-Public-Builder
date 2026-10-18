#!/usr/bin/env python3
"""Exercise the test-only injector and enforce a *real* chunk eviction assertion."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/wireless-energy/inject-wireless-real-chunk-lifecycle-gametest.py"
SRC=PATCH.read_text()


class WirelessRealChunkLifecycle(unittest.TestCase):
    def test_actual_unload_and_reload_with_exact_energy_balance(self):
        for needle in (
            "nether.getChunkSource().hasChunk(cx,cz)",
            "check(!loaded,",
            "WirelessEnergyRuntime.available(",
            "WirelessEnergyRuntime.pull(",
            "tx.stored()==4096",
            "nether.getChunkAt(txPos);",
            "nether.setChunkForced(cx,cz,false)",
            "WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS",
            "check(tx.stored()==4096,",
            "nether.setBlock(txPos,Blocks.AIR.defaultBlockState(),3);",
        ):
            self.assertIn(needle,SRC)
        self.assertIn("assert source.count(anchor)==1",SRC)

    def test_generator_applies_once_and_preserves_prior_crossdim_test(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"dev/obsidiannetwork/build103"
            root.mkdir(parents=True)
            source=root/"Build103GameTests.java"
            source.write_text('''
                     System.out.println("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS");
                   })
                   .thenSucceed();''')
            env={**os.environ,"V1_SOURCE_ROOT":folder}
            result=subprocess.run([sys.executable,str(PATCH)],env=env,
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            generated=source.read_text()
            self.assertEqual(generated.count("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS"),1)
            self.assertEqual(generated.count("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS"),1)
            self.assertIn("check(!loaded,",generated)
            self.assertIn("nether.getChunkSource().hasChunk(cx,cz)",generated)
            self.assertLess(generated.index("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS"),
                            generated.index("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS"))
            again=subprocess.run([sys.executable,str(PATCH)],env=env,
                                 capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0,"re-application must fail closed")


if __name__=="__main__":
    unittest.main()
