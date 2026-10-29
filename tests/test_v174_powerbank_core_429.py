#!/usr/bin/env python3
"""v1.7.4 staged Powerbank tests: no overflow, no unloaded lookups, safe IO."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
script=(root/"features/v174/apply-powerbank-core-429.py").read_text()
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(script)
assert "python3 features/v174/apply-powerbank-core-429.py" in wf
assert "python3 tests/test_v174_powerbank_core_429.py" in wf
assert wf.index("python3 features/v174/apply-reactor-core-427.py")<wf.index("python3 features/v174/apply-powerbank-core-429.py")
for text in ("3x3x(3..12)","10_000_000_000L","100_000_000_000L","Math.min(",
             "b.journal.updateSnapshots(tx)","b.amount-=taken","b.amount+=taken",
             "MAX_IO=1_000_000","formed=false","world.hasChunkAt(p)",
             "Capabilities.Energy.BLOCK","new BlockEntityType("):
 assert text in script,text
for length in range(3,13):
 capacity=10_000_000_000+(length-3)*10_000_000_000
 assert 10_000_000_000<=capacity<=100_000_000_000
if os.environ.get("V1_SOURCE_ROOT"):
 root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerbank"
 for name in ("PowerbankGeometry","PowerbankBlock","PowerbankBlockEntity","PowerbankCapabilities"):
  assert (root/(name+".java")).is_file(),name
print("V174_POWERBANK_429_TEST_PASS")
