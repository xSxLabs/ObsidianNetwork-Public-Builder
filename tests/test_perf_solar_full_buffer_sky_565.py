#!/usr/bin/env python3
"""B565 fail-closed solar hotpath and FE-preservation checks."""
import ast,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"patches/spark-solar-full-buffer-sky-fastpath-565.py"
class SolarFullBufferFastpath(unittest.TestCase):
 def test_shape(self):
  s=SCRIPT.read_text(encoding="utf8")
  ast.parse(s)
  for needle in ("B536_SOLAR_MSPT_FACE_MASK","B547_SOLAR_SPARSE_FACE_WALK",
     "XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1","XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1",
     "be.energy.stored() < be.energy.capacity()","server.canSeeSky(pos.above())",
     "be.energyJournal.updateSnapshots(tx);","tx.commit();","budget -= accepted;",
     "B565_SOLAR_FULL_BUFFER_SKY_FASTPATH"):
   self.assertIn(needle,s)
  self.assertNotIn("return; // B565",s)
 def test_generation_identical_all_tiers_and_sky_cases(self):
  for rate in (640,1280,2560,5120):
   for capacity in (rate,rate*20,rate*100):
    for stored in (0,1,capacity-rate,capacity-1,capacity):
     for visible in (False,True):
      for day in (False,True):
       old=min(rate,capacity-stored) if visible and day else 0
       new=min(rate,capacity-stored) if stored<capacity and visible and day else 0
       self.assertEqual(old,new,(rate,capacity,stored,visible,day))
 def test_real_patch_and_duplicate_fails_closed(self):
  src="""// B536_SOLAR_MSPT_FACE_MASK
// B547_SOLAR_SPARSE_FACE_WALK
// XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1
// XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1
if (server.isDay() && server.canSeeSky(pos.above())) {
 long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());
}
long budget = be.energy.stored();
if (budget > 0L && be.xsxLiveSolarFaces(server)!=0) {
 int start = be.nextSide++ % sides.length;
 be.energyJournal.updateSnapshots(tx);
 long extracted = be.energy.extract(accepted);
 tx.commit();
 budget -= accepted;
}
"""
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
   p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text(src)
   env=dict(os.environ,V1_SOURCE_ROOT=d)
   subprocess.run([sys.executable,str(SCRIPT)],env=env,check=True,capture_output=True,text=True)
   modified=p.read_text()
   self.assertEqual(modified.count("B565_SOLAR_FULL_BUFFER_SKY_FASTPATH"),1)
   self.assertIn("stored() < be.energy.capacity() && server.canSeeSky(pos.above())",modified)
   self.assertIn("long budget = be.energy.stored();",modified)
   self.assertIn("tx.commit();",modified)
   bad=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertNotEqual(bad.returncode,0)
   self.assertEqual(p.read_text(),modified)
if __name__=="__main__":unittest.main()
