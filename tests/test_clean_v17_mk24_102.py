#!/usr/bin/env python3
"""Build102 static acceptance: 24 matching suit tiers and no duplicated new palettes."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUNDLE=(ROOT/"features/v17/apply-power-armor-bundle-93.py").read_text(encoding="utf-8")
ARMS=(ROOT/"features/v17/apply-power-armor-build98.py").read_text(encoding="utf-8")
JADE=(ROOT/"features/v17/apply-power-armor-jade-95.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
TREE=ast.parse(BUNDLE)

def dictionary(name):
 for node in TREE.body:
  if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id==name for n in node.targets):
   return ast.literal_eval(node.value)
 raise AssertionError(name+" not found")

class AllTiers(unittest.TestCase):
 def test_parse(self):
  for s in (BUNDLE,ARMS,JADE):ast.parse(s)
 def test_existing_colors_preserved_and_new_distinct(self):
  palettes=dictionary("finishes")
  self.assertEqual(set(palettes),set(range(3,25)))
  self.assertEqual(len(palettes),22)
  for tier in range(13,25):
   self.assertTrue(palettes[tier][0] and palettes[tier][1])
   for previous in range(3,tier):
    a,b=palettes[tier],palettes[previous]
    value=sum((x-y)**2 for x,y in zip(a[2],b[2]))**.5+.75*sum((x-y)**2 for x,y in zip(a[3],b[3]))**.5
    self.assertGreater(value,100,(tier,previous))
 def test_new_recipes_all_unique_and_legacy_unmodified(self):
  dyes=dictionary("new_trim_dyes")
  palettes=dictionary("finishes")
  self.assertEqual(set(dyes),set(range(13,25)))
  self.assertEqual(len(set((palettes[t][4],dyes[t]) for t in dyes)),12)
  self.assertIn('pattern=["ABA","CDC","EFE"] if tier>=13 else ["ABA","CDC","AEA"]',BUNDLE)
  self.assertIn('if tier>=13:ingredients["F"]="minecraft:"+new_trim_dyes[tier]',BUNDLE)
 def test_equipping_world_jade_firstperson_and_apotheosis(self):
  for q in (
    "for tier in range(1,25):", "==88","for tier in range(3,25):",
    'new AABB(pad)', "oldArmor.recover(p)",
    'getValue(ArmorStationBlock.FACING)',
    'apoth_data["values"][key]=category',
    'data["minecraft:geometry"][0]["description"]["identifier"]',
    'recolor_png(png.read_bytes(),primary,secondary)'):
   self.assertIn(q,BUNDLE)
  self.assertIn("if(tier<1 || tier>24)return;",JADE)
  self.assertIn("if(tier<1||tier>24)return;",ARMS)
  self.assertIn("for tier in range(1,25):",ARMS)
 def test_ci_integrates_full_check(self):
  self.assertIn("BUILD102_24_FIRST_PERSON_ARM_ASSETS PASS",WF)
  self.assertIn("BUILD102_MK24_SUITS_AND_ASSETS PASS",WF)
if __name__=="__main__":unittest.main()
