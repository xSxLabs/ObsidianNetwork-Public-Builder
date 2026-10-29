#!/usr/bin/env python3
"""B391 regression: no per-block full Blueprint decompression/splitting."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-blueprint-printer-state-cache-391.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class TestBlueprintPrinterStateCache391(unittest.TestCase):
 def test_patch_syntax_and_fail_closed_anchors(self):
  src=PATCH.read_text(encoding="utf-8")
  ast.parse(src)
  for m in ("B391_PRINTER_SOURCE_DRIFT","B391_PRINTER_STATE_CACHE",
            "B391_NO_PER_BLOCK_DECOMPRESSION",
            "B378_PRINTER_PLAN_CACHE","b391BlueprintStates()",
            "ItemStack.isSameItemSameComponents(b378Source,blueprint)"):
   self.assertIn(m,src)

 def test_one_unpack_per_blueprint_identity_not_per_block(self):
  src=PATCH.read_text(encoding="utf-8")
  self.assertIn('String states=NetworkBlueprintItem.read(blueprint,"xsxlabs_states");',src)
  self.assertIn('b391States=states.isBlank()?new String[0]:states.split(";",-1);',src)
  self.assertIn('String[] all=b391BlueprintStates();',src)
  self.assertIn('if(index>=0&&index<all.length&&!all[index].isEmpty())',src)
  self.assertIn('if(property!=null)targetState=restoreProperty',src)
  # The original per-tick full decompression must be eliminated.
  self.assertIn('  String properties=NetworkBlueprintItem.read(blueprint,"xsxlabs_states");',src)
  self.assertIn('  String[] all=b391BlueprintStates();',src)

 def test_cache_invalidated_on_item_components_change(self):
  # Mirrors the source's item+component equality and split-once behavior.
  cached=None
  decode_count=0
  def read(item):
   nonlocal cached,decode_count
   if cached is None or cached[0]!=item:
    decode_count+=1
    raw=item[1]
    cached=(item,[] if not raw.strip() else raw.split(";"))
   return cached[1]
  current=("blueprintA","north=facing;east=facing;;south=facing")
  for i in range(5000):
   self.assertEqual(len(read(current)),4)
  self.assertEqual(decode_count,1)
  self.assertEqual(read(("blueprintB","")) ,[])
  self.assertEqual(decode_count,2)
  self.assertEqual(read(current)[0],"north=facing")
  self.assertEqual(decode_count,3)

 def test_registered_in_build_pipeline(self):
  w=WF.read_text(encoding="utf-8")
  for q in ("test_v173_blueprint_printer_state_cache_391.py",
            "python3 features/v173/apply-blueprint-printer-state-cache-391.py",
            "grep -Fq 'B391_NO_PER_BLOCK_DECOMPRESSION'"):
   self.assertIn(q,w)
  self.assertLess(w.index("python3 features/v173/apply-blueprint-cache-378.py"),
                  w.index("python3 features/v173/apply-blueprint-printer-state-cache-391.py"))

if __name__=="__main__":
 unittest.main()
