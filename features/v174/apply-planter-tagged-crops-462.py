#!/usr/bin/env python3
"""B462: widen modded crop support to tagged age-based plants.

Only blocks marked c:crops with a real numeric AGE property qualify.
No guessed output, arbitrary block cloning or world mutation: native mature
Block.getDrops continues to own all item data and rarity.
"""
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B462_MOD_CROP_DRIFT",rel,s.count(old),old[:130])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
p="blockentity/NetworkPlanterModCrops.java"
edit(p,' private static final TagKey<Block> COMMON_FARMLANDS=TagKey.create(Registries.BLOCK,',
 ''' // B462_TAGGED_AGE_CROP: support modded, non-CropBlock age-based plants
 // ONLY when explicitly included in the common crop block tag.
 private static final TagKey<Block> COMMON_CROPS=TagKey.create(Registries.BLOCK,
       net.minecraft.resources.Identifier.fromNamespaceAndPath("c","crops"));
 private static final TagKey<Block> COMMON_FARMLANDS=TagKey.create(Registries.BLOCK,''')
edit(p,
 ''' public static boolean canGrow(ItemStack soil,ItemStack seed){
  if(crop(seed)==null||soil.isEmpty())return false;''',
 r''' private static net.minecraft.world.level.block.state.properties.IntegerProperty
    ageProperty(Block plant){
  var value=plant.getStateDefinition().getProperty("age");
  return value instanceof net.minecraft.world.level.block.state.properties.IntegerProperty p
   ? p:null;
 }
 private static Block taggedCrop(ItemStack seed){
  if(seed.isEmpty()||NetworkPlanterBlock.Plant.valid(seed))return null;
  if(seed.getItem() instanceof BlockItem blockItem){
   Block plant=blockItem.getBlock();
   if(plant.defaultBlockState().is(COMMON_CROPS)&&ageProperty(plant)!=null)
    return plant;
  }
  var id=BuiltInRegistries.ITEM.getKey(seed.getItem());
  if(id==null||"minecraft".equals(id.getNamespace()))return null;
  if(!seed.is(COMMON_SEEDS)&&!id.getPath().endsWith("_seed")&&
       !id.getPath().endsWith("_seeds"))return null;
  String name=id.getPath();
  String stem=name.endsWith("_seeds")?name.substring(0,name.length()-6):
      name.endsWith("_seed")?name.substring(0,name.length()-5):name;
  for(String suffix:new String[]{"_crop","_plant",""}){
   var block=BuiltInRegistries.BLOCK.getOptional(
     net.minecraft.resources.Identifier.fromNamespaceAndPath(
       id.getNamespace(),stem+suffix)).orElse(null);
   if(block!=null&&block.defaultBlockState().is(COMMON_CROPS)&&
         ageProperty(block)!=null)return block;
  }
  return null;
 }
 public static boolean accepts(ItemStack seed){
  return crop(seed)!=null||taggedCrop(seed)!=null;
 }
 public static boolean canGrow(ItemStack soil,ItemStack seed){
  if(!accepts(seed)||soil.isEmpty())return false;''')
edit(p,
 ''' public static BlockState growthState(ItemStack seed,int phase){
  CropBlock crop=crop(seed);
  if(crop==null)return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
  return crop.getStateForAge(Math.min(crop.getMaxAge(),
        Math.max(0,(crop.getMaxAge()*Math.min(3,Math.max(0,phase))+1)/3)));
 }''',
 r''' public static BlockState growthState(ItemStack seed,int phase){
  CropBlock vanillaStyle=crop(seed);
  int stage=Math.max(0,Math.min(3,phase));
  if(vanillaStyle!=null)
   return vanillaStyle.getStateForAge(Math.min(vanillaStyle.getMaxAge(),
       (vanillaStyle.getMaxAge()*stage+1)/3));
  Block tagged=taggedCrop(seed);
  if(tagged==null)return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
  var age=ageProperty(tagged);
  if(age==null)return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
  int max=age.getPossibleValues().stream().mapToInt(Integer::intValue).max().orElse(0);
  return tagged.defaultBlockState().setValue(age,Math.max(0,(max*stage+1)/3));
 }''')
edit(p,
 '''  CropBlock crop=crop(seed);
  if(crop==null)return List.of();
  BlockState mature=crop.getStateForAge(crop.getMaxAge());''',
 '''  if(!accepts(seed))return List.of();
  BlockState mature=growthState(seed,3);
  if(mature.isAir())return List.of();''')
edit("blockentity/NetworkPlanterBlockEntity.java",
 '||NetworkPlanterModCrops.crop(s)!=null;',
 '||NetworkPlanterModCrops.accepts(s);')
java=(J/p).read_text(encoding="utf-8")
assert 'B462_TAGGED_AGE_CROP' in java
assert 'Block.getDrops(mature,world,pos,null)' in java
assert 'List<ItemStack> rolled' in java
print("B462_PLANTER_TAGGED_CROPS_PASS: c:crops age plants, real loot & 9-slot atomic buffering")
