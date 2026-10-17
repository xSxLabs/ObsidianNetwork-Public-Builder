#!/usr/bin/env python3
"""Source-based safety test for known-neighbor BlockState capability lookup."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"patches/spark-energy-reuse-known-blockstate.py"
REL="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
def fixture():
    x="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {\n"
    for method in ("getAmountAsLong()","extract(int amount,TransactionContext tx)","insert(int amount,TransactionContext tx)"):
        x+=("void "+method+"{\n"
            "int cableBudget=4096;while(cableBudget-- > 0){\n"
            "BlockState nextState = server.getBlockState(next);\n"
            "EnergyHandler source=server.getCapability(Energy.BLOCK, next, side.getOpposite());\n"
            "if(source==null)source=server.getCapability(Energy.BLOCK, next, null);\n"
            "}\n}\n")
    return x+"}\n"
def run(source):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/REL;p.parent.mkdir(parents=True);p.write_text(source)
        r=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=d),capture_output=True,text=True)
        return r,p.read_text()
class KnownStateCapabilityTests(unittest.TestCase):
    def test_sided_and_fallback_context_preserved(self):
        result,after=run(fixture())
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(after.count("server.getCapability(Energy.BLOCK, next, nextState, null, side.getOpposite())"),3)
        self.assertEqual(after.count("server.getCapability(Energy.BLOCK, next, nextState, null, null)"),3)
        self.assertEqual(after.count("server.getBlockState(next)"),3)
        self.assertEqual(after.count("cableBudget-- > 0"),3)
    def test_missing_input_state_or_original_fallback_is_rejected(self):
        for before,after in (
          ("BlockState nextState = server.getBlockState(next);","BlockState nextState = null;"),
          ("server.getCapability(Energy.BLOCK, next, null)","server.getCapability(Energy.BLOCK, next, side)"),
          ("cableBudget-- > 0","cableBudget-- > 1"),
        ):
            changed=fixture().replace(before,after,1)
            bad,unchanged=run(changed)
            self.assertNotEqual(bad.returncode,0)
            self.assertEqual(unchanged,changed)
    def test_double_run_rejected_without_changes(self):
        first,changed=run(fixture())
        self.assertEqual(first.returncode,0,first.stderr)
        result,unchanged=run(changed)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(unchanged,changed)
if __name__=="__main__":unittest.main()
