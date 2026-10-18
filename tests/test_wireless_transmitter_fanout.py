#!/usr/bin/env python3
"""Regression: uncapped TX intake/withdrawal, unchanged 64k receiver budget,
and game-test injection for a single TX serving eight separate receivers.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "features/wireless-energy/apply-wireless-unlimited-transmitter.py"
INJECT = ROOT / "features/wireless-energy/inject-wireless-one-tx-eight-rx-gametest.py"


class TransmitterFanoutTest(unittest.TestCase):
    def test_python_sources_parse(self):
        ast.parse(PATCH.read_text())
        ast.parse(INJECT.read_text())

    def test_one_tx_unlimited_int_request_receivers_keep_64k(self):
        fixture = """public static final long CAPACITY=1000000L;
private static final int MAX_TRANSFER=320000;
int taken=(int)Math.min(Math.min(stored,(long)requested),MAX_TRANSFER);
int accepted=(int)Math.min((long)amount,Math.min(CAPACITY-stored,MAX_TRANSFER));
return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,MAX_TRANSFER),tx);
int remainingBudget=Math.min(MAX_TRANSFER,64000);
if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}
handler.journal.updateSnapshots(tx);
journal.updateSnapshots(tx);stored+=accepted;
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            file = root / "dev/obsidiannetwork/blockentity/WirelessNetworkBlockEntity.java"
            file.parent.mkdir(parents=True)
            file.write_text(fixture)
            env = {**os.environ, "V1_SOURCE_ROOT": str(root)}
            result = subprocess.run([sys.executable, str(PATCH)], env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("WIRELESS_UNLIMITED_TX_THROUGHPUT_V1 PASS", result.stdout)
            changed = file.read_text()
            self.assertIn("CAPACITY=64000000L", changed)
            self.assertIn("int taken=(int)Math.min(stored,(long)requested);", changed)
            self.assertIn("int accepted=(int)Math.min((long)amount,CAPACITY-stored);", changed)
            self.assertIn("networkId,Math.min(amount,64000),tx)", changed)
            self.assertIn("int remainingBudget=Math.min(MAX_TRANSFER,64000);", changed)
            self.assertIn("tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;", changed)
            self.assertNotIn("requested),MAX_TRANSFER)", changed)
            self.assertNotIn("CAPACITY-stored,MAX_TRANSFER)", changed)
            rerun = subprocess.run([sys.executable, str(PATCH)], env=env,
                                   text=True, capture_output=True)
            self.assertNotEqual(rerun.returncode, 0, "duplicate patch must fail closed")

    def test_game_test_injection_exact_and_preserves_chunk_cleanup(self):
        fixture = """                     for(int cx=260;cx<=262;cx++)for(int cz=260;cz<=262;cz++)
                      world.setChunkForced(cx,cz,false);
                     System.out.println("WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS");
                   })
                   .thenSucceed();"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            file = root / "dev/obsidiannetwork/build103/Build103GameTests.java"
            file.parent.mkdir(parents=True)
            file.write_text(fixture)
            env = {**os.environ, "V1_SOURCE_ROOT": str(root)}
            result = subprocess.run([sys.executable, str(INJECT)], env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            result_java = file.read_text()
            self.assertIn("WIRELESS_ONE_TX_EIGHT_RX_V1 PASS", result_java)
            self.assertIn("singleTx.energyHandler().insert(512000,funding)==512000", result_java)
            self.assertIn("i<8", result_java)
            self.assertIn("sink.stored()>0", result_java)
            self.assertIn("conservation==512000L", result_java)
            self.assertIn("world.setChunkForced(cx,cz,false)", result_java)
            self.assertIn('WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS', result_java)
            self.assertEqual(result_java.count(".thenSucceed();"), 1)
            self.assertNotEqual(subprocess.run([sys.executable, str(INJECT)], env=env,
                               capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
