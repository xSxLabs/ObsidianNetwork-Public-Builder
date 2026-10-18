#!/usr/bin/env python3
"""Synthetic fail-closed gates for the *final-JAR* solar bytecode verifier."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
from zipfile import ZipFile

VERIFY=Path(__file__).resolve().parent/"verify_compiled_solar_cache.py"
SPEC=importlib.util.spec_from_file_location("verify_solar", VERIFY)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
BYTECODE="""private final BlockCapabilityCache[] energyNeighbors;
  get3DDataValue:()I
  BlockCapabilityCache.create:
  BlockCapabilityCache.getCapability:()
  java/util/Arrays.fill:
  java/util/Arrays.fill:
  java/util/Arrays.fill:
  Transaction.openRoot:
  Transaction.commit:
"""
class Result:
    stdout=BYTECODE

class SolarReleaseVerifier(TestCase):
    def make_jar(self, path, leak=False):
        with ZipFile(path,"w") as z:
            z.writestr(MOD.ENTRY,b"class bytes")
            if leak:
                z.writestr("dev/obsidiannetwork/build103/Build103GameTests.class",b"test")

    def test_valid_compiled_contract(self):
        with TemporaryDirectory() as folder:
            jar=Path(folder)/"mod.jar"
            self.make_jar(jar)
            with patch.object(MOD.subprocess,"run",return_value=Result()):
                MOD.verify(jar)

    def test_each_missing_guard_fails(self):
        with TemporaryDirectory() as folder:
            jar=Path(folder)/"mod.jar"
            self.make_jar(jar)
            for missing in ("get3DDataValue:()I","BlockCapabilityCache.create:",
                            "BlockCapabilityCache.getCapability:()","Transaction.openRoot:",
                            "Transaction.commit:"):
                with self.subTest(missing=missing):
                    fake=type("Stub",(),{"stdout":BYTECODE.replace(missing,"removed")})()
                    with patch.object(MOD.subprocess,"run",return_value=fake):
                        with self.assertRaises(AssertionError):
                            MOD.verify(jar)
            for bad in (BYTECODE.replace("java/util/Arrays.fill:","",1),
                        BYTECODE+"java/util/EnumMap\n"):
                with patch.object(MOD.subprocess,"run",return_value=type("Stub",(),{"stdout":bad})()):
                    with self.assertRaises(AssertionError):
                        MOD.verify(jar)

    def test_missing_class_and_leaked_gametest_are_rejected(self):
        with TemporaryDirectory() as folder:
            jar=Path(folder)/"mod.jar"
            with ZipFile(jar,"w") as z:
                z.writestr("README.txt","sample")
            with self.assertRaises(AssertionError):
                MOD.verify(jar)
            self.make_jar(jar,leak=True)
            with self.assertRaises(AssertionError):
                MOD.verify(jar)

if __name__=="__main__":
    main()
