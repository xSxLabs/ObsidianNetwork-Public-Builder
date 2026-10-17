#!/usr/bin/env python3
from pathlib import Path
import os,shutil
root=Path(os.environ.get('V1_SOURCE_ROOT','work/src/main/java'))/'dev/obsidiannetwork/build103'
root.mkdir(parents=True,exist_ok=True)
source=Path('tests/integration/TerminalMenuGameTests.java')
assert source.is_file()
shutil.copyfile(source,root/source.name)
print('TERMINAL_MENU_TEST_INSTALL_V1 PASS')
