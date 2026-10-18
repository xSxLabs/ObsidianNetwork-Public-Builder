#!/usr/bin/env python3
"""CI-only 10/50/100 physical wireless FE runtime density regression contracts."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"features/wireless-energy/inject-wireless-dense-runtime-gametest.py"
S=SCRIPT.read_text()


class WirelessDenseRuntimeContracts(unittest.TestCase):
    def test_genuine_fe_blocks_10_50_100_and_cleanup(self):
        for marker in (
            "WIRELESS_DENSE_REAL_SERVER_10_V1 PASS",
            "WIRELESS_DENSE_REAL_SERVER_50_V1 PASS",
            "WIRELESS_DENSE_REAL_SERVER_100_V1 PASS",
            "WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS",
            "WirelessEnergyRuntime.available(",
            "world.setBlock(sourcePos,ObsidianNetwork.NETWORK_TRANSMITTER.get()",
            "world.setBlock(receiverPos,ObsidianNetwork.NETWORK_RECEIVER.get()",
            "world.setBlock(cellPos,ObsidianNetwork.BASIC_ENERGY_CELL.get()",
            "denseSender.energyHandler().insert(16000,funding)",
            "check(total==10L*256000&&received>0",
            "check(total==50L*256000&&received>0",
            "check(total==100L*256000&&received>0",
            "world.setChunkForced(cx,cz,false)",
            "check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(",
        ):
            self.assertIn(marker,S,marker)
        self.assertEqual(S.count("world.setChunkForced(cx,cz,true)"),1)
        self.assertEqual(S.count("world.setChunkForced(cx,cz,false)"),1)

    def test_generator_appends_once_after_curios_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"dev/obsidiannetwork/build103"
            root.mkdir(parents=True)
            source=root/"Build103GameTests.java"
            source.write_text("""
                     System.out.println("WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS");
                      }catch(ReflectiveOperationException error){
                     }
                   })
                   .thenSucceed();""")
            env={**os.environ,"V1_SOURCE_ROOT":d}
            result=subprocess.run([sys.executable,str(SCRIPT)],env=env,
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            generated=source.read_text()
            self.assertEqual(generated.count("WIRELESS_DENSE_REAL_SERVER_100_V1 PASS"),1)
            self.assertEqual(generated.count("WIRELESS_DENSE_REAL_SERVER_50_V1 PASS"),1)
            self.assertEqual(generated.count("WIRELESS_DENSE_REAL_SERVER_10_V1 PASS"),1)
            self.assertEqual(generated.count(".thenSucceed();"),1)
            self.assertLess(generated.index("WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS"),
                            generated.index("WIRELESS_DENSE_REAL_SERVER_10_V1 PASS"))
            again=subprocess.run([sys.executable,str(SCRIPT)],env=env,
                                 capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)


if __name__=="__main__":
    unittest.main()
