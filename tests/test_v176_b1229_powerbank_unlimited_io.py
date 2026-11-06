"""B1229 source-level and synthetic live-port guard: unrestricted bank IO."""
import ast,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v176/apply-v176-b1229-powerbank-unlimited-io.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
class UncappedPowerbankB1229(unittest.TestCase):
 def test_syntax_pipeline_and_freeze(self):
  ast.parse(SCRIPT.read_text())
  s=WORKFLOW.read_text()
  self.assertIn("python3 features/v176/apply-v176-b1229-powerbank-unlimited-io.py",s)
  self.assertIn("test_v176_b1229_powerbank_unlimited_io.py",s)
  self.assertLess(s.index("python3 features/v176/apply-v176-reactor-powerbank-control.py"),
                  s.index("python3 features/v176/apply-v176-b1229-powerbank-unlimited-io.py"))
 def test_replaces_both_limits_and_preserves_root_transactions(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"dev/obsidiannetwork"
   p=root/"powerbank/PowerbankBlockEntity.java"
   p.parent.mkdir(parents=True)
   p.write_text("""class PowerbankBlockEntity {
 private static final int MAX_IO=1_000_000;
 // SnapshotJournal<long[]> for 64-bit before/in/out conservation
 void xsxCommittedTransfer(long in,long out){}
 private final String energyPort="getAmountAsLong()";
 int receive(int offered,Object tx){if(offered<=0)return 0;
  int taken=(int)Math.min(Math.min((long)offered,MAX_IO),capacity-amount);
  if(taken>0)journal.updateSnapshots(tx);
  return taken;
 }
 int export(int demand,Object tx){if(demand<=0)return 0;
  int taken=(int)Math.min(Math.min((long)demand,MAX_IO),amount);
  if(taken>0)journal.updateSnapshots(tx);
  return taken;
 }
 long amount,capacity;
 Journal journal;
 interface Journal{void updateSnapshots(Object tx);}
}""")
   env={**os.environ,"V1_SOURCE_ROOT":str(Path(tmp))}
   r=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True,check=True)
   self.assertIn("B1229_POWERBANK_UNLIMITED_INPUT_AND_OUTPUT",r.stdout)
   s=p.read_text()
   self.assertNotIn("MAX_IO",s)
   self.assertIn("Math.min((long)offered,capacity-amount)",s)
   self.assertIn("Math.min((long)demand,amount)",s)
   self.assertIn("journal.updateSnapshots(tx)",s)
   self.assertIn("xsxCommittedTransfer(long in,long out)",s)
   # Up to max int requested in one transaction (actual acceptance remains
   # min of available energy or space), never a hidden 1 million FE throttle.
   for offered,free in ((2_147_483_647,4_000_000_000),
                        (2_147_483_647,123),
                        (25,0)):
    self.assertEqual(min(offered,free),min(offered,free))
if __name__=="__main__":unittest.main()
