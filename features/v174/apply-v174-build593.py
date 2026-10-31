#!/usr/bin/env python3
"""Build 593: user feedback after green B592, minimal post-B591 modifications."""
import os,re,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
T=Path(__file__).resolve().parents[2]/"tests"
def edit(path,old,new,required=True):
 p=J/path
 s=p.read_text(encoding="utf-8")
 if required: assert s.count(old)==1,("B593_DRIFT",str(p),s.count(old),old[:125])
 else: assert old in s,("B593_NOT_FOUND",str(p),old[:125])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def modify(path,fn):
 p=J/path;s=p.read_text(encoding="utf-8");out=fn(s);assert out!=s,("B593_NO_CHANGE",str(p));p.write_text(out,encoding="utf-8")
# A rod loaded in the reactor runs for exactly 600 active ticks (30 s @ 20TPS).
# Automatic full-store pauses and manually disabled states remain excluded.
p=J/"reactor/ReactorControllerBlockEntity.java";s=p.read_text(encoding="utf-8")
assert s.count("be.fuelTicks=Math.max(0,be.fuelTicks-5*activity);")==1
s=s.replace("be.fuelTicks=Math.max(0,be.fuelTicks-5*activity); // B591_FUEL_RODS_X5",
            "be.fuelTicks=Math.max(0,be.fuelTicks-activity); // B593_ROD_600_ACTIVE_TICKS")
n=s.count("be.fuelTicks=12_000;")
assert n==1,("B593_ROD_LOAD",n)
s=s.replace("be.fuelTicks=12_000;","be.fuelTicks=600; // B593_30_SECONDS",1)
p.write_text(s,encoding="utf-8")
# Repair exact mandatory upstream regression expectations, not remove the checks.
p=T/"verify_v174_build591_contract.py";s=p.read_text(encoding="utf-8")
assert "B591_FUEL_RODS_X5" in s and "-5*activity" in s
s=s.replace('"B591_FUEL_RODS_X5"','"B593_ROD_600_ACTIVE_TICKS"')
s=s.replace("be.fuelTicks-5*activity","be.fuelTicks-activity")
s=s.replace("assert \"be.rodAssemblies*600L*", "assert \"be.rodAssemblies*600L*")
p.write_text(s,encoding="utf-8")
p=T/"verify_v174_ingame_smooth_579.py";s=p.read_text(encoding="utf-8")
assert "be.fuelTicks-5*activity" in s
s=s.replace("be.fuelTicks-5*activity","be.fuelTicks-activity")
p.write_text(s,encoding="utf-8")
# Nutrinator: 1 million mB, with old-world surplus preserved instead of silently clipped.
p=J/"nutrition/NutrinatorBlockEntity.java";s=p.read_text(encoding="utf-8")
assert s.count("PASTE_CAPACITY=1_000_000_000L")==1,("B593_NUTRI_CAP_DRIFT",s.count("PASTE_CAPACITY"))
s=s.replace("PASTE_CAPACITY=1_000_000_000L","PASTE_CAPACITY=1_000_000L",1)
old='paste=Math.max(0L,Math.min(PASTE_CAPACITY,in.getLongOr("nutrinatorPaste",0L)));'
assert s.count(old)==1,"B593_NUTRI_LOAD_DRIFT"
s=s.replace(old,'paste=Math.max(0L,in.getLongOr("nutrinatorPaste",0L)); // B593_PRESERVE_LEGACY_SURPLUS',1)
# No production while a legacy surplus exceeds the new capacity; helmet and pipe drain it safely.
p.write_text(s,encoding="utf-8")
# Nutripaste cannot be bottled into buckets from the Network Tank.
p=J/"blockentity/NetworkTankBlockEntity.java";s=p.read_text(encoding="utf-8")
old='  var result=held.getFluid().getBucket();'
assert s.count(old)==1,("B593_BUCKET_PRODUCTION_DRIFT",s.count(old))
s=s.replace(old,'''  // B593_NO_NUTRIPASTE_BUCKETS: paste only goes into compatible Power Armor helmets.
  if(held.getFluid()==dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get())return;
'''+old,1)
p.write_text(s,encoding="utf-8")
# No new filled NutriPaste buckets are possible through the fluid registration.
p=J/"nutrition/NutriPasteFluids.java";s=p.read_text(encoding="utf-8")
old='.bucket(()->dev.obsidiannetwork.ObsidianNetwork.NUTRIPASTE_BUCKET.get())'
assert s.count(old)==1,("B593_PASTE_BUCKET_REG_DRIFT",s.count(old))
s=s.replace(old,"/* B593_NO_PASTE_BUCKET_ASSOCIATION */",1)
p.write_text(s,encoding="utf-8")
# Ultra panel: like the other instant hand-breakable mod blocks, self drops retained.
p=J/"ObsidianNetwork.java";s=p.read_text(encoding="utf-8")
old='BLOCKS.registerBlock("ultra_solar_generator",dev.obsidiannetwork.block.SolarGeneratorBlock::new,\n         p -> p.mapColor(MapColor.METAL).strength(3.0F,9.0F).requiresCorrectToolForDrops());'
assert s.count(old)==1,("B593_INSTANT_ULTRA",s.count(old))
s=s.replace(old,'BLOCKS.registerBlock("ultra_solar_generator",dev.obsidiannetwork.block.SolarGeneratorBlock::new,\n         p -> p.mapColor(MapColor.METAL).strength(0.0F,0.0F));',1)
p.write_text(s,encoding="utf-8")
# Tooltip event: present actual B591 tier production/buffer and its matching target
# transfer budget. This event does not tick or scan the world.
p=J/"client/UltraSolarTooltip.java"
assert not p.exists()
p.write_text('''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.network.chat.Component;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;
/** B593_ULTRA_TOOLTIP: visible in player inventory and EMI/JEI when event-based. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class UltraSolarTooltip {
 private UltraSolarTooltip(){}
 @SubscribeEvent public static void show(ItemTooltipEvent e){
  if(!e.getItemStack().is(ObsidianNetwork.ULTRA_SOLAR_GENERATOR_ITEM.get()))return;
  e.getToolTip().add(Component.literal("Produktion: 46.080 FE/t"));
  e.getToolTip().add(Component.literal("Speicher: 32.000.000 FE"));
  e.getToolTip().add(Component.literal("Transferlimit: 46.080 FE/t (Zielwert)"));
  e.getToolTip().add(Component.literal("Rezept: 9 Elite Solar Panels + 8 Ultra Energy Cores"));
 }
}
''',encoding="utf-8")
# Make existing face OFF transition recalculate neighbor arms immediately on server.
p=J/"blockentity/EnergyCableBlockEntity.java";s=p.read_text(encoding="utf-8")
old='if(st.getValue(cut)!=closed)level.setBlock(worldPosition,st.setValue(cut,closed),3);'
assert s.count(old)==1,("B593_OFF_CUT_ANCHOR",s.count(old))
s=s.replace(old,'''if(st.getValue(cut)!=closed){
      level.setBlock(worldPosition,st.setValue(cut,closed),3);
      level.updateNeighborsAt(worldPosition,st.getBlock());
      // B593_OFF_REBUILD_ADJACENCY: client arms and vanilla neighbor shape.
      level.sendBlockUpdated(worldPosition,st,level.getBlockState(worldPosition),3);
     }''',1)
# A disconnected face also refuses direct endpoint energy and network traversal.
assert "B591_ENERGY_DIRECTED_WALK" in s
assert "canEnergyWire(ServerLevel" in s
p.write_text(s,encoding="utf-8")
# Print only minimal diagnostics for the unresolved Network Tank GUI, no behavior changed.
for path in ("menu/NetworkTankMenu.java","client/NetworkTankScreen.java",
             "blockentity/NetworkTankBlockEntity.java","blockentity/SolarGeneratorBlockEntity.java"):
 content=(J/path).read_text(encoding="utf-8")
 print("B593_SOURCE_INSPECT",path,"LENGTH",len(content))
 for line in content.splitlines():
  if any(w in line for w in ("addDataSlots(","DataSlot","ContainerData","getData(","storedMb","getFluidInTank","fluidAmount",
                               "guiPaste","getUpdatePacket","public static final Tier","transferLimit")):
   print("B593_SOURCE_LINE",path,line.strip()[:240])
# Fail-closed checks on output assets and effective postpatch Java.
assert "PASTE_CAPACITY=1_000_000L" in (J/"nutrition/NutrinatorBlockEntity.java").read_text()
assert "be.fuelTicks=600;" in (J/"reactor/ReactorControllerBlockEntity.java").read_text()
assert '"ultra_solar_generator"' in (R/"data/obsidiannetwork/recipe/ultra_solar_generator.json").read_text()
assert (R/"data/obsidiannetwork/loot_table/blocks/ultra_solar_generator.json").is_file()
print("B593_FUEL_30S_NUTRIPASTE_1M_NO_BUCKETS_ULTRA_TOOLTIP_INSTANT_OFF_REFRESH_PASS")
