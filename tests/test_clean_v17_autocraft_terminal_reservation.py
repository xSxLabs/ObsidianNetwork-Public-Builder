#!/usr/bin/env python3
"""Eager autocrafting reservation / terminal availability conservation tests."""
from dataclasses import dataclass
from pathlib import Path
import os,random,subprocess,sys,tempfile,unittest
PATCH=Path(__file__).resolve().parents[1]/"patches/autocraft-eager-terminal-reservation-v17.py"
REL="dev/obsidiannetwork/platform/MinecraftAutocraftingService.java"
SOURCE="""class MinecraftAutocraftingService {
 void queue() {
  long taken = this.runtime.storage().extract(e.getKey(), Math.min(e.getValue(),perCraftNeeds.getOrDefault(e.getKey(),0L)));
  this.queueMissingDependencies(level, t, needs, reserved);
 }
 void refill() {
  long missing = Math.max(0L, Math.min(b.perCraft() - b.buffered(), b.target() - b.buffered()));
  long taken = missing > 0L ? this.runtime.storage().extract(b.descriptor().key(), missing) : 0L;
 }
 void cancel() {
  if (!this.canRestoreReserved(c.reserved())) return;
  this.restoreReserved(c.reserved());
  it.remove();
 }
 boolean canRestoreReserved() { return this.runtime.storage().previewInsertExact(key, payload, qty)>0; }
 void restoreReserved() {
  long restored = this.runtime.storage().insertExact(key,payload,qty);
  if (restored != b.buffered()) throw new IllegalStateException("bad");
 }
 void save() { out.writeLong(b.perCraft()); out.writeLong(b.buffered()); }
 void load() { long perCraft = version >= 6 ? in.readLong() : 0L; }
}
"""
def apply(source):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/REL;p.parent.mkdir(parents=True);p.write_text(source)
  res=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":d},text=True,capture_output=True)
  return res,p.read_text()

@dataclass
class Job:
 need:int
 held:int=0
 done:int=0
 def reserve(self,stock):
  take=min(max(0,self.need-self.held),stock)
  self.held+=take
  return stock-take
 def consume(self,amount):
  assert 0<=amount<=self.held
  self.held-=amount;self.need-=amount;self.done+=amount

class TestTerminalReservation(unittest.TestCase):
 def test_fail_closed_patch_matches_existing_runtime_contract(self):
  result,source=apply(SOURCE)
  self.assertEqual(0,result.returncode,result.stderr)
  self.assertIn("XSXLABS_AUTOCRAFT_EAGER_PRIVATE_RESERVATIONS_V17",source)
  self.assertIn("Math.min(e.getValue(), available)",source)
  self.assertIn("Math.min(missing, stock)",source)
  self.assertNotIn("Math.min(b.perCraft() - b.buffered(),",source)
  self.assertIn("this.restoreReserved(c.reserved())",source)
 def test_source_drift_rejected_without_edit(self):
  for drift in ["this.restoreReserved(c.reserved());","out.writeLong(b.buffered());","this.queueMissingDependencies(level, t, needs, reserved);"]:
   bad=SOURCE.replace(drift,"// removed",1)
   result,after=apply(bad)
   self.assertNotEqual(0,result.returncode)
   self.assertEqual(bad,after)
 def test_all_usable_items_disappear_then_return_on_cancel(self):
  for available,needed in [(64,40),(11,40),(40,40),(0,40),(500,5)]:
   job=Job(needed)
   visible=job.reserve(available)
   self.assertEqual(max(0,available-needed),visible)
   # new items delivered while job waits are hidden by subsequent refill
   visible+=17
   visible=job.reserve(visible)
   self.assertEqual(max(0,available+17-needed),visible)
   visible+=job.held # guarded successful cancellation restores exact held quantity
   self.assertEqual(available+17,visible)
 def test_randomized_cancel_and_partial_craft_conservation(self):
  rng=random.Random(170026)
  for _ in range(10000):
   stock=rng.randrange(0,400);job=Job(rng.randrange(1,400));created=stock
   stock=job.reserve(stock)
   for tick in range(rng.randrange(0,8)):
    new=rng.randrange(0,50)
    stock+=new;created+=new
    stock=job.reserve(stock)
    if job.held and rng.randrange(3)==0:
     job.consume(min(job.held,job.need,rng.randrange(1,20)))
    self.assertEqual(created,stock+job.held+job.done)
   stock+=job.held
   self.assertEqual(created,stock+job.done)
if __name__=="__main__": unittest.main()
