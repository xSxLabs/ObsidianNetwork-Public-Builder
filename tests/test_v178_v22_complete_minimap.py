#!/usr/bin/env python3
"""v22: no incomplete minimap texture; exact centered zoom coverage."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v178/apply-v178-v22-complete-minimap.py"
def covered(x,z,crop,known):
    left,top=x-crop//2,z-crop//2
    return all((cx,cz) in known
               for cz in range(top//16,(top+crop-1)//16+1)
               for cx in range(left//16,(left+crop-1)//16+1))
def safe(x,z,requested,known):
    lo,hi=0,requested
    while lo<hi:
        mid=lo+(hi-lo+1)//2
        if covered(x,z,mid,known):lo=mid
        else:hi=mid-1
    return lo
class CompleteMap(unittest.TestCase):
    def test_no_holes_maximal_centered_crop(self):
        known={(x,z) for x in range(-5,6) for z in range(-5,6)}
        known.remove((3,1))
        for x,z in ((0,0),(15,15),(-1,-1),(-16,16)):
            n=safe(x,z,624,known)
            self.assertGreater(n,16)
            self.assertTrue(covered(x,z,n,known))
            self.assertFalse(covered(x,z,n+1,known))
            self.assertEqual(n,max(k for k in range(1,625) if covered(x,z,k,known)))
    def test_initial_missing_center_and_recovery(self):
        self.assertEqual(safe(0,0,624,set()),0)
        self.assertLess(safe(0,0,624,{(0,0)}),16)
        full={(x,z) for x in range(-21,22) for z in range(-21,22)}
        self.assertEqual(safe(0,0,624,full),624)
    def test_source_contract(self):
        s=P.read_text("utf-8")
        ast.parse(s)
        for t in ("v22SafeCrop(x,z,requested","if(crop<16){valid=false",
                  "requestedCropPixels()","V178MiniRaster.effectiveCrop(requested)",
                  "int color=tile[pixelRow+B1799_COLUMN_PIXEL[px]];",
                  "if(drawTerrain&&!V178MiniRaster.hasCompleteTerrain())",
                  "v22RasterWorld.get()!=world"):
            self.assertIn(t,s)
    def test_reconstructed(self):
        root=os.environ.get("V1_SOURCE_ROOT")
        if not root:self.skipTest("CI reconstructed sources only")
        j=Path(root)/"dev/obsidiannetwork/client"
        raster=(j/"V178MiniRaster.java").read_text("utf-8")
        self.assertNotIn("tile==null?UNKNOWN",raster)
        self.assertIn("if(crop<16){valid=false",raster)
        self.assertIn("b1883Tint(color,claim",raster)
        self.assertIn("requestedCropPixels()", (j/"V178TerrainMap.java").read_text("utf-8"))
if __name__=="__main__":unittest.main()
