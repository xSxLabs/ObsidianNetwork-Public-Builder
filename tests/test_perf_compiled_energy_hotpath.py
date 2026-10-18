#!/usr/bin/env python3
"""Mutation tests: bytecode hotpath contract rejects duplicate/no FE semantics."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
from zipfile import ZipFile

VERIFY=Path(__file__).resolve().parent/"verify_compiled_energy_hotpath.py"
SPEC=importlib.util.spec_from_file_location("compiled_energy_verifier",VERIFY)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def method(name):
    contract=[
        "  private static boolean "+name+"(ServerLevel, BlockPos, BlockState);",
        "    Code:",
        "       1: // Field ObsidianNetwork.ENERGY_CABLE:",
        "       4: // Method BlockState.is:",
        "       8: // Field ObsidianNetwork.CONDUIT_BUNDLE:",
        "      12: // Method BlockState.is:",
        "      16: // Method ServerLevel.getBlockEntity:",
        "      20: // class ConduitBundleBlockEntity",
        "      24: // Field ConduitBundleBlockEntity$Layer.ENERGY",
    ]
    if name=="energyOpen":
        contract+=["      28: // Method EnergyCableBlock.isCut:",
                   "      32: // Method ConduitBundleBlockEntity.enabled:"]
    else:
        contract+=["      28: // Method ConduitBundleBlockEntity.has:"]
    return "\n".join(contract)+"\n"

BASE=method("energyCable")+"\n"+method("energyOpen")+"\n  private static void following();\n"
class Result:
    def __init__(self,source):
        self.stdout=source

class CompiledEnergyContractTest(TestCase):
    def jar(self,folder):
        jar=Path(folder)/"test.jar"
        with ZipFile(jar,"w") as z:
            z.writestr(MOD.ENTRY,b"fake class bytecode")
        return jar

    def test_verified_hotpath_and_multiple_negative_mutations(self):
        with TemporaryDirectory() as folder:
            jar=self.jar(folder)
            with patch.object(MOD.subprocess,"run",return_value=Result(BASE)):
                MOD.verify(jar)
            for missing in (
                "ObsidianNetwork.ENERGY_CABLE:",
                "ObsidianNetwork.CONDUIT_BUNDLE:",
                "ServerLevel.getBlockEntity:",
                "ConduitBundleBlockEntity$Layer.ENERGY",
                "EnergyCableBlock.isCut:",
                "ConduitBundleBlockEntity.enabled:",
                "ConduitBundleBlockEntity.has:",
            ):
                with self.subTest(missing=missing):
                    with patch.object(MOD.subprocess,"run",return_value=Result(BASE.replace(missing,"removed"))):
                        with self.assertRaises(AssertionError):
                            MOD.verify(jar)
            # Old build280: duplicate BlockState.is from identical block type.
            duplicate=BASE.replace("      16: // Method ServerLevel.getBlockEntity:",
                                   "      13: // Method BlockState.is:\n      16: // Method ServerLevel.getBlockEntity:")
            with patch.object(MOD.subprocess,"run",return_value=Result(duplicate)):
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)

    def test_missing_jar_or_incomplete_method_boundary_rejected(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(AssertionError):
                MOD.verify(Path(folder)/"missing.jar")
            jar=self.jar(folder)
            with patch.object(MOD.subprocess,"run",return_value=Result(method("energyCable"))):
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)

if __name__=="__main__":
    main()
