#!/usr/bin/env python3
"""B457: optional NeoForge/modded CropBlock seed support for Network Planter.

Keeps all vanilla species, saved NBT, upgrades, native cable transfer and
canonical identity unchanged. Detects registered block-backed crops (including
ItemNameBlockItem) and conventional modid:foo_seeds -> modid:foo_crop IDs.
Mature drops come from the *mod's real loot table*, evaluated without placing
or breaking blocks. Transactionally commit full ItemStacks to nine output slots.
"""
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V174_MOD_CROP_DRIFT",rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

helper=J/"blockentity/NetworkPlanterModCrops.java"
assert not helper.exists()
helper.write_text(r'''package dev.obsidiannetwork.blockentity;

import dev.obsidiannetwork.block.NetworkPlanterBlock;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.FarmlandBlock;
import net.minecraft.world.level.block.state.BlockState;

/** B457_MODDED_PLANTER_CROPS: common NeoForge crops without specific mod APIs.
 * Strict opt-in recognition: ONLY real registered CropBlock instances.
 * Never synthesize produce from a seed ID or mutate world blocks.
 */
public final class NetworkPlanterModCrops {
 private NetworkPlanterModCrops(){}
 private static final TagKey<Item> COMMON_SEEDS=TagKey.create(Registries.ITEM,
       Identifier.fromNamespaceAndPath("c","seeds"));
 private static final TagKey<Block> COMMON_FARMLANDS=TagKey.create(Registries.BLOCK,
       Identifier.fromNamespaceAndPath("c","farmlands"));
 public static CropBlock crop(ItemStack seed){
  if(seed.isEmpty()||NetworkPlanterBlock.Plant.valid(seed))return null;
  if(seed.getItem() instanceof BlockItem bi && bi.getBlock() instanceof CropBlock plant)
   return plant;
  var id=BuiltInRegistries.ITEM.getKey(seed.getItem());
  if(id==null || "minecraft".equals(id.getNamespace()))return null;
  String name=id.getPath();
  boolean naming=name.endsWith("_seeds")||name.endsWith("_seed");
  if(!naming&&!seed.is(COMMON_SEEDS))return null;
  String stem=name.endsWith("_seeds")?name.substring(0,name.length()-6):
     name.endsWith("_seed")?name.substring(0,name.length()-5):name;
  // Namespace is always the seed's own mod: never infer an unrelated drop.
  for(String candidate:new String[]{stem+"_crop",stem+"_plant",stem}){
   var key=Identifier.fromNamespaceAndPath(id.getNamespace(),candidate);
   var block=BuiltInRegistries.BLOCK.getOptional(key).orElse(null);
   if(block instanceof CropBlock plant)return plant;
  }
  return null;
 }
 public static boolean canGrow(ItemStack soil,ItemStack seed){
  if(crop(seed)==null||soil.isEmpty())return false;
  if(soil.getItem() instanceof BlockItem bi){
   Block block=bi.getBlock();
   return block instanceof FarmlandBlock ||
      block.defaultBlockState().is(COMMON_FARMLANDS) ||
      block.defaultBlockState().is(net.minecraft.tags.BlockTags.DIRT);
  }
  return false;
 }
 public static boolean acceptsSoil(ItemStack soil){
  if(soil.isEmpty()||!(soil.getItem() instanceof BlockItem bi))return false;
  Block block=bi.getBlock();
  return block instanceof FarmlandBlock ||
       block.defaultBlockState().is(COMMON_FARMLANDS);
 }
 public static BlockState growthState(ItemStack seed,int phase){
  CropBlock crop=crop(seed);
  if(crop==null)return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
  return crop.getStateForAge(Math.min(crop.getMaxAge(),
        Math.max(0,(crop.getMaxAge()*Math.min(3,Math.max(0,phase))+1)/3)));
 }
 public static List<ItemStack> harvest(ServerLevel world,BlockPos pos,ItemStack seed){
  CropBlock crop=crop(seed);
  if(crop==null)return List.of();
  BlockState mature=crop.getStateForAge(crop.getMaxAge());
  // Only Block.getDrops: no setBlock, no spawning, no world inventory mutation.
  List<ItemStack> rolled=Block.getDrops(mature,world,pos,null);
  if(rolled.isEmpty()||rolled.size()>64)return List.of();
  ArrayList<ItemStack> safe=new ArrayList<>();
  int total=0;
  for(ItemStack stack:rolled){
   if(stack.isEmpty())continue;
   total+=stack.getCount();
   if(total>576)return List.of(); // nine-slot storage bound per harvest
   safe.add(stack.copy()); // preserve components, modded NBT, max stack size
  }
  return safe;
 }
}
''',encoding="utf-8")

# The 9-slot GUI & manual insertion will accept real modded seeds/soil.
edit("blockentity/NetworkPlanterBlockEntity.java",
 " private static boolean seed(ItemStack s){return NetworkPlanterBlock.Plant.valid(s);}",
 """ // B457_MOD_SEED_ACCEPT: prefer fixed vanilla table; allow real modded crops.
 private static boolean seed(ItemStack s){return NetworkPlanterBlock.Plant.valid(s)
   ||NetworkPlanterModCrops.crop(s)!=null;}""")
edit("blockentity/NetworkPlanterBlockEntity.java",
 " private boolean pair(){\n  if(soil.isEmpty()||seed.isEmpty())return false;",
 """  private boolean pair(){
   if(soil.isEmpty()||seed.isEmpty())return false;
   if(!NetworkPlanterBlock.Plant.valid(seed))
    return NetworkPlanterModCrops.canGrow(soil,seed);""")
# Existing soil whitelist already handles vanilla dirt/farmland, and modded
# farmland tags / classes are optional extras.
soilfile=J/"blockentity/NetworkPlanterBlockEntity.java"
s=soilfile.read_text(encoding="utf-8")
key='||s.is(Blocks.CRIMSON_NYLIUM.asItem())||s.is(Blocks.WARPED_NYLIUM.asItem());'
assert s.count(key)==1,("B457_SOIL_DRIFT",s.count(key))
soilfile.write_text(s.replace(key,key[:-1]+'\n       ||NetworkPlanterModCrops.acceptsSoil(s);',1),encoding="utf-8")

# Atomic multi-stack insertion mirrors old vanilla fits()+store() but keeps
# each loot-generated ItemStack's exact data components (e.g. custom foods).
edit("blockentity/NetworkPlanterBlockEntity.java",
 " private boolean fits(Map<Item,Integer> drops){",
 r''' // B457_MOD_CROP_ATOMIC: simulate into copies first, commit only if
 // every component-bearing drop fits; no partial insertion/duplication.
 private boolean storeModded(java.util.List<ItemStack> drops){
  ItemStack[] trial=new ItemStack[9];
  for(int i=0;i<9;i++)trial[i]=output[i].copy();
  for(ItemStack source:drops){
   int remaining=source.getCount();
   if(source.isEmpty())continue;
   for(int i=0;i<9&&remaining>0;i++){
    ItemStack current=trial[i];
    if(current.isEmpty()||!ItemStack.isSameItemSameComponents(current,source))continue;
    int moved=Math.min(remaining,current.getMaxStackSize()-current.getCount());
    if(moved>0){current.grow(moved);remaining-=moved;}
   }
   for(int i=0;i<9&&remaining>0;i++){
    if(!trial[i].isEmpty())continue;
    int moved=Math.min(remaining,source.getMaxStackSize());
    if(moved>0){trial[i]=source.copyWithCount(moved);remaining-=moved;}
   }
   if(remaining!=0)return false;
  }
  for(int i=0;i<9;i++)output[i]=trial[i];
  sync();return true;
 }
 private boolean fits(Map<Item,Integer> drops){''')
edit("blockentity/NetworkPlanterBlockEntity.java",
 "  Map<Item,Integer> batch=be.harvest(world);",
 r'''   if(!NetworkPlanterBlock.Plant.valid(be.seed)){
    java.util.List<ItemStack> batch=NetworkPlanterModCrops.harvest(world,pos,be.seed);
    // Fail closed when the mod provides no mature drops or requires an
    // unsupported special crop mechanism; never guess fake produce.
    if(batch.isEmpty()||!be.storeModded(batch)){
     if(!be.stalled){be.stalled=true;be.sync();}
     return;
    }
    be.progress=0;be.harvests++;be.stalled=false;be.phase();
    be.flush(world);
    return;
   }
   Map<Item,Integer> batch=be.harvest(world);''')

# Existing native pot renderer can show registered modded crop states rather
# than wrongly rendering vanilla wheat or hiding the inserted mod crop.
edit("client/NetworkPlanterRenderer.java",
 "  if(out.species==NetworkPlanterBlock.Plant.EMPTY)return;",
 r'''  if(out.species==NetworkPlanterBlock.Plant.EMPTY){
   if(be.seedStack().isEmpty())return;
   BlockState modded=dev.obsidiannetwork.blockentity.NetworkPlanterModCrops.growthState(
     be.seedStack(),out.age);
   if(modded.isAir())return;
   resolver.update(out.plantModel,modded,DISPLAY_CONTEXT);
   out.tree=false;out.active=true;return;
  }''')
for path in (helper,soilfile,J/"client/NetworkPlanterRenderer.java"):
 assert path.exists()
assert "V173_PLANTER_EXACT_ITEM_KEY" in soilfile.read_text()
assert "V173_PLANTER_LEGACY_MIGRATION" in soilfile.read_text()
print("B457_PLANTER_MOD_CROPS_APPLIED: real modded CropBlock drops, atomic nine-slot buffer and native crop render")
