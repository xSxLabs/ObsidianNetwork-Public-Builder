#!/usr/bin/env python3
"""Static preflight of source-only P0 fix and full original GameTest wiring."""
import ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/"features/v176/apply-v176-b1102-critical-entry.py").read_text()
w=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
prior=(root/"features/v176/apply-v176-b1096-entry-visibility-recovery.py").read_text()
ast.parse(s)
for token in ("isEnteringOriginal1102(ServerPlayer player,ArmorStand suit)",
 "transitionStarted=PowerArmorSuitWorld.isEnteringOriginal1102(p,stand);",
 "B1102_REAL_TRANSFER_NOT_STARTED","B1102_REAL_SUIT_MUST_REMAIN_VISIBLE",
 "B1102_PLAYER_MUST_REMAIN_VISIBLE","if(!transitionStarted){"):
 assert token in s,token
assert "restoreFailedSuit1096(p,stand)" in prior
assert w.index("apply-v176-b1096-entry-visibility-recovery.py")<w.index("apply-v176-b1102-critical-entry.py")
assert "python3 tests/test_v176_b1102_critical_entry.py" in w
assert "contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')" in w
print("B1102_HOTFIX_PREBUILD_REGRESSION_PASS")
