#!/usr/bin/env python3
"""B478 full v1.7.4 integration gate: requirements -> generated source -> JAR.

No fabricated approval: "candidate" only means the assembled JAR contains
all required components. Full gameplay still requires actual human playtests.
"""
import argparse
import ast
import json
import os
from pathlib import Path
from zipfile import ZipFile

root=Path(__file__).resolve().parents[1]
workflow=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
scripts={
 "uranium":"features/v174/apply-uranium-fuel-chain.py",
 "reactor":"features/v174/apply-reactor-core-427.py",
 "reactor_ports":"features/v174/apply-reactor-ports-433.py",
 "reactor_recovery":"features/v174/apply-multiblock-recovery-431.py",
 "reactor_animations":"features/v174/apply-multiblock-animations-437.py",
 "powerbank":"features/v174/apply-powerbank-core-429.py",
 "water_pump":"features/v174/apply-water-pump-434.py",
 "machine_guis":"features/v174/apply-machine-guis-436.py",
 "build_guide":"features/v174/apply-guidebook-size-445.py",
 "nutrinator":"features/v174/apply-nutrition-438.py",
 "nutrinator_guis":"features/v174/apply-nutrinator-gui-461.py",
 "nutripaste_fluid":"features/v174/apply-nutripaste-fluid-477.py",
 "planter_modded":"features/v174/apply-planter-mod-crops-457.py",
 "planter_tagged":"features/v174/apply-planter-tagged-crops-462.py",
 "network_vision":"features/v174/apply-network-vision-xray-469.py",
 "warden_darkness":"features/v174/apply-nightvision-warden-darkness-464.py",
 "wip_schematics":"features/v174/apply-wip-public-test-476.py",
 "item_cable":"patches/v173-stack-upgrades-global.py",
 "portal_4way":"features/v173/apply-hotfix-terminal-portals-409.py",
 "jei_partial":"features/v173/apply-jei-cosmetic-partial-404.py"
}
for feature,path in scripts.items():
 p=root/path
 assert p.is_file(),(feature,path)
 if path.endswith(".py"):ast.parse(p.read_text(encoding="utf-8"))
 assert ("python3 "+path) in workflow,("not wired into integration workflow",feature,path)

# The patch series must execute in dependency order (preflight steps may
# invoke standalone tests early, so check the final source application).
for first,second in (
 ("apply-uranium-fuel-chain.py","apply-reactor-core-427.py"),
 ("apply-reactor-core-427.py","apply-powerbank-core-429.py"),
 ("apply-nutrition-438.py","apply-nutrinator-gui-461.py"),
 ("apply-nutrinator-gui-461.py","apply-nutripaste-fluid-477.py"),
 ("apply-nightvision-warden-darkness-464.py","apply-network-vision-xray-469.py"),
 ("apply-wip-public-test-476.py","apply-nutripaste-fluid-477.py"),
):
 assert workflow.index("python3 features/v174/"+first) < workflow.index("python3 features/v174/"+second),(first,second)

if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 r=Path(os.environ["V1_RESOURCE_ROOT"])
 expect={
  "reactor/ReactorStructure.java":("64","Result","rods"),
  "reactor/ReactorControllerBlockEntity.java":("water","storedFe","fuel"),
  "reactor/ReactorPortBlockEntity.java":("FluidResource","EnergyHandler"),
  "powerbank/PowerbankBlockEntity.java":("FE","energy"),
  "pump/ElectricWaterPumpBlockEntity.java":("FluidResource","water"),
  "nutrition/NutriPasteFluids.java":("B477_NUTRIPASTE_REAL_FLUID","flowing_nutripaste"),
  "nutrition/NutrinatorBlockEntity.java":("nutrinatorPaste","PASTE_CAPACITY","B477_NUTRIPASTE_TRANSACTIONAL_FLUID"),
  "client/NetworkVisionClient.java":("V174_XRAY_WORLD_WIREFRAME_B469","toggleFromWheel"),
  "blockentity/NetworkDeviceBlockEntity.java":("printer","holo"),
  "client/V174GuidebookScreen.java":("reactor","powerbank"),
 }
 for relative,markers in expect.items():
  src=(j/relative).read_text(encoding="utf-8")
  for marker in markers: assert marker.lower() in src.lower(),(relative,marker)
 # B527: early feature gate runs before the B514 private shape replacement,
 # while final JAR gate runs after it. Preserve both checks, never re-add
 # full-block blue rectangles just to satisfy an obsolete method name.
 vision=(j/"client/NetworkVisionClient.java").read_text(encoding="utf-8")
 if "B514_VISION_CABLE_GEOMETRY" in vision:
  for marker in ("private static void wirePipe(", "private static void pipeAt(",
                 "pipeAt(g,at,state,color,origin,inverse,focal,width,height);"):
   assert marker in vision,("B527 shaped xray cable rendering missing",marker)
  assert "wireCube(g,at" not in vision,"B527 old blue box call returned"
 else:
  assert "wireCube(g,at" in vision,"B527 B469 pre-B514 vision geometry missing"
 main=(j/"ObsidianNetwork.java").read_text(encoding="utf-8")
 for field in ("URANIUM_ORE","URANIUM_INGOT","URANIUM_ROD","NETWORK_PLANTER_ITEM",
               "NETWORK_HOLOGRAM_TERMINAL_ITEM","NETWORK_PRINTER_ITEM",
               "NETWORK_BLUEPRINT","NETWORK_SCHEMATIC_QUILL"):
  assert field in main,field
 for field in ("NETWORK_HOLOGRAM_TERMINAL_ITEM","NETWORK_PRINTER_ITEM",
               "NETWORK_BLUEPRINT","NETWORK_SCHEMATIC_QUILL"):
  assert "output.accept((ItemLike)"+field+".get());" in main,("hidden in creative",field)
 for item in ("network_hologram_terminal","network_printer","network_schematic_quill",
              "uranium_rod","electric_water_pump","nutrinator"):
  assert (r/"data/obsidiannetwork/recipe"/(item+".json")).is_file(),("missing recipe",item)
 # GuideME is now the real building guide. The obsolete legacy book remains
 # registered for save compatibility, but must no longer be craftable or creative.
 guide_meta=(r/"META-INF/neoforge.mods.toml").read_text(encoding="utf-8")
 if 'modId="guideme"' in guide_meta:
  assert not (r/"data/obsidiannetwork/recipe/network_guidebook.json").exists(),"legacy guide recipe returned"
  assert "output.accept((ItemLike)NETWORK_GUIDEBOOK.get());" not in main,"legacy guide creative returned"
  guide=r/"assets/obsidiannetwork/guides/obsidiannetwork/guide"
  for p in ("index.md","reactor.md","powerbank.md","pump.md","assets/reactor_5x5x5.snbt","assets/powerbank_3x3x3.snbt"):
   assert (guide/p).is_file(),("GuideME missing guide asset",p)
  assert 'src="assets/reactor_5x5x5.snbt"' in (guide/"reactor.md").read_text(encoding="utf-8")
  assert 'src="assets/powerbank_3x3x3.snbt"' in (guide/"powerbank.md").read_text(encoding="utf-8")
 else:
  assert (r/"data/obsidiannetwork/recipe/network_guidebook.json").is_file(),"legacy guide recipe missing"
 assert not (j/"compat/jei/WipItemsJeiPlugin.java").exists(),"JEI WIP hidden"
 assert "B409_PORTAL_FOUR_DIRECTIONS" in (j/"portal/PortalGateBlock.java").read_text()
 assert "B404_JEI_COSMETIC_MISSING" in (j/"compat/jei/NetworkStorageRecipeTransferHandler.java").read_text()
 print("B478_FULL_SOURCE_INTEGRATION_GATE_PASS")

p=argparse.ArgumentParser()
p.add_argument("--jar")
p.add_argument("--manifest")
args=p.parse_args()
if args.jar:
 path=Path(args.jar)
 assert path.is_file(),path
 with ZipFile(path) as z:
  present=set(z.namelist())
  needed=(
   "dev/obsidiannetwork/reactor/ReactorControllerBlockEntity.class",
   "dev/obsidiannetwork/reactor/ReactorStructure.class",
   "dev/obsidiannetwork/reactor/ReactorPortBlockEntity.class",
   "dev/obsidiannetwork/powerbank/PowerbankBlockEntity.class",
   "dev/obsidiannetwork/pump/ElectricWaterPumpBlockEntity.class",
   "dev/obsidiannetwork/nutrition/NutrinatorBlockEntity.class",
   "dev/obsidiannetwork/nutrition/NutriPasteFluids.class",
   "dev/obsidiannetwork/client/NetworkVisionClient.class",
   "dev/obsidiannetwork/client/V174GuidebookScreen.class",
   "data/obsidiannetwork/recipe/network_hologram_terminal.json",
   "data/obsidiannetwork/recipe/network_printer.json",
   "data/obsidiannetwork/recipe/network_schematic_quill.json",
   "data/obsidiannetwork/recipe/uranium_rod.json",
   "data/obsidiannetwork/recipe/electric_water_pump.json",
   "data/obsidiannetwork/recipe/nutrinator.json",
  )
  guideme="assets/obsidiannetwork/guides/obsidiannetwork/guide/index.md" in present
  if guideme:
   extra=(
    "assets/obsidiannetwork/guides/obsidiannetwork/guide/reactor.md",
    "assets/obsidiannetwork/guides/obsidiannetwork/guide/powerbank.md",
    "assets/obsidiannetwork/guides/obsidiannetwork/guide/assets/reactor_5x5x5.snbt",
    "assets/obsidiannetwork/guides/obsidiannetwork/guide/assets/powerbank_3x3x3.snbt")
   assert "data/obsidiannetwork/recipe/network_guidebook.json" not in present,"obsolete guide craftable in JAR"
   needed=needed+extra
  else:
   needed=needed+("data/obsidiannetwork/recipe/network_guidebook.json",)
  missing=[name for name in needed if name not in present]
  assert not missing,("B478 missing assembled Java/assets",missing)
 report={
  "version":"1.7.4",
  "status":"full_integrated_in_game_test_candidate",
  "does_not_imply_manual_approval":True,
  "features":sorted(scripts),
  "jar":path.name,
  "verified_classes_and_recipes":list(needed),
  "requires_real_in_game_testing":True
 }
 if args.manifest:
  dest=Path(args.manifest);dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("B478_FULL_JAR_COMPONENT_GATE_PASS")
else:
 print("B478_FULL_STATIC_FEATURE_GATE_PASS")
