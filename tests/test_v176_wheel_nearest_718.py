#!/usr/bin/env python3
"""B718 Action Wheel chooses nearest owner-authenticated suit."""
# B718 final complete-package verification: original v1.7.5 transitions unchanged.
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-wheel-nearest-718.py"
class NearestCompanionTest(unittest.TestCase):
 def test_multiple_own_suits(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"dev/obsidiannetwork/client/V176CompanionClient.java"
   path.parent.mkdir(parents=True)
   path.write_text(''' // exact owner identity
 "xsxlabs_v176_owner_"+mc.player.getUUID()
  return stands.size()==1?stands.get(0):null;''')
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   r=subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True,env=env)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   code=path.read_text()
   self.assertNotIn("stands.size()==1",code)
   self.assertIn("stands.stream().min(",code)
   self.assertIn("stand.distanceToSqr(mc.player)",code)
   self.assertIn("xsxlabs_v176_owner_",code)
   r=subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True,env=env)
   self.assertNotEqual(r.returncode,0)
if __name__=="__main__":unittest.main()
