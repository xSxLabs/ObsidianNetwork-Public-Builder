import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_provenance.py"
SPEC = importlib.util.spec_from_file_location("build_provenance", SCRIPT)
provenance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provenance)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.args = argparse.Namespace(source_dir=self.root / "source", resource_dir=self.root / "resources", classes_dir=self.root / "classes", public_repo=self.root, private_repo=self.root, private_source_artifact=None, manifest=self.root / "manifest.json", jar=self.root / "mod.jar")
        for directory in (self.args.source_dir, self.args.resource_dir, self.args.classes_dir):
            directory.mkdir()
        (self.args.source_dir / "Runtime.java").write_text("class Runtime {}")
        (self.args.resource_dir / "runtime.json").write_text("{}")
        (self.args.classes_dir / "Runtime.class").write_bytes(b"compiled runtime")
        self.mock = patch.object(provenance, "git_commit", return_value="a" * 40)
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.args.manifest.write_text(json.dumps(provenance.capture(self.args)))

    def jar(self, **extra):
        with ZipFile(self.args.jar, "w") as jar:
            jar.writestr("Runtime.class", (self.args.classes_dir / "Runtime.class").read_bytes())
            jar.writestr("runtime.json", "{}")
            for name, content in extra.items():
                jar.writestr(name, content)

    def test_identical_packaged_runtime_is_verified(self):
        self.jar()
        result = provenance.verify(self.args)
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["jar_classes_identical_to_test_preparation"])

    def test_source_mutation_after_tests_is_rejected(self):
        (self.args.source_dir / "Runtime.java").write_text("class Runtime { int changed; }")
        self.jar()
        with self.assertRaisesRegex(ValueError, "sources changed"):
            provenance.verify(self.args)

    def test_recompiled_class_mutation_is_rejected(self):
        (self.args.classes_dir / "Runtime.class").write_bytes(b"untested class")
        self.jar()
        with self.assertRaisesRegex(ValueError, "classes changed"):
            provenance.verify(self.args)

    def test_jar_class_must_equal_tested_class_bytes(self):
        with ZipFile(self.args.jar, "w") as jar:
            jar.writestr("Runtime.class", b"different packaged class")
            jar.writestr("runtime.json", "{}")
        with self.assertRaisesRegex(ValueError, "packaged JAR classes"):
            provenance.verify(self.args)

    def test_unexpected_stale_runtime_class_is_rejected(self):
        self.jar(**{"Unexpected.class": b"stale"})
        with self.assertRaisesRegex(ValueError, "packaged JAR classes"):
            provenance.verify(self.args)

    def test_ci_fixture_removal_is_allowed_but_packaging_is_rejected(self):
        for prefix in provenance.CI_PREFIXES:
            path = self.args.classes_dir / prefix / "Probe.class"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"test fixture")
        self.jar()
        self.assertEqual(provenance.verify(self.args)["status"], "passed")
        self.jar(**{"dev/obsidiannetwork/restarttest/Probe.class": b"test fixture"})
        with self.assertRaisesRegex(ValueError, "CI fixtures leaked"):
            provenance.verify(self.args)


if __name__ == "__main__":
    unittest.main()
