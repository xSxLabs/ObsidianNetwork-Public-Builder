#!/usr/bin/env python3
"""Never upgrade a vanilla or modded durability tool by wireless charging.

Only Battery Upgrade Smithing may install the Obsidian ENERGY_TOOL_FE component.
Existing incorrect conversions are not automatically stripped: they are
indistinguishable from a legitimate prior smithing upgrade on disk. The player
can explicitly remove just that component from their held tool via
/wirelessnet restoretool. Its DAMAGE, enchants, name and all unrelated
components are preserved. No inventory-wide mutation, no FE mint/refund.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
charge=root/"wireless/WirelessPlayerCharging.java"
source=charge.read_text(encoding="utf-8")
old="""  // Existing Obsidian EnergyTool items use a custom component, not an FE capability.
  if(EnergyTool.eligible(stack)){"""
new="""  // WIRELESS_SMITHING_ONLY_TOOL_CHARGE_V1: only an explicit Battery Upgrade
  // Smithing result has this persistent component. Merely being damageable
  // does not authorize converting a normal tool to energy operation.
  // Never call EnergyTool.setEnergy on an unupgraded ItemStack.
  if(EnergyTool.upgraded(stack)){"""
assert source.count(old)==1, "Wireless chargeOne upgrade eligibility changed"
assert source.count("EnergyTool.setEnergy(stack,EnergyTool.energy(stack)+drawn);")==1
assert "getCapability(Capabilities.Energy.ITEM)" in source
charge.write_text(source.replace(old,new,1),encoding="utf-8")

# Recovery is explicit, main hand only, never automatically alters existing
# upgrade data in someone's saved world. Since both intended smithing and the
# prior bug installed the same component, old items cannot be identified
# unambiguously. Preserve every other ItemStack component.
commands=root/"wireless/WirelessNetworkCommands.java"
text=commands.read_text(encoding="utf-8")
old="""      })))
  );
 }
}"""
new="""      })))
    .then(Commands.literal("restoretool")
     .executes(ctx->{
      var player=ctx.getSource().getPlayerOrException();
      var held=player.getMainHandItem();
      // WIRELESS_HELD_TOOL_RESTORE_V1: never affect offhand, armor, other
      // inventory items, naturally energy-powered mods or unmodified tools.
      if(held.isEmpty()||!dev.obsidiannetwork.core.EnergyTool.upgraded(held)){
       player.sendSystemMessage(Component.literal("Hold an Obsidian energy-upgraded tool in your main hand."));
       return 0;
      }
      // Only the Obsidian conversion marker is removed. The original
      // durability component, enchantments, custom names etc. remain.
      held.remove(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get());
      player.getInventory().setChanged();
      player.containerMenu.broadcastChanges();
      player.sendSystemMessage(Component.literal("Restored normal durability tool (Obsidian FE component removed)."));
      return 1;
     }))
  );
 }
}"""
assert text.count(old)==1, "Wireless command chain drift"
assert text.count('Commands.literal("delete")')==1, "existing owner command disappeared"
commands.write_text(text.replace(old,new,1),encoding="utf-8")
smith=root/"recipe/BatteryUpgradeSmithingRecipe.java"
recipe=smith.read_text(encoding="utf-8")
assert "EnergyTool.setEnergy(out,EnergyTool.capacity(out));" in recipe
assert "in.template().is(ObsidianNetwork.BATTERY_UPGRADE.get())" in recipe
assert "in.addition().is(ObsidianNetwork.BATTERY.get())" in recipe
assert "EnergyTool.eligible(in.base())&&!EnergyTool.upgraded(in.base())" in recipe
assert "out.setDamageValue(0)" in recipe
print("WIRELESS_SMITHING_ONLY_TOOL_CHARGE_V1 PASS; WIRELESS_HELD_TOOL_RESTORE_V1 PASS")
