"""Guard the reconstructed-source/test/package ordering that Build #194 lacked."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/networkstorage-v1.6.yml'


class WorkflowPipelineTests(unittest.TestCase):
    def test_every_runtime_patch_precedes_gametests(self):
        script = WORKFLOW.read_text()
        execution = script.index('runGameTestServer --stacktrace')
        for patch in (
            'private/v1.1.1/apply-v16-final-features.py',
            'private/v1.1.1/apply-perf-full-cell-fast-reject.py',
            'private/v1.1.1/apply-perf-shift-craft-copy-elision.py',
            'private/v1.1.1/apply-v16-bundle-tps-cache.py',
            'patches/equipment-dirty-serialization.py',
            'patches/equipment-round3-hotpaths.py',
            'patches/terminal-menu-hotpaths.py',
            'patches/item-conduit-tick-dedup.py',
        ):
            call = 'python3 ' + patch
            self.assertEqual(script.count(call), 1, patch)
            self.assertLess(script.index(call), execution, patch)
        self.assertNotIn('python3 private/', script[execution:])
        self.assertNotIn('python3 patches/', script[execution:])

    def test_runtime_manifest_spans_tests_and_restart(self):
        script = WORKFLOW.read_text()
        capture = script.index('python3 scripts/build_provenance.py capture')
        execution = script.index('runGameTestServer --stacktrace')
        restart = script.index('python3 tests/integration/item_conduit_restart.py')
        cleanup = script.index('rm -rf work/src/main/java/dev/obsidiannetwork/build103')
        verify = script.index('python3 scripts/build_provenance.py verify')
        publish = script.index('cp "$JAR_PATH" dist/')
        self.assertLess(capture, execution)
        self.assertLess(execution, restart)
        self.assertLess(restart, cleanup)
        self.assertLess(cleanup, verify)
        self.assertLess(verify, script.index('python3 scripts/diagnostic_report.py'))
        self.assertLess(script.index('test -s dist/diagnostic-report.json'), publish)
        self.assertIn('ON_SERVER_TICK_REPORT=', script[capture:execution])


if __name__ == '__main__':
    unittest.main()
