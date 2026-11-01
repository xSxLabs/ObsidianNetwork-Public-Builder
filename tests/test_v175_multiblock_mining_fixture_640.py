#!/usr/bin/env python3
"""B640 independent preflight: real B639 failure fixture (instant 0/0 skin).

Run against an isolated reconstruction before the expensive Gradle build.
It deliberately mixes 0.0/0.0 unprotected multiblock skins, original
3/9 protected blocks and extra property chain methods.
"""
import json, os, re, runpy, tempfile, unittest
from pathlib import Path

PATCH=Path(__file__).resolve().parents[1]/"features/v175/apply-v175-multiblock-pickaxe-638.py"
REACTOR=("reactor_casing","reactor_glass","reactor_fuel_assembly",
         "reactor_item_port","reactor_fluid_port","reactor_power_port","reactor_controller")
POWERBANK=("powerbank_casing","powerbank_glass","powerbank_controller",
           "powerbank_input_port","powerbank_output_port")
NAMES=REACTOR+POWERBANK
class Mineable640(unittest.TestCase):
 def test_integrated_zero_hardness_and_original_blocks(self):
  with tempfile.TemporaryDirectory() as root:
   root=Path(root)
   java=root/"java"/"dev"/"obsidiannetwork"
   res=root/"res"
   java.mkdir(parents=True)
   tag=res/"data"/"minecraft"/"tags"/"block"/"mineable"/"pickaxe.json"
   tag.parent.mkdir(parents=True)
   tag.write_text(json.dumps({"replace":False,"values":["obsidiannetwork:"+n for n in NAMES]}))
   lines=["package dev.obsidiannetwork;","public class ObsidianNetwork {"]
   for i,n in enumerate(NAMES):
    if i%3==0:
     entry=f'BLOCKS.registerBlock("{n}", dev.obsidiannetwork.multiblock.MultiblockSkinBlock::new,\n            p -> p.mapColor(MapColor.METAL).strength(0.0F,0.0F));'
    elif i%3==1:
     entry=f'BLOCKS.registerBlock("{n}", net.minecraft.world.level.block.Block::new,\n            p -> p.mapColor(MapColor.METAL).strength(3.5F,9.0F).requiresCorrectToolForDrops());'
    else:
     entry=f'BLOCKS.registerBlock("{n}", net.minecraft.world.level.block.Block::new,\n            p -> p.mapColor(MapColor.METAL).strength(3.0F,9.0F).noOcclusion());'
    lines.append(entry)
   lines.append("}")
   original="\n".join(lines)+"\n"
   (java/"ObsidianNetwork.java").write_text(original,encoding="utf-8")
   old_src=os.environ.get("V1_SOURCE_ROOT")
   old_res=os.environ.get("V1_RESOURCE_ROOT")
   try:
    os.environ["V1_SOURCE_ROOT"]=str(root/"java")
    os.environ["V1_RESOURCE_ROOT"]=str(res)
    runpy.run_path(str(PATCH),run_name="__main__")
   finally:
    if old_src is None:os.environ.pop("V1_SOURCE_ROOT",None)
    else:os.environ["V1_SOURCE_ROOT"]=old_src
    if old_res is None:os.environ.pop("V1_RESOURCE_ROOT",None)
    else:os.environ["V1_RESOURCE_ROOT"]=old_res
   actual=(java/"ObsidianNetwork.java").read_text()
   for name in NAMES:
    assert actual.count(f'BLOCKS.registerBlock("{name}"')==1
    match=re.search(r'BLOCKS\.registerBlock\("'+name+r'".*?(?=\);)',actual,re.S)
    self.assertIsNotNone(match,name)
    self.assertIn('.strength(6.0F,9.0F)',match.group(),name)
    self.assertIn('.requiresCorrectToolForDrops()',match.group(),name)
   self.assertEqual(actual.count(".noOcclusion()"),original.count(".noOcclusion()"))
   self.assertEqual(actual.count("::new"),original.count("::new"))
   self.assertNotIn(".strength(0.0F,0.0F)",actual)

if __name__=="__main__":unittest.main()
