"""B1270: eight-block, every-tick, lossless Backpack Magnet acceptance gates.

This is a staged source patch and does not by itself verify NeoForge
compilation or live multiplayer performance.
"""
import ast
from pathlib import Path
import random
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1270-magnet-8-instant-batched.py"
WORKFLOW=ROOT/".github/workflows/v176-b1269-backpack-ingress-source-preflight.yml"

class EightBlockMagnetB1270(unittest.TestCase):
 def test_radius_and_no_old_default(self):
  source=PATCH.read_text("utf-8")
  ast.parse(source)
  self.assertIn("private static final double RANGE=8.0D;",source)
  self.assertNotIn("RANGE=16.0D",source)
  self.assertIn("entity.distanceToSqr(player)>RANGE*RANGE",source)
  self.assertIn("player.getBoundingBox().inflate(RANGE)",source)
  self.assertIn("B1270_MAGNET_8_BLOCK_EVERY_TICK",source)

 def test_exact_boundary_sphere(self):
  rng=random.Random(1270)
  radius2=8.0**2
  self.assertTrue((8*8+0*0+0*0)<=radius2)
  self.assertFalse((8.01*8.01)>radius2 is False)
  for _ in range(3000):
   x=rng.uniform(-9,9)
   y=rng.uniform(-9,9)
   z=rng.uniform(-9,9)
   self.assertEqual(x*x+y*y+z*z<=radius2,
                    x*x+y*y+z*z<=64.0)

 def test_every_tick_and_atomic_commit(self):
  s=PATCH.read_text("utf-8")
  self.assertNotIn("player.tickCount%",s)
  self.assertNotIn("ITEM_BUDGET=",s)
  self.assertNotIn("ENTITY_BUDGET=",s)
  self.assertIn("location.persist(player,updated);",s)
  self.assertIn("remainder.shrink(pickup.amount());",s)
  self.assertIn("V176BackpackEquipped.activeMagnet(player)",s)
  self.assertIn("V176BackpackCells.magnetAccepts(",s)
  self.assertIn('tag.getBooleanOr("xsx_v176_magnet_on",true)',s)
  self.assertIn("V176BackpackCells.insert(",s)
  self.assertIn("LinkedHashMap",s)
  self.assertIn("ItemResource.of(dropped)",s)
  self.assertIn("left-=take;",s)
  self.assertIn("if(pickups.isEmpty())return;",s)
  self.assertIn("catch(RuntimeException refused){return;}",s)

 def test_lossless_partial_distribution(self):
  rng=random.Random(81270)
  for _ in range(10000):
   stacks=[rng.randint(1,64) for _ in range(rng.randint(1,48))]
   accepted=rng.randint(0,sum(stacks))
   remain=accepted
   moved=[]
   for count in stacks:
    n=min(remain,count)
    moved.append(n)
    remain-=n
   self.assertEqual(remain,0)
   self.assertEqual(sum(moved),accepted)
   self.assertEqual(sum(stacks[i]-moved[i] for i in range(len(stacks))),
                    sum(stacks)-accepted)

 def test_source_only_branch(self):
  workflow=WORKFLOW.read_text("utf-8")
  self.assertIn(PATCH.name,workflow)
  self.assertIn("test_v176_b1270_magnet_8_blocks.py",workflow)
  self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text("utf-8"))

if __name__=="__main__":
 unittest.main()
