#!/usr/bin/env python3
"""Standalone fail-closed v1.7.6 Micro-MG registration regression tests."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v176/apply-v176-micro-mg-module.py"
class MicroMgModuleTests(unittest.TestCase):
 def test_module_install_recipe_and_repeated_patch_fail_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp)
   j=base/"src/dev/obsidiannetwork"
   (j/"powerarmor").mkdir(parents=True)
   (j/"ObsidianNetwork.java").write_text(
     '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_ENERGY_SHIELD =\n'
     '            output.accept((ItemLike)POWER_CARD_ENERGY_SHIELD.get());\n')
   (j/"powerarmor/PowerArmorCards.java").write_text('   default -> null;\n')
   r=base/"resources/assets/obsidiannetwork/lang"
   r.mkdir(parents=True)
   for lang in ("de_de","en_us"):
    (r/(lang+".json")).write_text('{"existing.key": "unchanged"}\n')
   env={**os.environ,"V1_SOURCE_ROOT":str(base/"src"),"V1_RESOURCE_ROOT":str(base/"resources")}
   result=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn("V176_MICRO_MG_REGISTERED_AND_STATION_INSTALLABLE PASS",result.stdout)
   registry=(j/"ObsidianNetwork.java").read_text()
   self.assertEqual(registry.count('ITEMS.registerItem("power_card_micro_mg"'),1)
   self.assertIn('output.accept((ItemLike)POWER_CARD_MICRO_MG.get());',registry)
   lookup=(j/"powerarmor/PowerArmorCards.java").read_text()
   self.assertIn('case "micro_mg" ->',lookup)
   recipe=json.loads((base/"resources/data/obsidiannetwork/recipe/power_card_micro_mg.json").read_text())
   self.assertEqual(recipe["result"]["id"],"obsidiannetwork:power_card_micro_mg")
   self.assertEqual(recipe["pattern"],["CEC","EUE","CEC"])
   self.assertEqual(set(recipe["key"]),{"C","E","U"})
   for lang in ("de_de","en_us"):
    lang_doc=json.loads((r/(lang+".json")).read_text())
    self.assertEqual(lang_doc["existing.key"],"unchanged")
    self.assertIn("item.obsidiannetwork.power_card_micro_mg",lang_doc)
   again=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertNotEqual(again.returncode,0,"Patch must fail closed when already applied")

if __name__=="__main__":unittest.main()
