#!/usr/bin/env python3
"""Solid Fuel Generator: targeted visual occlusion correction, no runtime regression."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v177/apply-v177-solid-fuel-generator-occlusion.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class SolidFuelOcclusion(unittest.TestCase):
 def test_injector_changes_only_one_block_properties(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
  with tempfile.TemporaryDirectory() as folder:
   j=Path(folder)/"dev/obsidiannetwork"
   j.mkdir(parents=True)
   main=j/"ObsidianNetwork.java"
   original="""public final class ObsidianNetwork {
 static Object OTHER=BLOCKS.registerBlock("other_machine",OtherMachine::new,
     p->p.strength(3.0F,8.0F));
 static Object SOLID_FUEL_GENERATOR=BLOCKS.registerBlock("solid_fuel_generator",
     SolidFuelGeneratorBlock::new,p -> p.mapColor(MapColor.METAL)
         .strength(3.0F,8.0F).requiresCorrectToolForDrops());
}
"""
   main.write_text(original,encoding="utf-8")
   env={**os.environ,"V1_SOURCE_ROOT":folder}
   first=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(first.returncode,0,first.stdout+first.stderr)
   actual=main.read_text(encoding="utf-8")
   self.assertEqual(actual.count(".noOcclusion()"),1)
   self.assertIn("p.noOcclusion() /* V177_SOLID_FUEL_NO_OCCLUSION */.mapColor",actual)
   self.assertIn('BLOCKS.registerBlock("other_machine",OtherMachine::new,\n     p->p.strength(3.0F,8.0F));',actual)
   self.assertEqual(actual.replace(".noOcclusion() /* V177_SOLID_FUEL_NO_OCCLUSION */",""),original)
   second=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(second.returncode,0,"Must not double-patch properties")

 def test_unknown_registration_does_not_mutate_source(self):
  with tempfile.TemporaryDirectory() as folder:
   j=Path(folder)/"dev/obsidiannetwork"
   j.mkdir(parents=True)
   main=j/"ObsidianNetwork.java"
   before='public final class ObsidianNetwork {}'
   main.write_text(before,encoding="utf-8")
   test=subprocess.run([sys.executable,str(PATCH)],
      env={**os.environ,"V1_SOURCE_ROOT":folder},capture_output=True,text=True)
   self.assertNotEqual(test.returncode,0)
   self.assertEqual(main.read_text(encoding="utf-8"),before)

 def test_177_only_and_after_b609_existing_occlusion_fixes(self):
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',WORKFLOW)
  self.assertIn('python3 features/v177/apply-v177-solid-fuel-generator-occlusion.py',WORKFLOW)
  self.assertIn("test_v177_solid_fuel_generator_occlusion.py",WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v174/apply-v174-hotfix609-occlusion-and-facade-guard.py"),
                  WORKFLOW.index("python3 features/v177/apply-v177-solid-fuel-generator-occlusion.py"))

if __name__=="__main__":
 unittest.main()
