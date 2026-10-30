#!/usr/bin/env python3
"""B477: real registry NutriPaste Fluid + output-only transactional fluid cable port.

Preserve 1_000_000 bucket internal paste storage, helmet Feeding Card, food
conversion, save-data keys and existing GUI. Never expose food/paste as FE.
"""
import json
import os
import struct
import zlib
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

def once(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B477_SOURCE_DRIFT",rel,s.count(old),old[:90])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def add(rel,body):
 p=J/rel
 assert not p.exists(),("B477_JAVA_COLLISION",str(p))
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(body,encoding="utf-8")

add("nutrition/NutriPasteFluids.java",r'''package dev.obsidiannetwork.nutrition;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.fluids.BaseFlowingFluid;
import net.neoforged.neoforge.fluids.FluidType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/** B477_NUTRIPASTE_REAL_FLUID: independently registered food paste.
 * Stored internally as a long 1,000,000-bucket reservoir, moved as native
 * FluidResource in transactions; no water substitution or synthetic FE.
 */
public final class NutriPasteFluids {
 private NutriPasteFluids(){}
 public static final DeferredRegister<FluidType> FLUID_TYPES =
     DeferredRegister.create(NeoForgeRegistries.FLUID_TYPES,"obsidiannetwork");
 public static final DeferredRegister<Fluid> FLUIDS =
     DeferredRegister.create(Registries.FLUID,"obsidiannetwork");
 public static final DeferredHolder<FluidType,FluidType> TYPE =
     FLUID_TYPES.register("nutripaste",id -> new FluidType(
       FluidType.Properties.create()
          .descriptionId(net.minecraft.Util.makeDescriptionId("fluid",id))
          .canSwim(false)));
 public static final DeferredHolder<Fluid,BaseFlowingFluid.Source> SOURCE =
     FLUIDS.register("nutripaste",() -> new BaseFlowingFluid.Source(NutriPasteFluids.PROPERTIES));
 public static final DeferredHolder<Fluid,BaseFlowingFluid.Flowing> FLOWING =
     FLUIDS.register("flowing_nutripaste",() -> new BaseFlowingFluid.Flowing(NutriPasteFluids.PROPERTIES));
 public static final BaseFlowingFluid.Properties PROPERTIES =
     new BaseFlowingFluid.Properties(TYPE,SOURCE,FLOWING);
 public static void register(IEventBus eventBus){
  FLUID_TYPES.register(eventBus);
  FLUIDS.register(eventBus);
 }
}
''')

once("ObsidianNetwork.java",
 "      BLOCKS.register(modEventBus);",
 "      BLOCKS.register(modEventBus);\n      dev.obsidiannetwork.nutrition.NutriPasteFluids.register(modEventBus);")

once("nutrition/NutrinatorBlockEntity.java",
 '  public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}',
 '''  public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}
  // B477_NUTRIPASTE_TRANSACTIONAL_FLUID: no paste created by external pipes.
  // One real NutriPaste tank, output only, independent from the FE inventory.
  private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> pasteJournal =
    new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
     @Override protected Long createSnapshot(){return paste;}
     @Override protected void revertToSnapshot(Long old){paste=old;}
     @Override protected void onRootCommit(Long old){if(old!=paste)setChanged();}
    };
  private final net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> pastePort =
    new net.neoforged.neoforge.transfer.ResourceHandler<>() {
     private net.neoforged.neoforge.transfer.fluid.FluidResource pasteResource(){
      return net.neoforged.neoforge.transfer.fluid.FluidResource.of(NutriPasteFluids.SOURCE.get());
     }
     @Override public int size(){return 1;}
     @Override public net.neoforged.neoforge.transfer.fluid.FluidResource getResource(int i){
      java.util.Objects.checkIndex(i,1);
      return paste>0L?pasteResource():net.neoforged.neoforge.transfer.fluid.FluidResource.EMPTY;
     }
     @Override public long getAmountAsLong(int i){java.util.Objects.checkIndex(i,1);return paste;}
     @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
      java.util.Objects.checkIndex(i,1);return pasteResource().equals(r);
     }
     @Override public long getCapacityAsLong(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
      java.util.Objects.checkIndex(i,1);
      return r.isEmpty()||isValid(i,r)?PASTE_CAPACITY:0L;
     }
     @Override public int insert(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
        net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
      java.util.Objects.checkIndex(i,1);return 0;
     }
     @Override public int extract(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
        net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
      java.util.Objects.checkIndex(i,1);
      if(n<=0||paste<=0L||!isValid(i,r))return 0;
      int given=(int)Math.min((long)n,paste);
      if(given>0){pasteJournal.updateSnapshots(tx);paste-=given;}
      return given;
     }
    };
  public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> fluidPort(){return pastePort;}''')

once("nutrition/NutrinatorCapabilities.java",
 '   e.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.NUTRINATOR.get(),',
 '''   e.registerBlockEntity(Capabilities.Fluid.BLOCK,ModBlockEntities.NUTRINATOR.get(),
     (be,side)->be.fluidPort());
   e.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.NUTRINATOR.get(),''')

# Asset/translation IDs: the 26.1 FluidModel can also be supplied by a tank UI.
# The machine itself already has synchronized paste/helmet bars.
for lang,label in (("en_us","NutriPaste"),("de_de","Nährpaste")):
 path=R/("assets/obsidiannetwork/lang/"+lang+".json")
 data=json.loads(path.read_text(encoding="utf-8"))
 data["fluid.obsidiannetwork.nutripaste"]=label
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

assert "nutrinatorPaste" in (J/"nutrition/NutrinatorBlockEntity.java").read_text()
assert "B477_NUTRIPASTE_REAL_FLUID" in (J/"nutrition/NutriPasteFluids.java").read_text()
print("B477_NUTRIPASTE_REAL_FLUID_PASS: native fluid registry, transactional pipe extraction, saved 1m bucket tank")
