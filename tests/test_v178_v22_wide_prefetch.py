#!/usr/bin/env python3
"""v22 scheduler coverage, bound and reconstructed-source checks."""
import ast, math, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v178/apply-v178-v22-wide-prefetch.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
def offset(i):
    if i==0:return (0,0)
    r=int((math.sqrt(i)+1)/2)
    side=2*r
    k=i-(side-1)**2
    if k<side:return (-r+k,-r)
    if k<2*side:return (r,-r+k-side)
    if k<3*side:return (r-(k-2*side),r)
    return (-r,r-(k-3*side))
class WidePrefetch(unittest.TestCase):
    def test_square_rings_unique_complete(self):
        for r in (2,20,32,80):
            points=[offset(i) for i in range((2*r+1)**2)]
            self.assertEqual(set(points),{(x,z) for x in range(-r,r+1) for z in range(-r,r+1)})
            self.assertEqual(len(points),len(set(points)))
            self.assertEqual(sorted(points,key=lambda p:max(map(abs,p))),points)
    def test_budget_and_artifact(self):
        src=P.read_text("utf-8")
        ast.parse(src)
        for t in ("V22_MAX_RADIUS=80,V22_MIN_RADIUS=32","visible*4","V22_MAX_SAMPLES=12",
                  "V22_BUDGET_NS=2_000_000L","V22_WIDE_PROBES=1024","MAX_CACHED=8192",
                  "known.containsKey(pos(x,z))||!world.hasChunk(x,z)",
                  "v22WideCursor=(i+1)%wideCount","v22LastWorld!=world",
                  "Math.min(16,(int)Math.ceil(speed*2.5D))"):
            self.assertIn(t,src)
        self.assertIn("cp work/build/libs/*.jar dist/xSxLabs-Network-Storage-1.7.8-v22.jar",WF)
        self.assertIn("'xsxlabs-network-storage-1.7.8-v22'",WF)
        self.assertLess(WF.index("test_v178_b1895_miner_gui_layout.py"),
                        WF.index("apply-v178-v22-wide-prefetch.py"))
    def test_reconstructed(self):
        root=os.environ.get("V1_SOURCE_ROOT")
        if not root:self.skipTest("CI reconstructed sources only")
        p=Path(root)/"dev/obsidiannetwork/client/V178TerrainMap.java"
        s=p.read_text("utf-8")
        for t in ("MAX_CACHED=8192","V22_MAX_RADIUS=80","v22Offset(i)",
                  "b1843FillVisible(world,cx,cz,start);","V178MiniRaster.tick(world);",
                  "world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)"):
            self.assertIn(t,s)
if __name__=="__main__":unittest.main()
