#!/usr/bin/env python3
"""Build398 regression: WIP items hidden but old saves stay loadable."""
import os
from pathlib import Path

java = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
data = Path(os.environ["V1_RESOURCE_ROOT"]) / "data/obsidiannetwork"
main = (java / "ObsidianNetwork.java").read_text(encoding="utf-8")
plugin = (java / "compat/jei/WipItemsJeiPlugin.java").read_text(encoding="utf-8")
entity_reg = (java / "registry/ModBlockEntities.java").read_text(encoding="utf-8")
wip = ("NETWORK_HOLOGRAM_TERMINAL_ITEM", "NETWORK_PRINTER_ITEM",
       "NETWORK_BLUEPRINT", "NETWORK_SCHEMATIC_QUILL")
for field in wip:
    assert f"output.accept((ItemLike){field}.get())" not in main, field
    assert field in main, ("WIP registration lost", field)
    assert f"ObsidianNetwork.{field}.get()" in plugin, field
assert "output.accept((ItemLike)NETWORK_PLANTER_ITEM.get())" in main
assert 'registerBlock("network_hologram_terminal"' in main
assert 'registerBlock("network_printer"' in main
assert "NETWORK_HOLOGRAM_TERMINAL.get()" in entity_reg
assert "NETWORK_PRINTER.get()" in entity_reg
for name in ("network_hologram_terminal", "network_printer",
             "network_blueprint", "network_schematic_quill"):
    assert not (data / f"recipe/{name}.json").exists(), name
assert "@mezz.jei.api.JeiPlugin" in plugin
assert "removeIngredientsAtRuntime(" in plugin
assert "VanillaTypes.ITEM_STACK" in plugin
assert "NETWORK_PLANTER_ITEM.get()" not in plugin
print("B398_WIP_HIDDEN_SOURCE_GATE_PASS")
