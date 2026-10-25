#!/usr/bin/env python3
"""v1.7.3 wireless receiver status must use its paired TRANSMITTER, not local FE."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v173/apply-wireless-link-status.py").read_text()
BASE=(ROOT/"features/v173/apply-wireless-network-only.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class ReceiverStatusV173(unittest.TestCase):
 def test_python_syntax(self):ast.parse(PATCH)
 def test_original_false_positive_is_patched_exactly(self):
  self.assertIn('return transmitter()?"SOURCE ONLINE":"CONNECTED"',BASE)
  self.assertIn('assert s.count(old)==1',PATCH)
  self.assertIn("NetworkSignalRelayBridge.sourceOnline(world,this)",PATCH)
 def test_link_status_requires_live_matched_source(self):
  for x in ("!rx.paired()","rx.transmitter()","RESOLVING.get()",
            "RESOLVING.set(true)","transmitterRuntime(receiverLevel,rx)",
            "source!=null&&source.powered()","finally{RESOLVING.set(false);}"):
   self.assertIn(x,PATCH)
  for x in ("!tx.owner().equals(rx.owner())",
            "!tx.channel().equals(rx.channel())",
            "rt!=null&&rt.powered()"):
   self.assertIn(x,BASE)
  self.assertIn('if(!cable)return "NO NETWORK CABLE";',PATCH)
  self.assertIn('?"CONNECTED":"NO LIVE TRANSMITTER / SOURCE OFFLINE"',PATCH)
 def test_no_fe_and_applied_after_network_bundle(self):
  self.assertNotIn("EnergyHandler",PATCH)
  self.assertIn("python3 features/v173/apply-wireless-link-status.py",WF)
  self.assertLess(WF.index("python3 features/v173/apply-wireless-network-only.py"),
                  WF.index("python3 features/v173/apply-wireless-link-status.py"))
  self.assertLess(WF.index("python3 features/v173/apply-machine-network-bundle-compat.py"),
                  WF.index("python3 features/v173/apply-wireless-link-status.py"))
  self.assertIn("V173_REAL_WIRELESS_LINK_STATUS_PASS",WF)
if __name__=="__main__":unittest.main()
