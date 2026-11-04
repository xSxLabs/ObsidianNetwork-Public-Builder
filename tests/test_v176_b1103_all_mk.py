#!/usr/bin/env python3
import ast
from pathlib import Path
r=Path(__file__).resolve().parents[1]
g=(r/"features/v176/apply-v176-b1103-all-mk-gametest.py").read_text()
w=(r/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(g)
for required in ("range(1,25)","for(int tier=0;tier<24;tier++)","Real MK1-MK24 Power Armor conservation roundtrip",
                 "B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP","B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE","protection5_roundtrip=true"):
 assert required in g,required
assert "python3 features/v176/apply-v176-b1102-critical-entry.py" not in w
assert "python3 features/v176/apply-v176-b1096-entry-visibility-recovery.py" not in w
assert w.index("python3 tests/verify_v175_b662.py") < w.index("apply-v176-b1103-all-mk-gametest.py")
assert "python3 tests/test_v176_b1103_all_mk.py" in w
assert "B1103_ALL_24_MK_REAL_ROUNDTRIP_BOTH_CURIOS_MODES_PASS" in w
assert "contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')" in w
print("B1103_ALL_24_MK_TEST_WIRING_PASS")
