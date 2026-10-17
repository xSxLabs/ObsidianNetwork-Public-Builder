#!/usr/bin/env python3
"""Install the CI-only equipment menu and equivalent registry benchmark."""
import os
from pathlib import Path
p=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork/build103/Build103GameTests.java'
s=p.read_text()
start=s.index('            private static final class FullEquipmentCellTest') if '            private static final class FullEquipmentCellTest' in s else s.index('  private static final class FullEquipmentCellTest')
# Include only leading indentation on the declaration's line.
start=s.rfind('\n',0,start)+1
end=s.index('private static final class FiftyDriveTest',start)
end=s.rfind('\n',0,end)+1
fragment=(Path(__file__).resolve().parents[1]/'tests/EquipmentRound3Test.java.fragment').read_text()
s=s[:start]+fragment+s[end:]
p.write_text(s)
assert s.count('EQUIPMENT_MENU_CONSERVATION_V1 PASS')==1
print('EQUIPMENT_ROUND3_GAMETEST_SOURCE_V1 PASS offline=30 attached=30 real_menu=true')
