#!/usr/bin/env python3
"""Preflight for B1104 freeze-mode restore, fail closed on accidental regression."""
import ast
from pathlib import Path
r=Path(__file__).resolve().parents[1]
wf=(r/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
t=(r/"tests/test_v176_b1104_freeze_entry.py").read_text()
gen=(r/"features/v176/apply-v176-b1103-all-mk-gametest.py").read_text()
ast.parse(t)
assert "python3 features/v176/apply-v176-b1096-entry-visibility-recovery.py" not in wf
assert "python3 features/v176/apply-v176-b1102-critical-entry.py" not in wf
assert wf.index("python3 tests/verify_v175_b662.py")<wf.index("B1104_FROZEN_V175_MANUAL_ENTRY_SNAPSHOTTED")<wf.index("python3 tests/test_v176_b1104_freeze_entry.py")
assert "B1104_FREEZE175_MANUAL_ENTRY_AND_EXIT_EXACT_SOURCE_PASS" in t
assert "if(!inside(p,stand))return;" in t
assert 'B662_HIDE_ON_STEP_IN_BEFORE_REAL_EQUIP' in gen
assert 'B662_REVEAL_ONLY_AFTER_EQUIP_COMPLETE' in gen
assert 'for(int tier=0;tier<24;tier++)' in gen
assert "contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')" in wf
print("B1104_FREEZE175_RESTORATION_PIPELINE_GUARD_PASS")
