#!/usr/bin/env python3
"""Install shared, add-only v1.7.6 backpack, Power Monitor and sleep rules.

Integration tests compile and execute the rule tests before distributable JAR.
The rules do not themselves register or expose world objects.
"""
from pathlib import Path
import os
import shutil
root=Path(__file__).resolve().parent
target=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
rules={
 "V176BackpackRules.java":"backpack",
 "V176BackpackCodec.java":"backpack",
 "V176BackpackItemState.java":"backpack",
 "V176PowerMonitorRules.java":"power",
 "V176PowerSleepRules.java":"powerarmor",
}
for name,directory in rules.items():
 src=root/"java"/name
 dest=target/directory/name
 assert src.is_file(),("V176_RULES_MISSING",name)
 assert not dest.exists(),("V176_RULES_DUPLICATED",str(dest))
 dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dest)
 assert dest.read_bytes()==src.read_bytes()
print("V176_BACKPACK_POWER_MONITOR_SLEEP_RULES_INSTALLED_PASS")
