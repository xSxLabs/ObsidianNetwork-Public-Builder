#!/usr/bin/env python3
"""Regression fixtures: ENERGY helper duplicate immutable BlockState predicate.

Synthetic Python/Java source checks complement real NeoForge FE and wireless
GameTests; never replace them. Reject source drift before writing.
"""
import ast
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FAST=ROOT/"patches/spark-energy-fast-reject-nonbundle.py"
PATCH=ROOT/"patches/spark-energy-helper-duplicate-blocktype-elision.py"
REL="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
SOURCE="""public final class EnergyCableBlockEntity {
 private static boolean energyCable(ServerLevel level,BlockPos pos,BlockState state) {
  if(state.is((Block)ObsidianNetwork.ENERGY_CABLE.get()))return true;
  BlockEntity be=level.getBlockEntity(pos);
  return be instanceof ConduitBundleBlockEntity b&&b.has(ConduitBundleBlockEntity.Layer.ENERGY);
 }
 private static boolean energyOpen(ServerLevel level,BlockPos pos,BlockState state,Direction side) {
  if(state.is((Block)ObsidianNetwork.ENERGY_CABLE.get()))return !EnergyCableBlock.isCut(state,side);
  BlockEntity be=level.getBlockEntity(pos);
  return be instanceof ConduitBundleBlockEntity b&&b.enabled(ConduitBundleBlockEntity.Layer.ENERGY,side);
 }
 private final class CableEnergyHandler implements EnergyHandler {
  public void noop() {}
 }
 // XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1
}
"""

def apply(source,original_fast_patch=True):
    with tempfile.TemporaryDirectory() as folder:
        file=Path(folder)/REL
        file.parent.mkdir(parents=True)
        file.write_text(source)
        env={**os.environ,"V1_SOURCE_ROOT":folder}
        result_fast=None
        if original_fast_patch:
            result_fast=subprocess.run([sys.executable,str(FAST)],env=env,capture_output=True,text=True)
            if result_fast.returncode:
                return result_fast,source,source
        before=file.read_text()
        result=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
        return result,before,file.read_text()

class EnergyDuplicatePredicateRegression(unittest.TestCase):
    def test_six_hot_path_evaluations_reduce_to_four_without_semantic_changes(self):
        ast.parse(PATCH.read_text())
        result,before,after=apply(SOURCE)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(before.count("state.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"),4)
        self.assertEqual(after.count("state.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"),2)
        self.assertEqual(after.count("XSXLABS_ENERGY_HELPER_DUPLICATE_BLOCKTYPE_ELISION_V1"),2)
        self.assertEqual(after.count("boolean physicalEnergyCable = "),2)
        self.assertEqual(after.count("if(!physicalEnergyCable && !state.is((Block)ObsidianNetwork.CONDUIT_BUNDLE.get())) return false;"),2)
        for invariant in (
            "return !EnergyCableBlock.isCut(state,side);",
            "b&&b.has(ConduitBundleBlockEntity.Layer.ENERGY)",
            "b&&b.enabled(ConduitBundleBlockEntity.Layer.ENERGY,side)",
            "BlockEntity be=level.getBlockEntity(pos);",
            "private final class CableEnergyHandler implements EnergyHandler",
        ):
            self.assertEqual(after.count(invariant),before.count(invariant),invariant)
        self.assertEqual(after.count("getBlockEntity("),before.count("getBlockEntity("))
        self.assertEqual(after.count("ObsidianNetwork.CONDUIT_BUNDLE.get()"),2)
        self.assertNotIn("static boolean physicalEnergyCable",after)

    def test_double_patch_or_untrusted_source_drift_never_modifies_file(self):
        good,original,updated=apply(SOURCE)
        self.assertEqual(good.returncode,0,good.stderr)
        again,before,after=apply(updated,False)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(before,after)
        fast,fast_src,_=apply(SOURCE.replace("ConduitBundleBlockEntity b&&b.has","Other b&&b.has"))
        self.assertNotEqual(fast.returncode,0)
        for old,new in (
            ("return !EnergyCableBlock.isCut(state,side)","return true"),
            ("b&&b.has(","b&&b.any("),
            ("b&&b.enabled(","b&&b.any("),
            ("state.is((Block)ObsidianNetwork.CONDUIT_BUNDLE.get())",
             "state.is((Block)ObsidianNetwork.ITEM_CABLE.get())"),
            ("BlockEntity be=level.getBlockEntity(pos);","BlockEntity be=null;"),
        ):
            changed=original.replace(old,new,1)
            self.assertNotEqual(changed,original)
            r,b,a=apply(changed,False)
            self.assertNotEqual(r.returncode,0,old)
            self.assertEqual(b,a,old)

    def test_randomized_equivalence_cable_bundles_and_six_faces(self):
        rng=random.Random(20261018)
        for _ in range(30000):
            kind=rng.choice(("energy_cable","conduit_bundle","item_cable","machine","air","fluid","stone"))
            cut=[rng.choice((False,True)) for __ in range(6)]
            enabled=[rng.choice((False,True)) for __ in range(6)]
            layer=rng.choice((False,True))
            side=rng.randrange(6)
            is_energy=kind=="energy_cable"
            is_bundle=kind=="conduit_bundle"
            old_cable=is_energy or (is_bundle and layer)
            old_open=(is_energy and not cut[side]) or (is_bundle and enabled[side])
            # Hoisted immutable predicate mirrors the original two checks.
            cable=is_energy
            new_cable=(cable or is_bundle) and (cable or (is_bundle and layer))
            open_side=is_energy
            new_open=(open_side or is_bundle) and (
                (open_side and not cut[side]) or (is_bundle and enabled[side]))
            self.assertEqual(new_cable,old_cable)
            self.assertEqual(new_open,old_open)

if __name__=="__main__":
    unittest.main()
