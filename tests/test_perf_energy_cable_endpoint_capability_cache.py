#!/usr/bin/env python3
"""Fail-closed fixtures for NeoForge ENERGY cable endpoint capability caches."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH=Path(__file__).resolve().parents[1]/"patches/spark-energy-cable-endpoint-capability-cache.py"
CLS="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
PAIR=lambda role: (
    "EnergyHandler "+role+" = (EnergyHandler)server.getCapability(Energy.BLOCK, next, nextState, null, side.getOpposite());\n"
    "                        if ("+role+" == null) {\n"
    "                           "+role+" = (EnergyHandler)server.getCapability(Energy.BLOCK, next, nextState, null, null);\n"
    "                        }"
)

def fixture():
    preamble = ("// XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1\n"
                "// XSXLABS_SPARK_BFS_PRIMITIVE_VISITED_V1\n"+CLS+"\n")
    def body(role, method, suffix):
        return (
            f"   public {method} {{\n"
            "      while (cableBudget-- > 0) {\n"
            "         BlockState nextState = server.getBlockState(next);\n"
            "         if (energyOpen(server,cable,side)) {}\n"
            "                        "+PAIR(role)+"\n"
            "                        "+suffix+"\n"
            "                        if (var18 == 0) break;\n"
            "      }\n"
            "   }\n"
        )
    return (preamble
        +body("source","long getAmountAsLong()","source.getAmountAsLong();")
        +body("source","int extract(int amount, TransactionContext transaction)","source.extract(var18,transaction);")
        +body("target","int insert(int amount, TransactionContext transaction)","target.insert(var18,transaction);")
        +"   private final class CableEnergyHandler implements EnergyHandler {}\n"
        +"}\n")

def run(src):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
        p.parent.mkdir(parents=True)
        p.write_text(src)
        result=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
            env={**os.environ,"V1_SOURCE_ROOT":str(d)})
        return result,p.read_text()

class EnergyCableCacheTest(unittest.TestCase):
    def test_replaces_exactly_three_endpoint_lookups_without_altering_transfer(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        original=fixture()
        result,patched=run(original)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1 PASS",result.stdout)
        self.assertEqual(patched.count("liveBoundaryEnergy(server, cable, side, next, nextState)"),3)
        self.assertIn("cachedEnergyEndpoint(server, side)",patched)
        self.assertEqual(patched.count("BlockCapabilityCache.create("),2)
        self.assertIn("() -> !isRemoved() && level == server",patched)
        self.assertIn("clearEnergyEndpointCaches();",patched)
        self.assertIn("public void onLoad()",patched)
        self.assertIn("public void setRemoved()",patched)
        self.assertIn("server.getBlockEntity(cable)",patched)
        self.assertIn("if (cable.equals(worldPosition))",patched)
        self.assertIn("side.getOpposite()",patched)
        self.assertIn("worldPosition.relative(side)",patched)
        self.assertIn("nextState, null, null)",patched)
        self.assertIn("source.extract(var18,transaction);",patched)
        self.assertIn("target.insert(var18,transaction);",patched)
        self.assertEqual(patched.count("energyOpen("),original.count("energyOpen("))
        self.assertEqual(patched.count("while (cableBudget-- > 0)"),3)
        self.assertEqual(patched.count("BlockState nextState = server.getBlockState(next);"),3)
        self.assertEqual(patched.count("if (var18 == 0) break;"),3)
        failed,result_again=run(patched)
        self.assertNotEqual(failed.returncode,0)
        self.assertEqual(result_again,patched)

    def test_partial_or_wrong_source_fails_without_modifying_file(self):
        old=fixture()
        for modified in (
            old.replace("nextState, null, null","nextState, null, side",1),
            old.replace("XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1","removed"),
            old.replace("source.extract(var18,transaction);","wrong.extract(var18,transaction);"),
            old.replace(CLS,CLS+"\n   public void onLoad() {}"),
        ):
            with self.subTest(src=modified[:90]):
                result,after=run(modified)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(after,modified)

    def test_no_energy_or_topology_semantic_shortcuts(self):
        code=PATCH.read_text()
        self.assertNotIn("setChunkForced(",code)
        self.assertIn('assert s.count("Transaction.openRoot()")',code)
        self.assertNotIn("tx.commit()",code)
        self.assertNotIn("setDamageValue(",code)
        self.assertIn("Null-sided fallback",code)
        self.assertIn("capability resolution",code)
        self.assertIn("segment.worldPosition.equals(cable)",code)

if __name__=="__main__":
    unittest.main()
