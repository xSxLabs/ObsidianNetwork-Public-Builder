#!/usr/bin/env python3
"""v1.7.4 B436: synced GUI screens, live tiles, no fake powerbank item storage."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
script=(root/"features/v174/apply-machine-guis-436.py").read_text(encoding="utf-8")
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
ast.parse(script)
for t in (
 "V174MachineScreen","GuiGraphicsExtractor","extractBackground(",
 "extractLabels(","xsxV174MachineGuiOpen","ScreenEvent.Opening",
 "ClientboundBlockEntityDataPacket.create(this)","getUpdateTag(",
 "world.getGameTime()%40L","sl.getGameTime()%40L",
 "getGuiGraphics" if False else "guiEnergy()","guiWaterCapacity()",
 "PowerbankMenu","slots.get(i).container","mayPickup(Player p){return false;}"
):assert t in script,t
for t in ("python3 features/v174/apply-machine-guis-436.py",
          "python3 tests/test_v174_machine_guis_436.py"):
 assert t in wf,t
assert wf.index("python3 features/v174/apply-water-pump-434.py")<wf.index("python3 features/v174/apply-machine-guis-436.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 assert (j/"client/V174MachineScreen.java").is_file()
 assert (j/"powerbank/PowerbankMenu.java").is_file()
 for path in ("reactor/ReactorControllerBlockEntity.java",
              "pump/ElectricWaterPumpBlockEntity.java",
              "powerbank/PowerbankBlockEntity.java"):
  assert "ClientboundBlockEntityDataPacket.create(this)" in (j/path).read_text(),path
print("V174_MACHINE_GUI_B436_TEST_PASS")
