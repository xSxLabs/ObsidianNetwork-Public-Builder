#!/usr/bin/env python3
"""Fail closed on changed energy cable source, and preserve capability/FE code."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"patches/spark-energy-bfs-loop-invariants.py"
REL="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
def example():
    s="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {\n"
    for name in ["getAmountAsLong()","extract(int amount, TransactionContext transaction)","insert(int amount, TransactionContext transaction)"]:
        s+="public int "+name+" { ArrayDeque queue = new ArrayDeque();\n"
        s+="HashSet visited = new HashSet(); int cableBudget=4096;\n"
        if name=="getAmountAsLong()":s+="int available = source.getAmountAsLong();\n"
        s+="while (!queue.isEmpty() && cableBudget-- > 0) {\n"
        s+="for (Direction side : Direction.values()) {\n"
        s+="if (nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())) {\n"
        s+="queue.addLast(next.immutable()); } else {\n"
        s+="EnergyHandler source = server.getCapability(Energy.BLOCK, next, side.getOpposite());\n"
        s+="if (source == null) source = server.getCapability(Energy.BLOCK, next, null);\n"
        s+="} } } return 0; }\n"
    return s+"}\n"
def run(s):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/REL;p.parent.mkdir(parents=True);p.write_text(s)
        r=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=tmp),capture_output=True,text=True)
        return r,p.read_text()
class EnergyCableHoistTests(unittest.TestCase):
    def test_three_traversals_keep_fresh_capability_and_bfs(self):
        result,s=run(example())
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(s.count("ENERGY_SCAN_DIRECTIONS = Direction.values()"),1)
        self.assertEqual(s.count("for (Direction side : ENERGY_SCAN_DIRECTIONS)"),3)
        self.assertEqual(s.count("nextState.is(energyCableType)"),3)
        self.assertEqual(s.count("server.getCapability(Energy.BLOCK, next, side.getOpposite())"),3)
        self.assertEqual(s.count("server.getCapability(Energy.BLOCK, next, null)"),3)
        self.assertEqual(s.count("cableBudget-- > 0"),3)
    def test_anchor_changes_dont_write(self):
        original=example()
        for old,new in (
            ("nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())","nextState.is(BLOCK)"),
            ("server.getCapability(Energy.BLOCK, next, null)","null"),
            ("cableBudget-- > 0","cableBudget-- > 1"),
            ("HashSet visited = new HashSet();","HashSet visited = new HashSetX();"),
        ):
            broken=original.replace(old,new,1)
            result,output=run(broken)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(output,broken)
    def test_second_application_rejected(self):
        result,changed=run(example())
        self.assertEqual(result.returncode,0,result.stderr)
        rerun,output=run(changed)
        self.assertNotEqual(rerun.returncode,0)
        self.assertEqual(output,changed)
    def test_helper_based_energy_source_hoists_only_directions(self):
        old=example()
        old=old.replace("nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())",
                        "energyCable(next) && energyOpen(next, side)")
        # The helper-based shape still dynamically checks world state and all
        # external capabilities on each transfer; it must not be simplified.
        old=old.replace("return 0; }", "return 0; }", 1)
        result,updated=run(old)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(updated.count("ENERGY_SCAN_DIRECTIONS = Direction.values()"),1)
        self.assertEqual(updated.count("for (Direction side : ENERGY_SCAN_DIRECTIONS)"),3)
        self.assertEqual(updated.count("energyCable(next) && energyOpen(next, side)"),3)
        self.assertEqual(updated.count("server.getCapability(Energy.BLOCK, next, null)"),3)

    def test_unknown_new_source_shape_refuses_without_mutating(self):
        original=example().replace("nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())",
            "canConnect(next)")
        result,updated=run(original)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(updated,original)

if __name__=="__main__":unittest.main()
