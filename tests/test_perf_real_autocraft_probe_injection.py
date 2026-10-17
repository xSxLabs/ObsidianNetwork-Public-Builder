#!/usr/bin/env python3
"""Fail-closed source contract tests for CI-only live GameTest injection."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH=Path(__file__).resolve().parents[1]/"patches/perf-real-autocraft-reservation-gametest.py"
REL="src/main/java/dev/obsidiannetwork/build103/Build103GameTests.java"
FIXTURE="""
class Build103GameTests {
private static final class FiftyDriveTest extends GameTestInstance {
  FiftyDriveTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data) { super(data); }
  void run(GameTestHelper h) {
     var level=h.getLevel();
     var rt=runtime;
     System.out.println("REAL_50_DRIVE_SUSTAINED_SUMMARY");
     if(p95>50_000_000L) throw new IllegalStateException();
     h.succeed();
  }
}
private static final class MixedCableTest extends GameTestInstance {}
}
"""


def run_patch(source):
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/REL
        p.parent.mkdir(parents=True)
        p.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],
                              env=dict(os.environ,V1_PROJECT_ROOT=temp),
                              capture_output=True,text=True)
        return result,p.read_text()


class LiveAutocraftProbeTests(unittest.TestCase):
    def test_probe_attaches_to_only_fifty_drive_game_test(self):
        result,modified=run_patch(FIXTURE)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        prefix,tail=modified.split("private static final class MixedCableTest")
        self.assertEqual(prefix.count("REAL_AUTOCRAFT_RESERVATION_CONSERVATION_V1"),1)
        self.assertEqual(prefix.count("REAL_AUTOCRAFT_IDLE_RESERVATION_V1"),1)
        self.assertEqual(prefix.count("assertLiveAutocraftReservations(level,rt);"),1)
        self.assertNotIn("REAL_AUTOCRAFT",tail)
        self.assertEqual(modified.count("h.succeed();"),1)
        self.assertIn("runtime.storage().insertExact(key,available.canonicalPayload(),10L)",modified)

    def test_changed_game_test_fails_unchanged(self):
        broken=FIXTURE.replace("REAL_50_DRIVE_SUSTAINED_SUMMARY","UNEXPECTED_SOURCE")
        result,after=run_patch(broken)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(after,broken)

    def test_second_application_is_rejected(self):
        result,patched=run_patch(FIXTURE)
        self.assertEqual(result.returncode,0,result.stderr)
        again,second=run_patch(patched)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(second,patched)


if __name__=="__main__":
    unittest.main()
