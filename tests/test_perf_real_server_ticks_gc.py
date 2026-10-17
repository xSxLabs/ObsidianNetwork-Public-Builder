#!/usr/bin/env python3
"""Fail-closed unit tests for test-only 50-drive tick and GC injection."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"patches/perf-real-server-ticks-gc-gametest.py"
REL="src/main/java/dev/obsidiannetwork/build103/Build103GameTests.java"
SOURCE="""class Build103GameTests {
private static final class FiftyDriveTest extends GameTestInstance {
  FiftyDriveTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data) { super(data); }
  void run(GameTestHelper h) {
    final long[] storageTickWorkNs=new long[20];
    System.out.println("REAL_50_DRIVE_SUSTAINED_SUMMARY");
    if(p95>50_000_000L) throw new IllegalStateException();
    h.succeed();
  }
}
private static final class MixedCableTest extends GameTestInstance {}
}
"""
def apply(source):
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/REL
        file.parent.mkdir(parents=True)
        file.write_text(source)
        done=subprocess.run([sys.executable,str(SCRIPT)],
                            env=dict(os.environ,V1_PROJECT_ROOT=tmp),
                            capture_output=True,text=True)
        return done,file.read_text()

class TickGcProbeTests(unittest.TestCase):
    def test_real_server_methods_and_unchanged_neighbor(self):
        result,updated=apply(SOURCE)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("getTickTimesNanos()",updated)
        self.assertIn("getGarbageCollectorMXBeans()",updated)
        self.assertIn("REAL_SERVER_TICK_RING_V1",updated)
        self.assertIn("REAL_SERVER_GC_WINDOW_V1",updated)
        self.assertEqual(updated.count("h.succeed();"),1)
        self.assertEqual(updated.split("private static final class MixedCableTest")[1],
                         SOURCE.split("private static final class MixedCableTest")[1])

    def test_removed_budget_refuses_mutation(self):
        changed=SOURCE.replace("if(p95>50_000_000L)","if(p95>60_000_000L)")
        run,updated=apply(changed)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(updated,changed)

    def test_removed_tick_load_refuses_mutation(self):
        changed=SOURCE.replace("storageTickWorkNs=new long[20]","storageTickWorkNs=new long[10]")
        run,updated=apply(changed)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(updated,changed)

    def test_double_injection_refused(self):
        ok,updated=apply(SOURCE)
        self.assertEqual(ok.returncode,0,ok.stderr)
        fail,again=apply(updated)
        self.assertNotEqual(fail.returncode,0)
        self.assertEqual(again,updated)

if __name__=="__main__":
    unittest.main()
