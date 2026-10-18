#!/usr/bin/env python3
"""Fail-closed report for real 10/50/100 Wireless FE GameTests (not Spark/MSPT).

The CI logs contain exact per-density transmitter+EnergyCell balances after
tick-driven transfer. Reject missing, duplicated, negative, truncated, and
synthetically echoed claims; keep Curios-present and absent results separate.
"""
import argparse
import json
import re
from pathlib import Path

RECORD=re.compile(r"\bWIRELESS_DENSE_REAL_SERVER_(10|50|100)_V1 PASS total=(\d+) sink=(\d+)\b")
IDLE="WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS"

def verify(log: str) -> dict:
    values={}
    idle=0
    for line in log.splitlines():
        if "System.out.println" in line or "grep -Fq" in line or "\x1b[" in line:
            continue
        match=RECORD.search(line)
        if match:
            count,total,sink=map(int,match.groups())
            if count in values:
                raise ValueError(f"Duplicate Wireless density phase {count}")
            if total!=count*256_000 or sink<=0 or sink>total:
                raise ValueError(f"Invalid real FE conservation for {count}: total={total}, sink={sink}")
            values[count]={"transmitters":count,"receivers":count,"total_fe":total,
                           "received_fe":sink,"wireless_active":True}
        if IDLE in line:
            idle+=1
    if set(values)!={10,50,100} or idle!=1:
        raise ValueError(f"Incomplete wireless density test phases: {sorted(values)}, idle={idle}")
    return {"phases":[values[k] for k in (10,50,100)],
            "idle_after_100_pass":True,
            "scope":"Real GameTest FE conservation for loaded blocks; NOT Spark, p95/p99 MSPT or an A/B benchmark"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--without-curios",type=Path,required=True)
    p.add_argument("--with-curios",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report={"without_curios":verify(args.without_curios.read_text()),
            "with_curios":verify(args.with_curios.read_text())}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("WIRELESS_DENSITY_REPORT_VALIDATED_V1 PASS")

if __name__=="__main__":
    main()
