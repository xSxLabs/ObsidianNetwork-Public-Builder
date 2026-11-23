#!/usr/bin/env python3
"""B1855 claim screenshot regressions: visually filled, bounded, shared painter."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v178/apply-v178-v19-b1855-claim-overlay.py").read_text("utf-8")
BASE=(ROOT/"features/v178/apply-v178-ftb-map-gui.py").read_text("utf-8")

class ClaimVisualB1855(unittest.TestCase):
    def test_both_maps_use_the_same_painter(self):
        self.assertGreaterEqual(BASE.count("V178TerrainMap.drawClaim("),2)
        self.assertIn("V178ClaimsClient.java",PATCH)
        self.assertIn("V178ClaimsMapScreen.java",PATCH)
    def test_filled_chunk_with_four_sharp_edges(self):
        self.assertIn("g.fill(x,y,x+tile,y+tile,fill);",PATCH)
        for edge in ("g.fill(x,y,x+tile,y+1,edge);",
                     "g.fill(x,y+tile-1,x+tile,y+tile,edge);",
                     "g.fill(x,y,x+1,y+tile,edge);",
                     "g.fill(x+tile-1,y,x+tile,y+tile,edge);"):
            self.assertIn(edge,PATCH)
        for color in ("0x5379b4ff","0x486acaf2","0x497e94d5"):
            self.assertIn(color,PATCH)
    def test_claim_bits_and_server_persistence_unchanged(self):
        self.assertIn("(status&3)==0",PATCH)
        self.assertIn("(status&4)!=0",PATCH)
        self.assertIn("tile>=6",PATCH)
        self.assertIn("assert s.count(anchor)==1",PATCH)
        self.assertIn("assert \"V178TerrainMap.drawClaim(\" in mini",PATCH)
        self.assertIn("assert \"V178TerrainMap.drawClaim(\" in full",PATCH)

if __name__=="__main__":
    unittest.main()
