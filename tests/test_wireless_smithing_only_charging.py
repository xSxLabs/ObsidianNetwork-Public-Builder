#!/usr/bin/env python3
"""Fail-closed prevention of implicit battery-tool smithing via player charging."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/wireless-energy/apply-wireless-smithing-only-charging.py"

CHARGE="""package dev.obsidiannetwork.wireless;
public class WirelessPlayerCharging {
 static int chargeOne(ServerPlayer player,String network,ItemStack stack,int budget){
  var energy=net.neoforged.neoforge.transfer.access.ItemAccess.forStack(stack).getCapability(Capabilities.Energy.ITEM);
  if(energy!=null){return 0;}
  // Existing Obsidian EnergyTool items use a custom component, not an FE capability.
  if(EnergyTool.eligible(stack)){
   long missing=Math.max(0,EnergyTool.capacity(stack)-EnergyTool.energy(stack));
   if(missing<=0)return 0;
   int drawn=123;
   EnergyTool.setEnergy(stack,EnergyTool.energy(stack)+drawn);
   return drawn;
  }
  return 0;
 }
}
"""
COMMANDS="""package dev.obsidiannetwork.wireless;
public class WirelessNetworkCommands {
 public static void register(RegisterCommandsEvent event){
  event.getDispatcher().register(Commands.literal("wirelessnet")
    .then(Commands.literal("delete")
     .then(Commands.argument("id",StringArgumentType.word())
      .executes(ctx->{
       return 1;
      })))
  );
 }
}
"""
SMITH="""public class BatteryUpgradeSmithingRecipe {
 public boolean matches(SmithingRecipeInput in,Level level){
   return in.template().is(ObsidianNetwork.BATTERY_UPGRADE.get())&&EnergyTool.eligible(in.base())&&!EnergyTool.upgraded(in.base())&&in.addition().is(ObsidianNetwork.BATTERY.get());
 }
 public ItemStack assemble(SmithingRecipeInput in){
   ItemStack out=in.base().copy();
   out.setCount(1);
   out.setDamageValue(0);
   EnergyTool.setEnergy(out,EnergyTool.capacity(out));
   return out;
 }
}
"""

def make_fixture(root,charge=CHARGE,commands=COMMANDS,smith=SMITH):
    for relative,content in {
        "wireless/WirelessPlayerCharging.java":charge,
        "wireless/WirelessNetworkCommands.java":commands,
        "recipe/BatteryUpgradeSmithingRecipe.java":smith,
    }.items():
        f=root/"dev/obsidiannetwork"/relative
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(content)

def run(root):
    return subprocess.run([sys.executable,str(PATCH)],capture_output=True,
                          text=True,env={**os.environ,"V1_SOURCE_ROOT":str(root)})

class SmithingOnlyWirelessCharging(unittest.TestCase):
    def test_real_patch_and_smithing_only_guard(self):
        ast.parse(PATCH.read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); make_fixture(root)
            result=run(root)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            ch=(root/"dev/obsidiannetwork/wireless/WirelessPlayerCharging.java").read_text()
            self.assertIn("if(EnergyTool.upgraded(stack))",ch)
            self.assertNotIn("if(EnergyTool.eligible(stack))",ch)
            self.assertIn("getCapability(Capabilities.Energy.ITEM)",ch)
            self.assertIn("EnergyTool.setEnergy(stack,EnergyTool.energy(stack)+drawn)",ch)
            self.assertIn("WIRELESS_SMITHING_ONLY_TOOL_CHARGE_V1",ch)
            cmd=(root/"dev/obsidiannetwork/wireless/WirelessNetworkCommands.java").read_text()
            self.assertIn('Commands.literal("delete")',cmd)
            self.assertIn('Commands.literal("restoretool")',cmd)
            self.assertIn("held.remove(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get())",cmd)
            self.assertIn("held.isEmpty()||!dev.obsidiannetwork.core.EnergyTool.upgraded(held)",cmd)
            self.assertNotIn("setDamageValue(",cmd)
            self.assertNotIn("getNonEquipmentItems()",cmd)
            self.assertIn("player.getMainHandItem()",cmd)
            self.assertEqual((root/"dev/obsidiannetwork/recipe/BatteryUpgradeSmithingRecipe.java").read_text(),SMITH)
            self.assertNotEqual(run(root).returncode,0)
            self.assertEqual((root/"dev/obsidiannetwork/wireless/WirelessPlayerCharging.java").read_text(),ch)
    def test_source_drift_never_changes_charge_or_smithing(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            make_fixture(root,charge=CHARGE.replace("EnergyTool.eligible(stack)","EnergyTool.eligibleWithUnknownChanges(stack)"))
            old=(root/"dev/obsidiannetwork/wireless/WirelessPlayerCharging.java").read_text()
            r=run(root); self.assertNotEqual(r.returncode,0)
            self.assertEqual((root/"dev/obsidiannetwork/wireless/WirelessPlayerCharging.java").read_text(),old)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            make_fixture(root,smith=SMITH.replace("EnergyTool.setEnergy(out,EnergyTool.capacity(out));","return out;"))
            r=run(root); self.assertNotEqual(r.returncode,0)
    def test_guard_does_not_erase_all_existing_energy_upgrades(self):
        script=PATCH.read_text()
        self.assertIn("EnergyTool.upgraded(stack)",script)
        self.assertNotIn("stack.remove(",script)
        self.assertIn("held.remove(",script)
        self.assertIn("getMainHandItem()",script)
        self.assertNotIn("getOffhandItem()",script)


if __name__=="__main__":
    unittest.main()
