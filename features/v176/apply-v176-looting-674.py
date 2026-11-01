#!/usr/bin/env python3
"""B674: Micro-MG Looting I-III anvil support and roundtrip persistence.
Preserves every other upgrade card and rejects duplicate/changed source anchors.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def replace(rel,old,new):
 p=J/rel
 src=p.read_text(encoding="utf-8")
 assert src.count(old)==1,("V176_B674_SOURCE_DRIFT",rel,src.count(old),old[:100])
 p.write_text(src.replace(old,new,1),encoding="utf-8")

replace("powerarmor/UpgradeCardItem.java",
 ' public UpgradeCardItem(Properties p,String id){super(p.stacksTo(16));this.upgradeId=id;}',
 ''' public UpgradeCardItem(Properties p,String id){super(setup(p,id));this.upgradeId=id;}
 private static Properties setup(Properties p,String id){
  p.stacksTo("micro_mg".equals(id)?1:16);
  if("micro_mg".equals(id))
   p.component(net.minecraft.core.component.DataComponents.ENCHANTMENTS,
      net.minecraft.world.item.enchantment.ItemEnchantments.EMPTY);
  return p;
 }
 @Override public boolean supportsEnchantment(net.minecraft.world.item.ItemStack stack,
       net.minecraft.core.Holder<net.minecraft.world.item.enchantment.Enchantment> enchantment){
  if("micro_mg".equals(upgradeId))
   return enchantment.is(net.minecraft.world.item.enchantment.Enchantments.LOOTING);
  return super.supportsEnchantment(stack,enchantment);
 }
 @Override public boolean isPrimaryItemFor(net.minecraft.world.item.ItemStack stack,
       net.minecraft.core.Holder<net.minecraft.world.item.enchantment.Enchantment> enchantment){
  if("micro_mg".equals(upgradeId))return false; // anvil only, never random enchanting
  return super.isPrimaryItemFor(stack,enchantment);
 }''')
replace("powerarmor/ArmorStationBlock.java",
 'installed.isEmpty()?card.upgradeId:installed+","+card.upgradeId);',
 '        V176LootingSupport.install(installed,card.upgradeId,held,p.registryAccess()));')
replace("powerarmor/ArmorStationBlock.java",
 'if(!p.getInventory().add(new ItemStack(cardItem))){',
 '''      ItemStack returned=new ItemStack(cardItem);
      if("micro_mg".equals(removed))
       V176LootingSupport.restore(returned,installed,p.registryAccess());
      if(!p.getInventory().add(returned)){''')
replace("powerarmor/ArmorStationBlock.java",
 'left.remove(i);',
 '''      left.remove(i);
      if("micro_mg".equals(removed))
       left.removeIf(V176LootingSupport::isLootingToken);''')
replace("powerarmor/ArmorStationMenu.java",
 'ItemStack disk=new ItemStack(PowerArmorCards.item(id));',
 '''      ItemStack disk=new ItemStack(PowerArmorCards.item(id));
      if("micro_mg".equals(id))
       V176LootingSupport.restore(disk,String.join(",",values),owner.registryAccess());''')
replace("powerarmor/ArmorStationMenu.java",
 'values.remove(i);',
 '''    ItemStack returned=new ItemStack(item);
    boolean micro="micro_mg".equals(values.get(i));
    if(micro)V176LootingSupport.restore(returned,String.join(",",values),owner.registryAccess());
    values.remove(i);
    if(micro)values.removeIf(V176LootingSupport::isLootingToken);''')
replace("powerarmor/ArmorStationMenu.java",
 'setCarried(new ItemStack(item));',
 '    setCarried(returned);')
replace("powerarmor/ArmorStationMenu.java",
 'values.add(insertion,card.upgradeId);',
 '''    values.add(insertion,card.upgradeId);
    if("micro_mg".equals(card.upgradeId)){
     int loot=V176LootingSupport.itemLevel(carried,owner.registryAccess());
     if(loot>0)values.add(insertion+1,"micro_mg_looting_"+loot);
    }''')
replace("powerarmor/ArmorStationMenu.java",
 'for(int n=0;n<take;n++)values.add(card.upgradeId);',
 '''   for(int n=0;n<take;n++){
    values.add(card.upgradeId);
    if("micro_mg".equals(card.upgradeId)){
     int loot=V176LootingSupport.itemLevel(stack,owner.registryAccess());
     if(loot>0)values.add("micro_mg_looting_"+loot);
    }
   }''')

source=J/"powerarmor/V176LootingSupport.java"
assert not source.exists()
source.write_text("""package dev.obsidiannetwork.powerarmor;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantments;

/** Persist anvil Looting without cloning an armor upgrade item or altering its NBT. */
public final class V176LootingSupport {
 private V176LootingSupport(){}
 private static final String PREFIX="micro_mg_looting_";
 public static boolean isLootingToken(String s){return s!=null&&s.startsWith(PREFIX);}
 public static int level(String installed){
  if(installed==null||installed.isEmpty())return 0;
  boolean module=false;
  int found=0;
  for(String t:installed.split(",")){
   if(t.equals("micro_mg"))module=true;
   if(isLootingToken(t)){
    String raw=t.substring(PREFIX.length());
    if(raw.length()==1&&raw.charAt(0)>='1'&&raw.charAt(0)<='3')
     found=Math.max(found,raw.charAt(0)-'0');
   }
  }
  return module?found:0;
 }
 public static int itemLevel(ItemStack input,HolderLookup.Provider registries){
  var holder=registries.lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.LOOTING);
  return Math.max(0,Math.min(3,input.getEnchantmentLevel(holder)));
 }
 public static String install(String installed,String upgradeId,ItemStack input,
                              HolderLookup.Provider registries){
  String prior=installed==null?"":installed;
  String result=prior.isEmpty()?upgradeId:prior+","+upgradeId;
  if(!"micro_mg".equals(upgradeId))return result;
  int n=itemLevel(input,registries);
  return n==0?result:result+","+PREFIX+n;
 }
 public static void restore(ItemStack card,String installed,HolderLookup.Provider registries){
  int n=level(installed);
  if(n<=0)return;
  var holder=registries.lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.LOOTING);
  card.enchant(holder,n);
 }
}
""",encoding="utf-8")
source=J/"powerarmor/V176LootingEvents.java"
assert not source.exists()
source.write_text("""package dev.obsidiannetwork.powerarmor;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.enchantment.Enchantments;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.enchanting.EnchantedEntityLootEvent;

/** Use the real vanilla loot tables rather than inventing after-death bonus drops. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176LootingEvents {
 private V176LootingEvents(){}
 public static final String SHOT_PREFIX="xsxlabs_micro_mg_looting_";
 public static void mark(Projectile shot,int looting){
  if(looting>=1&&looting<=3)shot.addTag(SHOT_PREFIX+looting);
 }
 public static int level(Entity shot){
  if(!(shot instanceof Projectile))return 0;
  for(int n=3;n>=1;n--)
   if(shot.entityTags().contains(SHOT_PREFIX+n))return n;
  return 0;
 }
 @SubscribeEvent public static void onLoot(EnchantedEntityLootEvent event){
  if(!event.getEnchantment().is(Enchantments.LOOTING))return;
  Entity direct=event.getDamageSource().getDirectEntity();
  int n=level(direct);
  if(n>event.getEnchantmentLevel())event.setEnchantmentLevel(n);
 }
}
""",encoding="utf-8")
print("V176_B674_LOOTING_ANVIL_AND_STATION_ROUNDTRIP_PASS")
