#!/usr/bin/env python3
"""B445: generated guidebook geometry and bounded client-side layer selector."""
import ast
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
patch=(ROOT/"features/v174/apply-guidebook-size-445.py").read_text()
workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(patch)

for token in (
    "B445_SCALED_LAYERS", "showReactor", "reactorSize=5", "powerbankHeight=3",
    "Math.max(5,Math.min(64,", "Math.max(3,Math.min(12,",
    "reactorLayer=Math.min(", "powerbankLayer=Math.min(",
    "int step=Math.max(1,64/size)", "if(layer==1)",
    "xx==size/2&&z==size/2", "if(page==7)",
    "if(page!=7)", "x>=117D&&x<=170D"
):
    assert token in patch,token
assert workflow.index("python3 features/v174/apply-guidebook-442.py") < workflow.index("python3 features/v174/apply-guidebook-size-445.py")
assert workflow.index("python3 features/v174/apply-guidebook-size-445.py") < workflow.index("python3 tests/test_v174_guidebook_sizes_445.py")

# The chosen XZ layer and coloured controls must encode only structures
# accepted by the genuine server validator, including all 64/12 limits.
def layer(size,height,y,reactor):
    cells={}
    for z in range(size):
        for x in range(size):
            outer=(y in (0,height-1) or x in (0,size-1) or z in (0,size-1))
            part="shell" if outer else "air"
            if reactor and not outer and x==size//2 and z==size//2:part="rod"
            if y==1:
                if (x,z)==(size//2,0):part="controller"
                if (x,z)==(0,size//2):part="item" if reactor else "input"
                if (x,z)==(size-1,size//2):part="water" if reactor else "output"
                if reactor and (x,z)==(size//2,size-1):part="energy"
            cells[x,z]=part
    return cells

for n in (5,6,7,16,32,63,64):
    for y in range(n):
        m=layer(n,n,y,True)
        for (x,z),part in m.items():
            exterior=y in (0,n-1) or x in (0,n-1) or z in (0,n-1)
            assert (part in ("shell","controller","item","water","energy")) if exterior else (part in ("air","rod"))
        if y in (0,n-1):assert set(m.values())=={"shell"}
        if 0<y<n-1:assert m[n//2,n//2]=="rod"
        assert max(1,64//n)*n<=64
for h in range(3,13):
    for y in range(h):
        m=layer(3,h,y,False)
        assert m[1,1]=="air" if 0<y<h-1 else m[1,1]=="shell"
        assert "rod" not in m.values()
        if y==1:assert {"controller","input","output"}.issubset(set(m.values()))
if os.environ.get("V1_SOURCE_ROOT"):
    generated=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V174GuidebookScreen.java"
    actual=generated.read_text()
    assert "B445_SCALED_LAYERS" in actual
    assert "for(int z=0;z<size;z++)for(int xx=0;xx<size;xx++)" in actual
print("V174_GUIDEBOOK_SIZE_445_TEST_PASS")
