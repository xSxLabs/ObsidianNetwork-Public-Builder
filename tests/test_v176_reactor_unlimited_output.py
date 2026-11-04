"""v1.7.6 reactor output must not silently revert to a 262144-FE push budget."""
import ast
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
SRC = (R / "features/v176/apply-v176-reactor-unlimited-output.py").read_text("utf-8")
W = (R / ".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class ReactorUnlimitedOutput(unittest.TestCase):
    def test_valid_generator(self):
        ast.parse(SRC)
    def test_removes_262144_push_limit_but_preserves_atomic_fe(self):
        for token in (
            "V176_REACTOR_UNCAPPED_PORT_PUSH",
            "int budget=(int)Math.min((long)Integer.MAX_VALUE,storedFe);",
            "int accepted=sink.insert(budget,tx);",
            "energyPort.extract(accepted,tx)==accepted",
            "tx.commit();",
            "ReactorPortBlockEntity.java",
            "x.extract(n,tx)",
        ):
            self.assertIn(token, SRC)
    def test_applied_after_reactor_and_network_port_integration(self):
        first = W.index("python3 features/v176/apply-v176-network-power-ports.py")
        last = W.index("python3 features/v176/apply-v176-reactor-unlimited-output.py")
        self.assertLess(first, last)

if __name__ == "__main__":
    unittest.main()
