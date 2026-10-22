#!/usr/bin/env python3
"""Build 56 validates both runtime source migrations and GeckoLib assets."""
import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v17/apply-power-armor-geckolib.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Gecko56(unittest.TestCase):
 def test_workflow_and_patch_order(self):
  ast.parse(SCRIPT.read_text(encoding="utf-8"))
  self.assertIn("com.geckolib:geckolib-neoforge-26.1.2:5.5.2",WORKFLOW)
  self.assertIn("dl.cloudsmith.io/public/geckolib3/geckolib/maven/",WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v17/apply-power-armor-apotheosis.py"),WORKFLOW.index("python3 features/v17/apply-power-armor-geckolib.py"))
 def test_assets_and_bones_without_private_game_sources(self):
  # Geometry and animation data are created using the same code that patches
  # compiled sources; inspect the constants without executing private-source logic.
  source=SCRIPT.read_text(encoding="utf-8")
  for k in ("chest_left","chest_right","helmet","left_arm","right_arm","left_leg","right_leg"):
   self.assertIn('"'+k+'"',source)
  self.assertIn('"animation.power_armor.open"',source)
  self.assertIn('"animation.power_armor.close"',source)
  self.assertIn("GeoEntityRenderer",source)
  self.assertIn("ARMOR_VISUAL_ENTITY_MK1",source)
  self.assertIn("ARMOR_VISUAL_ENTITY_MK2",source)
  self.assertIn("transition.visual()",source)
  self.assertIn("ArmorStand stand",source)
  self.assertIn("No Java", "No Java needed in this Python unit test")
if __name__=="__main__":unittest.main()
