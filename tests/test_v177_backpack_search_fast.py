#!/usr/bin/env python3
"""Regression: responsive server-authoritative backpack search, no 1.7.6 drift."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-backpack-search-fast.py").read_text("utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class FastBackpackSearch(unittest.TestCase):
 def test_python_syntax(self):
  ast.parse(PATCH)

 def test_reuse_sorted_base_until_actual_storage_changes(self):
  for needle in (
    "xsxSearchContainer!=content",
    "xsxSearchCableRevision!=liveCableRevision",
    "xsxSearchSource!=live",
    "xsxSearchSort!=countSort",
    "if(xsxRebuildSearch){",
    "new java.util.ArrayList<>(V176BackpackCells.entries(live))",
    "xsxSearchSorted=java.util.List.copyOf(all)",
    "xsxSearchKeys=java.util.List.copyOf(keys)",
    "if(xsxSearchKeys.get(i).contains(query))result.add(xsxSearchSorted.get(i))",
    "cacheEntries=java.util.List.copyOf(result)",
    "if(xsxShiftLayoutFrozen)return xsxShiftEntries;",
    "B1304_REAL_NAME_AZ",
  ):
   self.assertIn(needle,PATCH,needle)
  self.assertLess(PATCH.index("if(xsxRebuildSearch){"),
                  PATCH.index("new java.util.ArrayList<>(V176BackpackCells.entries(live))"))
  self.assertLess(PATCH.index("xsxSearchKeys=java.util.List.copyOf(keys)"),
                  PATCH.index("if(xsxSearchKeys.get(i).contains(query))"))

 def test_network_coalesces_to_last_input_no_extra_packet(self):
  for needle in (
    "searchBox.setResponder(value->xsxQueueSearch(value));",
    "xsxPendingSearch=value;",
    "if(tick==xsxLastSearchPacketTick)return;",
    "String current=xsxPendingSearch;",
    "xsxPendingSearch=null;",
    "command(current.isBlank()?",
    "xsxFlushSearch();",
    "mc.player.containerMenu!=menu",
    "button(192+xsxPendingScroll)",
  ):
   self.assertIn(needle,PATCH,needle)
  self.assertNotIn("CustomPacketPayload",PATCH)
  self.assertNotIn("player.getInventory().add(",PATCH)

 def test_filter_stable_click_conservation_and_scope(self):
  self.assertIn("source.save(updated)",PATCH)
  self.assertIn("xsxShiftVisited.add(id)",PATCH)
  self.assertIn("xsxSyncServerScroll();",PATCH)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)
  order=FLOW.index("python3 features/v176/apply-v176-b1304-backpack-sort-display-names.py")
  search=FLOW.index("python3 features/v177/apply-v177-backpack-search-fast.py")
  self.assertLess(order,search)
  self.assertIn("test_v177_backpack_search_fast.py",FLOW)

if __name__=="__main__":
 unittest.main()
