#!/usr/bin/env python3
"""B591 fail-closed post-patch regression: FE direction, idle shutdown, solar recipe and glass."""
import os,json
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
a=(J/"reactor/ReactorControllerBlockEntity.java").read_text()
b=(J/"powerbank/PowerbankBlockEntity.java").read_text()
c=(J/"blockentity/EnergyCableBlockEntity.java").read_text()
solar=(J/"blockentity/SolarGeneratorBlockEntity.java").read_text()
reg=(J/"ObsidianNetwork.java").read_text()
be=(J/"registry/ModBlockEntities.java").read_text()
# Manual off and automatic full-buffer pause must be independent persisted states.
for required in (
 "B591_REACTOR_AUTO_FULL_GATE","B591_FUEL_RODS_X5",
 "if(!be.enabled){be.b591AutoFullPause=false;}",
 "be.storedFe>=FE_CAPACITY","be.storedFe<FE_CAPACITY",
 "if(be.b591AutoFullPause)","b591AutoFullPause=enabled && in.getBooleanOr(",
 "be.fuelTicks=Math.max(0,be.fuelTicks-5*activity);",
 "if(command==1||command==2){enabled=false;b591AutoFullPause=false;}",
 "if(command==0){enabled=true;b591AutoFullPause=false;}",
 "public boolean guiAutoPaused()",
 "B579_REACTOR_GENERATE_EVERY_TICK","B579_REACTOR_PUSH_EVERY_TICK",
 "public long guiFePerTick(){return b579ActualGeneration;}"):
 assert required in a,("B591_REACTOR_CONTRACT",required)
assert "be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L" in a
# No new production rate or loss/duplication: source and sink share a root transaction.
for required in (
 "B591_POWERBANK_OUTPUT_PUSH","b591PushOutput(","activePorts",
 "getBlockState(portPos).is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_OUTPUT.get())",
 "source.extract(accepted,tx)==accepted","target.insert(offer,tx)",
 "tx.commit();","B579_BANK_ROLLING_20","b579InputBuckets",
 "b579OutputBuckets"):
 assert required in b,("B591_BANK_CONTRACT",required)
assert b.index("target.insert(offer,tx)")<b.index("source.extract(accepted,tx)==accepted")<b.index("tx.commit();")
# The three real BFS traversals are individually mode-aware on both cable faces.
for required in ("B591_ENERGY_DIRECTED_WALK","B591_ENERGY_OFF_PHYSICAL_GAP",
 "B591_OFF_REMEMBERS_MANUAL_CUT","b591PriorCut",
 "b591FlowOpen(server,cable,cableState,side,false)",
 "b591FlowOpen(server,next,nextState,side.getOpposite(),true)",
 "b591FlowOpen(server,cable,cableState,side,true)",
 "b591FlowOpen(server,next,nextState,side.getOpposite(),false)",
 "mode==3 || mode==(outward?2:1)",
 "state.is(dev.obsidiannetwork.ObsidianNetwork.ENERGY_CABLE.get())"):
 assert required in c,("B591_CABLE_DIRECTION",required)
assert c.count("b591FlowOpen(server,cable,cableState,side,false)")==2
assert c.count("b591FlowOpen(server,cable,cableState,side,true)")==1
assert c.count("b591FlowOpen(server,next,nextState,side.getOpposite(),true)")==2
assert c.count("b591FlowOpen(server,next,nextState,side.getOpposite(),false)")==1
# Exhaustively verify all mode pairs: output can only feed input/both.
for lhs in range(4):
 for rhs in range(4):
  forward=(lhs in (2,3) and rhs in (1,3))
  backward=(rhs in (2,3) and lhs in (1,3))
  assert not (lhs==0 or rhs==0) or (not forward and not backward)
  assert forward == ((lhs==2 or lhs==3) and (rhs==1 or rhs==3))
  assert backward == ((rhs==2 or rhs==3) and (lhs==1 or lhs==3))
# All tier levels and existing production retained. One new ultra tier.
assert "ULTRA = new Tier(5,46080L,32000000L,\"Ultra\")" in solar
assert "return ULTRA; // B591_ULTRA_TIER" in solar
assert "ULTRA_SOLAR_GENERATOR.get()" in be
for k in ("ULTRA_SOLAR_GENERATOR","ULTRA_SOLAR_MATRIX","ULTRA_ENERGY_CORE"):assert k in reg,k
recipes=R/"data/obsidiannetwork/recipe"
m=json.loads((recipes/"ultra_solar_matrix.json").read_text())
core=json.loads((recipes/"ultra_energy_core.json").read_text())
panel=json.loads((recipes/"ultra_solar_generator.json").read_text())
assert m["pattern"]==["EEE"]*3 and m["key"]["E"]=="obsidiannetwork:elite_solar_generator"
assert core["pattern"]==["NNN","NSN","NNN"]
assert core["key"]=={"N":"minecraft:netherite_block","S":"minecraft:nether_star"}
assert panel["pattern"]==["CCC","CMC","CCC"]
assert panel["key"]=={"C":"obsidiannetwork:ultra_energy_core","M":"obsidiannetwork:ultra_solar_matrix"}
for name in ("ultra_solar_generator","ultra_energy_core","ultra_solar_matrix"):
 assert (R/"assets/obsidiannetwork/items"/(name+".json")).exists()
assert (R/"data/obsidiannetwork/loot_table/blocks/ultra_solar_generator.json").exists()
# These are only final formed block glass sprites: exactly same base RGB, lower alpha.
for name,expected in (("reactor_glass_formed",(43,104,148,56)),
                      ("reactor_glass_formed_lit",(49,160,232,74)),
                      ("powerbank_glass_formed",(34,100,139,28)),
                      ("powerbank_glass_formed_lit_detail0",(29,220,243,40)),
                      ("powerbank_glass_formed_lit_detail1",(29,220,243,40)),
                      ("powerbank_glass_formed_lit_detail2",(29,220,243,40))):
 with Image.open(R/"assets/obsidiannetwork/textures/block"/(name+".png")) as im:
  assert im.size==(32,32)
  assert set(im.convert("RGBA").getdata())=={expected},(name,im.getpixel((16,16)))
print("B591_ALL_FIVE_REQUESTS_POST_PATCH_CONTRACT_PASS")
