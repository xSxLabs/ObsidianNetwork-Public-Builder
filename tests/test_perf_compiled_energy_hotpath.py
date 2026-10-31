#!/usr/bin/env python3
"""Mutation tests: compiled ENERGY lazy block cache and live FE semantics must hold."""
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
        "       1: // Field XsxRegisteredEnergyBlocks.ENERGY:",
        "       4: // Method BlockState.is:",
        "       8: // Field XsxRegisteredEnergyBlocks.BUNDLE:",
        "      12: // Method BlockState.is:",
        "      16: // Method ServerLevel.getBlockEntity:",
        "      20: // class ConduitBundleBlockEntity",
        "      24: // Field ConduitBundleBlockEntity$Layer.ENERGY",
    ]
    if name=="energyOpen":
        contract+=["      28: // Method xsxEnergyCut:",
                   "      32: // Method ConduitBundleBlockEntity.enabled:"]
    else:
        contract+=["      28: // Method ConduitBundleBlockEntity.has:"]
    return "\n".join(contract)+"\n"

CUT_METHOD="""  private static boolean xsxEnergyCut(BlockState, Direction);
    Code:
       0: // Field XSX_CUT_MASKS:
       4: // InterfaceMethod Map.get:
       8: // Method EnergyCableBlock.isCut:
      12: // Method Direction.get3DDataValue:
      16: // InterfaceMethod Map.put:
"""

BASE=method("energyCable")+"\n"+method("energyOpen")+"\n"+CUT_METHOD+"\n  private static void following();\n"
CACHE="""final class EnergyCableBlockEntity$XsxRegisteredEnergyBlocks {
  private static final Block ENERGY;
  private static final Block BUNDLE;
  static {};
    Code:
       0: // Field ObsidianNetwork.ENERGY_CABLE:
       3: // Method DeferredHolder.get:
       6: // Field ObsidianNetwork.CONDUIT_BUNDLE:
       9: // Method DeferredHolder.get:
}
"""

class Result:
    def __init__(self,source):
        self.stdout=source

class CompiledEnergyContractTest(TestCase):
    def jar(self,folder,include_cache=True):
        jar=Path(folder)/"test.jar"
        with ZipFile(jar,"w") as z:
            z.writestr(MOD.ENTRY,b"fake helper bytecode")
            if include_cache:
                z.writestr(MOD.CACHE_ENTRY,b"fake nested initializer bytecode")
        return jar

    def javap(self,main_code=BASE,cache_code=CACHE):
        def run(cmd,**_):
            return Result(cache_code if cmd[-1]==MOD.CACHE_CLASS else main_code)
        return patch.object(MOD.subprocess,"run",side_effect=run)

    def test_verified_hotpath_and_multiple_negative_mutations(self):
        with TemporaryDirectory() as folder:
            jar=self.jar(folder)
            with self.javap():
                MOD.verify(jar)
            for missing in (
                "XsxRegisteredEnergyBlocks.ENERGY:",
                "XsxRegisteredEnergyBlocks.BUNDLE:",
                "ServerLevel.getBlockEntity:",
                "ConduitBundleBlockEntity$Layer.ENERGY",
                "EnergyCableBlock.isCut:",
                "xsxEnergyCut:",
                "XSX_CUT_MASKS:",
                "Direction.get3DDataValue:",
                "Map.get:",
                "Map.put:",
                "ConduitBundleBlockEntity.enabled:",
                "ConduitBundleBlockEntity.has:",
            ):
                with self.subTest(missing=missing):
                    with self.javap(main_code=BASE.replace(missing,"removed")):
                        with self.assertRaises(AssertionError):
                            MOD.verify(jar)
            for missing in ("ObsidianNetwork.ENERGY_CABLE:",
                            "ObsidianNetwork.CONDUIT_BUNDLE:",
                            "static {};"):
                with self.subTest(cache_missing=missing):
                    with self.javap(cache_code=CACHE.replace(missing,"removed")):
                        with self.assertRaises(AssertionError):
                            MOD.verify(jar)
            # Must reject reverting to old per-neighbor registry reads.
            old=BASE.replace("XsxRegisteredEnergyBlocks.ENERGY:",
                             "ObsidianNetwork.ENERGY_CABLE:")
            with self.javap(main_code=old):
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)
            # Reject duplicate BlockState checks in either compiled helper.
            duplicate=BASE.replace("      16: // Method ServerLevel.getBlockEntity:",
                                   "      13: // Method BlockState.is:\n      16: // Method ServerLevel.getBlockEntity:")
            with self.javap(main_code=duplicate):
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)

    def test_missing_jar_cache_or_method_boundary_rejected(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(AssertionError):
                MOD.verify(Path(folder)/"missing.jar")
            jar=self.jar(folder,include_cache=False)
            with self.javap():
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)
            jar=self.jar(folder,include_cache=True)
            with self.javap(main_code=method("energyCable")):
                with self.assertRaises(AssertionError):
                    MOD.verify(jar)

if __name__=="__main__":
    main()
