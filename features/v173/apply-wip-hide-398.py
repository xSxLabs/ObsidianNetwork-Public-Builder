#!/usr/bin/env python3
"""Build398: temporarily hide unfinished Holo, Printer, Schematic and Quill.

Preserve every block/item/block-entity registry entry and old world/player data.
No destructive feature removal; just suppress Creative, JEI and crafting access.
"""
import os
from pathlib import Path

java = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
data = Path(os.environ["V1_RESOURCE_ROOT"]) / "data/obsidiannetwork"

main = java / "ObsidianNetwork.java"
source = main.read_text(encoding="utf-8")
wip_items = (
    "NETWORK_HOLOGRAM_TERMINAL_ITEM",
    "NETWORK_PRINTER_ITEM",
    "NETWORK_BLUEPRINT",
    "NETWORK_SCHEMATIC_QUILL",
)
for field in wip_items:
    entry = f"            output.accept((ItemLike){field}.get());\n"
    assert source.count(entry) == 1, ("B398_CREATIVE_DRIFT", field, source.count(entry))
    source = source.replace(entry, "", 1)
    assert field in source, ("B398_REGISTRY_LOST", field)
assert "NETWORK_PLANTER_ITEM.get()" in source
main.write_text(source, encoding="utf-8")

for name in ("network_hologram_terminal", "network_printer",
             "network_schematic_quill"):
    recipe = data / f"recipe/{name}.json"
    assert recipe.is_file(), ("B398_RECIPE_DRIFT", str(recipe))
    recipe.unlink()
assert not (data / "recipe/network_blueprint.json").exists(), (
    "B398_SAVED_SCHEMATIC_RECIPE_UNEXPECTED")

# JEI indexes registered item ingredients independently of Creative and recipes.
# A separate optional JEI plugin can remove only these four WIP items once
# its ingredient manager is live. Other mod content is untouched.
plugin = java / "compat/jei/WipItemsJeiPlugin.java"
assert not plugin.exists(), ("B398_JEI_PLUGIN_ALREADY_EXISTS", str(plugin))
plugin.parent.mkdir(parents=True, exist_ok=True)
plugin.write_text("""package dev.obsidiannetwork.compat.jei;

// B398_WIP_JEI_HIDE: no public discovery of unfinished Holo/Printer/Schematics.
@mezz.jei.api.JeiPlugin
public final class WipItemsJeiPlugin implements mezz.jei.api.IModPlugin {
  @Override public net.minecraft.resources.Identifier getPluginUid() {
    return net.minecraft.resources.Identifier.fromNamespaceAndPath(
        "obsidiannetwork", "wip_items_hide");
  }
  @Override public void onRuntimeAvailable(mezz.jei.api.runtime.IJeiRuntime runtime) {
    runtime.getIngredientManager().removeIngredientsAtRuntime(
        mezz.jei.api.constants.VanillaTypes.ITEM_STACK,
        java.util.List.of(
          new net.minecraft.world.item.ItemStack(
              dev.obsidiannetwork.ObsidianNetwork.NETWORK_HOLOGRAM_TERMINAL_ITEM.get()),
          new net.minecraft.world.item.ItemStack(
              dev.obsidiannetwork.ObsidianNetwork.NETWORK_PRINTER_ITEM.get()),
          new net.minecraft.world.item.ItemStack(
              dev.obsidiannetwork.ObsidianNetwork.NETWORK_BLUEPRINT.get()),
          new net.minecraft.world.item.ItemStack(
              dev.obsidiannetwork.ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get())
        )
    );
  }
}
""", encoding="utf-8")

entity_reg = (java / "registry/ModBlockEntities.java").read_text(encoding="utf-8")
assert "NETWORK_HOLOGRAM_TERMINAL.get()" in entity_reg
assert "NETWORK_PRINTER.get()" in entity_reg
print("B398_WIP_HIDDEN_PASS: 4 items removed from Creative+JEI, 3 recipes removed; registrations retained")
