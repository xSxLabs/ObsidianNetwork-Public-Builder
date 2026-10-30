#!/usr/bin/env python3
"""B476: all inherited WIP blocks/items are included in v1.7.4 ingame build."""
import ast
import json
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
code=(root/"features/v174/apply-wip-public-test-476.py").read_text(encoding="utf-8")
workflow=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
ast.parse(code)
assert "B476_V174_WIP_PUBLIC_TEST_PASS" in code
assert "hidden.unlink()" in code
assert "NETWORK_HOLOGRAM_TERMINAL_ITEM" in code
assert "NETWORK_PRINTER_ITEM" in code
assert "NETWORK_BLUEPRINT" in code
assert "NETWORK_SCHEMATIC_QUILL" in code
assert workflow.index("python3 features/v173/apply-wip-hide-398.py") < workflow.index("python3 features/v174/apply-wip-public-test-476.py")
assert workflow.rindex("python3 features/v174/apply-wip-public-test-476.py") < workflow.rindex("python3 tests/test_v174_wip_public_476.py")
if os.environ.get("V1_SOURCE_ROOT"):
 java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 res=Path(os.environ["V1_RESOURCE_ROOT"])
 src=(java/"ObsidianNetwork.java").read_text()
 for f in ("NETWORK_HOLOGRAM_TERMINAL_ITEM","NETWORK_PRINTER_ITEM",
           "NETWORK_BLUEPRINT","NETWORK_SCHEMATIC_QUILL"):
  assert "output.accept((ItemLike)"+f+".get());" in src
 assert not (java/"compat/jei/WipItemsJeiPlugin.java").exists()
 for name in ("network_hologram_terminal","network_printer","network_schematic_quill"):
  recipe=json.loads((res/"data/obsidiannetwork/recipe"/(name+".json")).read_text())
  assert recipe["result"]["id"]=="obsidiannetwork:"+name
  assert recipe["type"]=="minecraft:crafting_shaped"
 print("B476_V174_WIP_PUBLIC_LIVE_GENERATED_PASS")
print("B476_V174_WIP_PUBLIC_TEST_PASS")
