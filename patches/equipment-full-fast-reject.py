#!/usr/bin/env python3
"""Skip descriptor hashing/validation for a full equipment cell.

No insertion is possible when free()==0; do not decode or hash a potentially
large equipment descriptor on each rapid bulk-insert attempt.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/core/EquipmentCellStore.java"
s=p.read_text()
old="if(n<=0||!EquipmentEligibility.isEquipment(k))return 0;check(k,p);"
new="if(n<=0||free()<=0||!EquipmentEligibility.isEquipment(k))return 0;check(k,p);"
assert s.count(old)==1,"equipment preview insertion anchor changed"
s=s.replace(old,new,1)
assert s.count(new)==1
p.write_text(s)
print("EQUIPMENT_FULL_FAST_REJECT_V1 PASS")
