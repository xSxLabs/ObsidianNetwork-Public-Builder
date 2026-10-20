#!/usr/bin/env python3
"""Skip redundant craft-slot setter dispatches in StorageTerminalMenu.

Only skip exact item+component+count matches. The authoritative BE getter is
used, so externally changed persistent craft grids still synchronize.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_TERMINAL_NINE_SLOT_DISPATCH_ELISION_V1"
assert marker not in s
a=re.search(r"\bpublic\s+void\s+slotsChanged\s*\(\s*Container\b",s)
b=re.search(r"\bpublic\s+int\s+recipeChoiceCount\s*\(",s)
assert a and b and a.start()<b.start()
body=s[a.start():b.start()]
pat=re.compile(r"(?P<target>(?:this\.)?[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.setCraftItem\(\s*(?P<index>[A-Za-z_]\w*)\s*,\s*(?P<stack>[^;]+?)\s*\);")
matches=list(pat.finditer(body))
assert len(matches)==1,("Expected exactly one craft-grid setter loop",len(matches))
m=matches[0]
target,index,stack=m.group("target","index","stack")
assert "getItem(" in stack,(target,index,stack)
assert "craftSlots" in body,(target,index,stack)
assert target not in ("this","super"),"Unexpected setter owner"
replacement=(
    "// "+marker+"\n"
    "         // Compare the authoritative persisted stack before dispatching a transaction.\n"
    "         if (!ItemStack.matches("+target+".getCraftItem("+index+"), "+stack+"))\n"
    "            "+m.group(0)
)
body=body[:m.start()]+replacement+body[m.end():]
assert body.count(marker)==1
assert body.count("setCraftItem(")==1
s=s[:a.start()]+body+s[b.start():]
p.write_text(s,encoding="utf-8")
print("TERMINAL_NINE_SLOT_DISPATCH_ELISION_V1 PASS")
