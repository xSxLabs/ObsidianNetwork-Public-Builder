#!/usr/bin/env python3
"""B1229: lift artificial Powerbank FE ingress/egress limits.

The NeoForge EnergyHandler API takes a signed int per single transaction.
Allow up to that requested amount at BOTH ports, bounded only by real stored
FE / unused capacity and the connected endpoint's acceptance. Keep the
existing root transaction journal, throughput telemetry, controller
enable/formed checks and saved 64-bit energy balance unchanged.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerbank/PowerbankBlockEntity.java"
s=p.read_text(encoding="utf-8")
assert "SnapshotJournal<long[]>" in s,"B1229_POWERBANK_TRANSACTION_JOURNAL_LOST"
assert "xsxCommittedTransfer(" in s,"B1229_POWERBANK_IO_RATE_TRACKING_LOST"
assert "journal.updateSnapshots(tx)" in s,"B1229_POWERBANK_TRANSACTION_BOUNDARY_LOST"
# The original B429 limit is 1,000,000 FE per individual input/output call,
# independent of available storage. Remove it after all older patches.
hits={}
for variable in ("offered","demand"):
 pattern=r"Math\.min\(\s*\(long\)"+variable+r"\s*,\s*MAX_IO\s*\)"
 s,n=re.subn(pattern,"(long)"+variable,s)
 hits[variable]=n
assert hits=={"offered":1,"demand":1},("B1229_POWERBANK_MAX_IO_EXPRESSION_DRIFT",hits)
# Reject any second transfer throttle silently left behind.
remaining=re.findall(r"\bMAX_IO\b",s)
assert len(remaining)==1,("B1229_ADDITIONAL_BANK_RATE_CAP",len(remaining))
s,n=re.subn(r"(?m)^ private static final int MAX_IO=1_000_000;\s*\n","",s)
assert n==1,("B1229_POWERBANK_MAX_IO_CONSTANT_DRIFT",n)
assert "MAX_IO" not in s
for var in ("offered","demand"):
 assert f"(long){var}" in s
assert "Math.min" in s and "getAmountAsLong()" in s
p.write_text(s,encoding="utf-8")
print("B1229_POWERBANK_UNLIMITED_INPUT_AND_OUTPUT_REAL_64BIT_CAPACITY_API_INT_MAX_PASS")
