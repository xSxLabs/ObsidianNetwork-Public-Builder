#!/usr/bin/env python3
"""Static B674 regression: Looting I-III carries across station install/remove."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-looting-674.py"
class TestLooting(unittest.TestCase):
 def test_suit_anvil_and_installed_roundtrip(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"dev/obsidiannetwork"
   (root/"powerarmor").mkdir(parents=True)
   (root/"powerarmor/UpgradeCardItem.java").write_text(
    ' public UpgradeCardItem(Properties p,String id){super(p.stacksTo(16));this.upgradeId=id;}')
   (root/"powerarmor/ArmorStationBlock.java").write_text("""
        installed.isEmpty()?card.upgradeId:installed+","+card.upgradeId);
      if(!p.getInventory().add(new ItemStack(cardItem))){
      left.remove(i);
""")
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   cp=subprocess.run([sys.executable,str(PATCH)],env=env,text=True,capture_output=True)
   self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
   item=(root/"powerarmor/UpgradeCardItem.java").read_text()
   suit=(root/"powerarmor/ArmorStationBlock.java").read_text()
   helper=(root/"powerarmor/V176LootingSupport.java").read_text()
   self.assertIn('enchantment.is(net.minecraft.world.item.enchantment.Enchantments.LOOTING)',item)
   self.assertIn('"micro_mg".equals(id)?1:16',item)
   self.assertIn('V176LootingSupport.install(',suit)
   self.assertIn('V176LootingSupport.restore(',suit)
   self.assertIn('left.removeIf(V176LootingSupport::isLootingToken)',suit)
   self.assertIn('return module?found:0;',helper)
   self.assertIn('Math.min(3,input.getEnchantmentLevel(holder))',helper)
   cp2=subprocess.run([sys.executable,str(PATCH)],env=env,text=True,capture_output=True)
   self.assertNotEqual(cp2.returncode,0)
if __name__=="__main__":unittest.main()
