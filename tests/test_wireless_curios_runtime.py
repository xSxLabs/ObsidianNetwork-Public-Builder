#!/usr/bin/env python3
"""Curios absent/present GameTest source contract; fail if patch silently drifts."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/wireless-energy/inject-wireless-curios-runtime-gametest.py"
S=PATCH.read_text()


class WirelessCuriosRuntime(unittest.TestCase):
    def test_optional_loading_and_real_bridge_path(self):
        for entry in (
            'isLoaded("curios")',
            'Class.forName("top.theillusivec4.curios.api.CuriosApi")',
            'Class.forName("dev.obsidiannetwork.wireless.WirelessCuriosCharging")',
            'getDeclaredMethod("charge",',
            'method.invoke(null,probe,',
            'WIRELESS_CURIOS_ABSENT_START_V1 PASS',
            'WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS',
        ):
            self.assertIn(entry,S)
        self.assertIn("assert s.count(anchor)==1",S)

    def test_inject_once_and_preserve_previous_authorization_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/"dev/obsidiannetwork/build103"
            directory.mkdir(parents=True)
            target=directory/"Build103GameTests.java"
            target.write_text('''
                     System.out.println("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS");
                   })
                   .thenSucceed();''')
            env={**os.environ,"V1_SOURCE_ROOT":tmp}
            p=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            j=target.read_text()
            self.assertEqual(j.count("WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS"),1)
            self.assertEqual(j.count("WIRELESS_CURIOS_ABSENT_START_V1 PASS"),1)
            self.assertIn("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS",j)
            again=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)


if __name__=="__main__":
    unittest.main()
