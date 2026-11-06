"""B1226 survival and modded tool enchantment regression."""
import ast,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"features/v176/apply-v176-b1226-tool-enchantments.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
class ToolEnchantmentsB1226(unittest.TestCase):
 def test_pipeline_and_syntax(self):
  ast.parse(SOURCE.read_text())
  text=WORKFLOW.read_text()
  self.assertIn("test_v176_b1226_tool_enchantments.py",text)
  self.assertIn("python3 features/v176/apply-v176-b1226-tool-enchantments.py",text)
  self.assertLess(text.index("python3 features/v176/apply-v176-b1224-held-tools.py"),
                  text.index("python3 features/v176/apply-v176-b1226-tool-enchantments.py"))
 def test_survival_vanilla_modded_tags_and_components(self):
  with tempfile.TemporaryDirectory() as tmp:
   java=Path(tmp)/"src/dev/obsidiannetwork"
   resources=Path(tmp)/"resources"
   for name,durability in (("multitool",6093),("hammer",12186)):
    p=java/name/(name.capitalize()+"Item.java")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("super(ToolMaterial.NETHERITE.applyToolProperties(properties,BlockTags.MINEABLE_WITH_PICKAXE,8.0F,-3.0F,0.0F).durability("+str(durability)+"));")
   env={**os.environ,"V1_SOURCE_ROOT":str(Path(tmp)/"src"),"V1_RESOURCE_ROOT":str(resources)}
   done=subprocess.run([sys.executable,str(SOURCE)],env=env,capture_output=True,text=True,check=True)
   self.assertIn("VANILLA_AND_MODDED_PICKAXE_TAGS_PASS",done.stdout)
   for name,durability in (("multitool",6093),("hammer",12186)):
    p=java/name/(name.capitalize()+"Item.java")
    self.assertIn(f".durability({durability}).enchantable(15)",p.read_text())
   root=resources/"data/minecraft/tags/item"
   for key,needed in (
    ("pickaxes",["obsidiannetwork:multitool","obsidiannetwork:hammer"]),
    ("axes",["obsidiannetwork:multitool"]),
    ("shovels",["obsidiannetwork:multitool"])
   ):
    tag=json.loads((root/(key+".json")).read_text())
    self.assertEqual(tag["replace"],False)
    self.assertEqual(tag["values"],needed)
   # Must not be a hardcoded enchantment whitelist; modded entries use
   # normal data-driven item tags and can register on their own.
   self.assertNotIn("minecraft:efficiency",SOURCE.read_text())
   self.assertNotIn("modded_enchantments_only",SOURCE.read_text())
if __name__=="__main__":unittest.main()
