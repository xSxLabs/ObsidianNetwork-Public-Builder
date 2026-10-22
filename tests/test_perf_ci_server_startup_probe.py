#!/usr/bin/env python3
"""Build-time fast server readiness gate: no false pass on early exit/crash."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/"tests/ci_server_startup_probe.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"


def probe(code, timeout=4, stability=0.3):
    with tempfile.TemporaryDirectory() as tmp:
        cmd=[
            sys.executable,str(PROBE),
            "--workdir",tmp,"--log",str(Path(tmp)/"server.log"),
            "--timeout",str(timeout),"--stability",str(stability),
            "--",sys.executable,"-u","-c",code
        ]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=8)
        return result


class CiServerStartupSpeedTests(unittest.TestCase):
    def test_exits_after_ready_stability_not_whole_timeout(self):
        result=probe('import time;print("Done (0.4s)!");time.sleep(5)')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("CI_SERVER_STARTUP_PASS",result.stdout)

    def test_does_not_pass_on_start_message_only(self):
        result=probe('print("Starting Minecraft server on *:25565")',timeout=1)
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn("CI_SERVER_STARTUP_PASS",result.stdout)

    def test_rejects_crash_after_ready(self):
        result=probe('import time;print("Done (1.2s)!");print("Exception in server tick loop");time.sleep(5)')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn("CI_SERVER_STARTUP_PASS",result.stdout)

    def test_workflow_keeps_all_game_tests_and_compiled_gates(self):
        w=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("gradle/actions/setup-gradle@v6",w)
        self.assertIn("cache-read-only: false",w)
        self.assertIn("python3 tests/ci_server_startup_probe.py",w)
        self.assertNotIn("timeout 90s bash -c 'cd work && gradle",w)
        for contract in (
            "runGameTestServer --stacktrace",
            "build103-postpatch-gametest.log",
            "build103-curios-installed-gametest.log",
            "verify_compiled_network_elytra_speedcheck.py",
            "gradle --no-daemon --no-configuration-cache clean build",
            "python3 -m unittest discover -s tests -p 'test_perf_*.py' -v",
        ):
            self.assertIn(contract,w)


if __name__=="__main__":
    unittest.main()
