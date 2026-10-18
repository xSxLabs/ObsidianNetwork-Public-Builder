#!/usr/bin/env python3
"""Guard the real GameTest two-owner authorization script and source generator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/wireless-energy/inject-wireless-owner-authorization-gametest.py"
S=SCRIPT.read_text()


class WirelessTwoOwnerAuthorization(unittest.TestCase):
    def test_actual_distinct_server_player_path_and_denials(self):
        for check in (
            "FakePlayerFactory.get(", "java.util.UUID.fromString(",
            "check(!storage.canAccess(b,id)", "storage.available(b).stream().noneMatch(",
            "check(!storage.setCharging(b,id,31)", "check(!storage.rename(b,id,",
            "check(!storage.delete(b,id)", "check(!antenna.canConfigure(b)",
            "check(!antenna.selectNetworkFor(b,id)", "antenna.selectNetworkFor(a,id)",
            "storage.rename(a,id,", "storage.setCharging(a,id,17)",
            "storage.delete(a,id)", "storage.find(id)==null",
            "check(antenna.stored()==1024",
            "WIRELESS preserved FE can be recovered after network deletion",
            "WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS",
        ):
            self.assertIn(check,S,check)
        self.assertIn("assert s.count(anchor)==1",S)

    def test_injector_adds_after_real_chunk_test_and_is_not_reentrant(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"dev/obsidiannetwork/build103"
            root.mkdir(parents=True)
            java=root/"Build103GameTests.java"
            java.write_text('''
                     System.out.println("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS");
                   })
                   .thenSucceed();''')
            env={**os.environ,"V1_SOURCE_ROOT":temp}
            first=subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True,env=env)
            self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            built=java.read_text()
            self.assertEqual(built.count("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS"),1)
            self.assertEqual(built.count("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS"),1)
            second=subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True,env=env)
            self.assertNotEqual(second.returncode,0)


if __name__=="__main__":
    unittest.main()
