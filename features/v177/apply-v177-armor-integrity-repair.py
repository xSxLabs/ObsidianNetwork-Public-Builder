#!/usr/bin/env python3
"""v1.7.7 core: nonbreaking suit integrity, native 200k FE station and extra HUD.

Fail closed against final reconstructed 1.7.7 source; do not alter v1.7.6.
Run near the END of the v1.7.6 reconstruction, before Gradle compilation.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def replace(rel,old,new):
 p=root/rel
 source=p.read_text(encoding="utf-8")
 assert source.count(old)==1,("V177_SOURCE_DRIFT",rel,old[:120],source.count(old))
 p.write_text(source.replace(old,new,1),encoding="utf-8")

def add(rel,source):
 p=root/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V177_DUPLICATE_CLASS",rel)
 p.write_text(source,encoding="utf-8")

# Persist real FE inside the SAME station BE; generic input capability is
# shared by the mod's Energy Cable and by other NeoForge 26.1 energy mods.
replace("powerarmor/ArmorStationBlockEntity.java",
 "public final class ArmorStationBlockEntity extends BlockEntity {",
 """public final class ArmorStationBlockEntity extends BlockEntity {
 // V177_STATION_200000_FE: transaction-rollback-aware input-only handler.
 private final net.neoforged.neoforge.transfer.energy.SimpleEnergyHandler v177Energy =
   new net.neoforged.neoforge.transfer.energy.SimpleEnergyHandler(200000,200000,0){
    @Override protected void onEnergyChanged(int previous){ArmorStationBlockEntity.this.setChanged();}
   };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler v177Energy(){return v177Energy;}
 public int v177StoredFe(){return (int)v177Energy.getAmountAsLong();}
 public int v177ConsumeFe(int requested){
  int used=Math.max(0,Math.min(v177StoredFe(),requested));
  if(used>0)v177Energy.set(v177StoredFe()-used);
  return used;
 }
""")
replace("powerarmor/ArmorStationBlockEntity.java",
 "  super.saveAdditional(out);",
 """  super.saveAdditional(out);
  out.putInt("v177_armor_station_fe",v177StoredFe());""")
replace("powerarmor/ArmorStationBlockEntity.java",
 "  super.loadAdditional(in);",
 """  super.loadAdditional(in);
  v177Energy.set(Math.max(0,Math.min(200000,in.getIntOr("v177_armor_station_fe",0))));""")
replace("powerarmor/ArmorStationBlockEntity.java",
 " public static void serverTick(net.minecraft.world.level.Level level,BlockPos pos,BlockState state,ArmorStationBlockEntity be){",
 """ public static void serverTick(net.minecraft.world.level.Level level,BlockPos pos,BlockState state,ArmorStationBlockEntity be){
  // V177_REPAIR_TICK: no extra ticker, no chunk scan and no FE burn at idle.
  if(level instanceof net.minecraft.server.level.ServerLevel server
      && server.getGameTime()%5L==0L)
    V177ArmorIntegrity.repairNearby(server,pos,be);""")
replace("backpack/V176BackpackCableCapability.java",
 " public static void register(RegisterCapabilitiesEvent event){",
 """ public static void register(RegisterCapabilitiesEvent event){
  // V177_STATION_NATIVE_ENERGY_INPUT: no output/extract path.
  event.registerBlockEntity(Capabilities.Energy.BLOCK,
      ModBlockEntities.ARMOR_STATION.get(),
      (station,side)->station.v177Energy());""")

# Powered armor abilities must respect structural failure.
replace("powerarmor/PowerArmorRuntime.java",
 """ public static boolean powered(ServerPlayer p){
  if(!full(p))return false;""",
 """ public static boolean powered(ServerPlayer p){
  if(!full(p)||V177ArmorIntegrity.failed(p))return false;""")

# 3rd meter immediately ABOVE Paste, matching existing bottom-left FE/Paste.
replace("client/PowerArmorBuild98Client.java",
 '   String pasteLabel="PASTE";',
 '''   // V177_INTEGRITY_ABOVE_PASTE (single combined value for four pieces)
   dev.obsidiannetwork.client.V177IntegrityHud.draw(event,px,py-24,pasteWidth);
   String pasteLabel="PASTE";''')

add("powerarmor/V177ArmorIntegrity.java",r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.common.damagesource.DamageContainer;

/** Dedicated MK1-MK24 structural integrity. Never break or delete armor items.
 *  Vanilla unbreakable keeps old suits safe; damage is applied MANUALLY.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V177ArmorIntegrity {
 private V177ArmorIntegrity(){}
 public static boolean piece(ItemStack stack,int slot){
  return !stack.isEmpty()&&PowerArmorRuntime.tier(stack,slot)>0
     &&stack.getMaxDamage()>1;
 }
 private static int max(ItemStack s){return Math.max(1,s.getMaxDamage()-1);}
 public static boolean broken(ItemStack s){
  return s.getMaxDamage()>1&&s.getDamageValue()>=max(s);
 }
 public static boolean failed(ServerPlayer p){
  if(!PowerArmorRuntime.full(p))return false;
  for(int i=0;i<4;i++){
   ItemStack stack=p.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(piece(stack,i)&&broken(stack))return true;
  }
  return false;
 }
 public static int totalPercent(Player p){
  long total=0L,remaining=0L;
  for(int i=0;i<4;i++){
   ItemStack s=p.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(!piece(s,i))continue;
   int m=max(s);
   total+=m;
   remaining+=Math.max(0,m-Math.min(m,s.getDamageValue()));
  }
  return total==0L?0:(int)Math.round(100.0*remaining/(double)total);
 }
 @SubscribeEvent public static void noBrokenAttributes(ItemAttributeModifierEvent e){
  ItemStack stack=e.getItemStack();
  if(!(stack.getItem() instanceof PowerArmorItem)||!broken(stack))return;
  e.clearModifiers(); // zero armor, toughness, knockback, and all item modifiers
 }
 @SubscribeEvent public static void wear(LivingDamageEvent.Pre e){
  if(!(e.getEntity() instanceof ServerPlayer p)||!PowerArmorRuntime.full(p))return;
  if(failed(p)){
   // The armor must provide NO enchantment damage reduction when failed.
   // Preserve other mods' shields, potions, innate resistance and absorption.
   float enchant=e.getContainer().getReduction(DamageContainer.Reduction.ENCHANTMENTS);
   if(enchant>0&&Float.isFinite(enchant))
     e.setNewDamage(Math.max(0F,e.getNewDamage()+enchant));
   return;
  }
  float amount=e.getNewDamage();
  if(!(amount>0F)||!Float.isFinite(amount))return;
  // ~0.25% integrity per one point of actually received health damage.
  int wear=Math.max(1,Math.min(500000,(int)Math.ceil(amount*10000F)));
  for(int i=0;i<4;i++){
   ItemStack s=p.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(!piece(s,i))continue;
   s.setDamageValue(Math.min(max(s),s.getDamageValue()+wear));
  }
 }
 private static int repairOne(ItemStack stack,int availableFe){
  if(availableFe<=0||stack.isEmpty()||stack.getDamageValue()<=0)return 0;
  int restore=Math.min(stack.getDamageValue(),Math.min(25000,availableFe*100));
  if(restore<=0)return 0;
  int cost=(restore+99)/100; // exactly consumed and never negative
  stack.setDamageValue(Math.max(0,stack.getDamageValue()-restore));
  return cost;
 }
 public static void repairNearby(ServerLevel level,BlockPos pos,ArmorStationBlockEntity station){
  if(station.v177StoredFe()<=0)return;
  int budget=Math.min(1000,station.v177StoredFe());
  // The placed station's top is walkable. Check only current level players.
  for(Player entity:level.players()){
   if(!(entity instanceof ServerPlayer p)||!p.isAlive()||!PowerArmorRuntime.full(p))continue;
   if(Math.abs(p.getX()-(pos.getX()+.5D))>1D
       ||Math.abs(p.getZ()-(pos.getZ()+.5D))>1D
       ||p.getY()<pos.getY()||p.getY()>pos.getY()+2.5D)continue;
   int needed=0;
   for(int i=0;i<4;i++){
    ItemStack stack=p.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
    if(piece(stack,i))needed+=repairOne(stack,Math.max(0,budget-needed));
    if(needed>=budget)break;
   }
   if(needed>0)station.v177ConsumeFe(needed);
   break; // never repair two players from one single 5-tick budget
  }
 }
}
''')
add("client/V177IntegrityHud.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.V177ArmorIntegrity;
import net.minecraft.client.Minecraft;
import net.neoforged.neoforge.client.event.RenderGuiEvent;

/** Matches the 80-pixel FE/Paste bars; one combined four-piece value. */
public final class V177IntegrityHud {
 private V177IntegrityHud(){}
 public static void draw(RenderGuiEvent.Post event,int x,int y,int width){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null)return;
  int value=V177ArmorIntegrity.totalPercent(mc.player);
  int color=value<=25?0xffed6464:value<=50?0xfff2cb52:0xff76da96;
  var g=event.getGuiGraphics();
  g.pose().pushMatrix();
  g.pose().translate((float)x,(float)(y+4));
  g.pose().scale(.6f,.6f);
  g.text(mc.font,"ARMOR INTEGRITY",0,0,color);
  g.pose().popMatrix();
  String percent=value+"%";
  g.pose().pushMatrix();
  g.pose().translate(x+width-mc.font.width(percent)*.6f-1f,y+4f);
  g.pose().scale(.6f,.6f);
  g.text(mc.font,percent,0,0,color);
  g.pose().popMatrix();
  g.fill(x,y+10,x+width,y+12,0x88435855);
  g.fill(x,y+10,x+(int)Math.round(width*(value/100.0)),y+12,color);
 }
}
''')

print("V177_INTEGRITY_STATION_200K_FE_HUD_SOURCE_INSTALLED")
