#!/usr/bin/env python3
"""B1815 regressions: menu packet indices, maximal formed bank glazing,
and improved pickaxe face. Run after the B1815 source/resource patch."""
import ast
import json
import os
import struct
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v178/apply-v178-b1815-v15.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf8")

class B1815(unittest.TestCase):
 def test_pipeline_and_patch_compile(self):
  src=SCRIPT.read_text("utf8")
  ast.parse(src)
  old="python3 features/v178/apply-v178-b1810-v15.py"
  new="python3 features/v178/apply-v178-b1815-v15.py"
  self.assertIn(old,WF)
  self.assertIn(new,WF)
  self.assertLess(WF.index(old),WF.index(new))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v17.jar",WF)
 def test_minecraft_click_slot_index_contract(self):
  src=SCRIPT.read_text("utf8")
  for token in ("slots.get(1).index=1;",
                "menu.slots.get(1).index=1;",
                "slots.get(0).index=0;",
                "menu.slots.get(0).index=0;",
                ".get(i).index=i;",
                "return be.installedSpeedUpgrades().copy();",
                "source.setByPlayer(held)",
                "moveItemStackTo(held,27,63,true)"):
   self.assertIn(token,src)
  self.assertNotIn("forceChunk(",src)
 def test_glass_and_one_cube_contract(self):
  src=SCRIPT.read_text("utf8")
  self.assertIn("(32,112,154,164)",src)
  self.assertIn("(31,169,201,176)",src)
  self.assertIn('len(bank["variants"]) == 144',src)
  self.assertIn('len(model["elements"]) == 1',src)
  self.assertIn("png_rgba32()",src)
 def test_reconstructed_java_resources(self):
  java_root=os.getenv("V1_SOURCE_ROOT")
  resource_root=os.getenv("V1_RESOURCE_ROOT")
  if not java_root or not resource_root:
   self.skipTest("requires reconstructed CI Minecraft java/resource roots")
  j=Path(java_root)/"dev/obsidiannetwork"
  a=Path(resource_root)/"assets/obsidiannetwork"
  server=(j/"mining/V178MiningBuilderMenu.java").read_text("utf8")
  client=(j/"client/V178MiningBuilderOperationsScreen.java").read_text("utf8")
  for token in ("slots.get(0).index=0;", "slots.get(1).index=1;",
                "slots.get(i).index=i;", "source.setByPlayer(held)",
                "moveItemStackTo(held,27,63,true)"):
   self.assertIn(token,server)
  for token in ("menu.slots.get(0).index=0;", "menu.slots.get(1).index=1;",
                "menu.slots.get(i).index=i;"):
   self.assertIn(token,client)
  icon=a/"textures/block/mining_builder_front_v15.png"
  with Image.open(icon) as png:
   self.assertEqual(png.size,(32,32))
   self.assertEqual(png.getpixel((15,11))[0],189)
  model=json.loads((a/"models/block/mining_builder.json").read_text("utf8"))
  self.assertEqual(len(model["elements"]),1)
  self.assertEqual(model["elements"][0]["faces"]["north"]["texture"],"#front")
  variants=json.loads((a/"blockstates/powerbank_glass.json").read_text("utf8"))["variants"]
  self.assertEqual(len(variants),144)
  for suffix in ("","_lit_detail0","_lit_detail1","_lit_detail2"):
   name="powerbank_glass_formed"+suffix
   with Image.open(a/"textures/block"/(name+".png")) as png:
    self.assertEqual(png.size,(32,32))
    expected=(32,112,154,164) if not suffix else (31,169,201,176)
    self.assertEqual(png.getpixel((0,0)),expected)
    self.assertEqual(png.getpixel((31,31)),expected)
  for key,data in variants.items():
   if key.startswith("formed=true,"):
    model=data["model"].split("/")[-1]
    self.assertTrue((a/"models/block"/(model+".json")).is_file(),model)

if __name__=="__main__": unittest.main()
