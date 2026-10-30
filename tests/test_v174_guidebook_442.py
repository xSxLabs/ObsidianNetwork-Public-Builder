#!/usr/bin/env python3
"""Build442 guidebook: min-size layer coverage, page navigation, real use."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
patch=(root/"features/v174/apply-guidebook-442.py").read_text()
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(patch)
for text in ("Multiblock Guidebook","GUIDEBOOK_USE","xSxLabs Multiblock Guidebook",
 "public InteractionResult use(Level world,Player player,InteractionHand hand)",
 "mouseClicked(MouseButtonEvent e,boolean doubleClick)","getLeftPos()",
 "page=(page+PLAN.length-1)%PLAN.length","page=(page+1)%PLAN.length",
 "POWERBANK 3x3x3","REACTOR 5x5x5",'"##C##","#...#","I.R.W","#...#","##E##"',
 "3x3x3..12","sides 5..64","new SimpleContainer(27)"):
 assert text in patch,text
for text in ("python3 features/v174/apply-guidebook-442.py","python3 tests/test_v174_guidebook_442.py"):
 assert text in wf,text
assert wf.index("python3 features/v174/apply-nutrition-438.py")<wf.index("python3 features/v174/apply-guidebook-442.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 for f in ("guide/NetworkGuidebookItem.java","guide/NetworkGuidebookMenu.java","client/V174GuidebookScreen.java"):
  assert (j/f).is_file(),f
 assert 'case "feeding"' in (j/"powerarmor/PowerArmorCards.java").read_text()
print("V174_GUIDEBOOK_442_TEST_PASS")
