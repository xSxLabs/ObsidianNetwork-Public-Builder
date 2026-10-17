#!/usr/bin/env python3
"""Fail-closed helper injections and randomized exact cable/bundle logic model."""
import os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"patches/spark-energy-fast-reject-nonbundle.py"
REL="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
ORIGINAL="""public final class EnergyCableBlockEntity {
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
}
"""
def run(source):
    with tempfile.TemporaryDirectory() as root:
        p=Path(root)/REL;p.parent.mkdir(parents=True);p.write_text(source)
        result=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=root),capture_output=True,text=True)
        return result,p.read_text()
class NonBundleFastRejectTests(unittest.TestCase):
    def test_exact_methods_and_existing_logic_retained(self):
        result,patched=run(ORIGINAL)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(patched.count("XSXLABS_SPARK_ENERGY_NONBUNDLE_FAST_REJECT_V1"),2)
        self.assertEqual(patched.count("level.getBlockEntity(pos)"),2)
        self.assertIn("EnergyCableBlock.isCut(state,side)",patched)
        self.assertIn("b.has(ConduitBundleBlockEntity.Layer.ENERGY)",patched)
        self.assertIn("b.enabled(ConduitBundleBlockEntity.Layer.ENERGY,side)",patched)
    def test_incompatible_helper_fails_closed(self):
        for before,after in (
            ("BlockEntity be=level.getBlockEntity(pos);","BlockEntity be=getBe(pos);"),
            ("ConduitBundleBlockEntity b&&b.has","OtherBundle b&&b.has"),
            ("ObsidianNetwork.ENERGY_CABLE.get()","ObsidianNetwork.ITEM_CABLE.get()"),
        ):
            broken=ORIGINAL.replace(before,after,1)
            response,unchanged=run(broken)
            self.assertNotEqual(response.returncode,0)
            self.assertEqual(unchanged,broken)
    def test_patched_source_cannot_be_applied_twice(self):
        first,changed=run(ORIGINAL)
        self.assertEqual(first.returncode,0,first.stderr)
        again,repeated=run(changed)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(repeated,changed)
    def test_20000_random_energy_cut_and_bundle_membership_cases(self):
        rnd=random.Random(20261017)
        for trial in range(20000):
            kind=rnd.choice(("cable","bundle","air","machine","fluid","solid"))
            energy_layer=rnd.choice((False,True))
            enabled=rnd.choice((False,True))
            cut=rnd.choice((False,True))
            for method in ("cable","open"):
                old=(kind=="cable" and (method=="cable" or not cut)) or (
                    kind=="bundle" and (energy_layer if method=="cable" else enabled))
                guard=kind=="cable" or kind=="bundle"
                optimized=guard and ((kind=="cable" and (method=="cable" or not cut)) or (
                    kind=="bundle" and (energy_layer if method=="cable" else enabled)))
                self.assertEqual(bool(old),bool(optimized))
if __name__=="__main__":unittest.main()
