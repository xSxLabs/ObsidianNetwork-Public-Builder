#!/usr/bin/env python3
"""Copy validated pure Java Micro-MG rules into reconstructed NeoForge 26.1 source."""
import os,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
dest=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/V176MicroMgRules.java"
assert not dest.exists(),("V176_DUPLICATE_CORE_CLASS",str(dest))
src=root/"java/V176MicroMgRules.java"
assert src.is_file()
dest.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(src,dest)
assert dest.read_bytes()==src.read_bytes()
print("V176_MICRO_MG_JAVA_RULES_INSTALLED PASS")
