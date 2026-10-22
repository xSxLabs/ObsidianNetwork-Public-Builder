#!/usr/bin/env python3
"""Build 59: fix duplicate deploy + permit V exit from a manually worn MK1/MK2.

Source-only overlay, always AFTER the GeckoLib conversion. Server owns each
four-piece inventory transfer. Old persistent backup remains untouched on errors.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def replace_one(rel,old,new):
 p=root/rel
 content=p.read_text(encoding="utf-8")
 assert content.count(old)==1, "BUILD59 anchor drift "+rel+" "+str(content.count(old))
 p.write_text(content.replace(old,new,1),encoding="utf-8")

file=root/"powerarmor/PowerArmorSuitWorld.java"
code=file.read_text(encoding="utf-8")
start=code.index(" /** Initial setup without any station;")
end=code.index(" /** Exit never creates or places an Armor Station. */",start)
assert "public static int deploy(ServerPlayer player)" in code[start:end]
code=code[:start]+code[end:]
file.write_text(code,encoding="utf-8")
replace_one("powerarmor/PowerArmorCommands.java",
 '''   .then(Commands.literal("deploy").executes(c->PowerArmorSuitWorld.deploy(c.getSource().getPlayerOrException())))
''','')

old_exit=''' public static int exit(ServerPlayer player){
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  var backup=saved.get(player);
  if(backup==null||!PowerArmorRuntime.full(player))return 0;
  List<ItemStack> suit=new ArrayList<>();
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)suit.add(player.getItemBySlot(slot).copy());
  if(!spawn(player,suit))return 0;
  for(int i=0;i<4;i++)player.setItemSlot(
      PowerArmorRuntime.SLOTS[i],backup.previous().get(i).copy());
  saved.finish(player);
  player.sendSystemMessage(Component.literal(
   "Power Armor exited. Original equipment restored; suit stands beside you."));
  return 1;
 }'''
new_exit=''' public static int exit(ServerPlayer player){
  // Manually equip a matching MK1/MK2 suit, then press the existing V hotkey.
  if(!PowerArmorRuntime.full(player)){
   player.sendSystemMessage(Component.literal(
    "Power Armor: put on all four matching MK1 or MK2 pieces first."));
   return 0;
  }
  if(ACTIVE.containsKey(player.getUUID())){
   player.sendSystemMessage(Component.literal("Power Armor: animation already in progress."));
   return 0;
  }
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  var backup=saved.get(player);
  if(backup!=null&&backup.previous().size()!=4){
   player.sendSystemMessage(Component.literal("Power Armor: invalid loadout backup; no item moved."));
   return 0;
  }
  List<ItemStack> suit=new ArrayList<>(4);
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)suit.add(player.getItemBySlot(slot).copy());
  // Validate and spawn first, clear the original slots only on success.
  if(!spawn(player,suit))return 0;
  for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],
   backup==null?ItemStack.EMPTY:backup.previous().get(i).copy());
  if(backup!=null)saved.finish(player);
  player.sendSystemMessage(Component.literal(
   "Power Armor disengaged. Right-click the standing suit to enter again."));
  return 1;
 }'''
replace_one("powerarmor/PowerArmorSuitWorld.java",old_exit,new_exit)
replace_one("powerarmor/PowerArmorSuitWorld.java",
 '''  if(!full(stand)){
   player.sendSystemMessage(Component.literal("Power Armor: suit is incomplete; no items moved."));
   return;
  }
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());''',
 '''  if(!full(stand)){
   player.sendSystemMessage(Component.literal("Power Armor: suit is incomplete; no items moved."));
   return;
  }
  // Never back up a second worn power suit as the player's previous armor.
  if(PowerArmorRuntime.full(player)){
   player.sendSystemMessage(Component.literal(
    "Power Armor: already wearing a suit. Exit it before entering another."));
   return;
  }
  if(ACTIVE.containsKey(player.getUUID()))return;
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());''')
replace_one("powerarmor/ArmorStationBlock.java",
 '''      "Armor Station is for upgrades. Deploy a full suit with /powerarmor deploy."''',
 '''      "Armor Station is for upgrades. Equip MK1/MK2, then use the Exit hotkey."''')

# Optional, server-authoritative diagnostic. Apotheosis 26.1 ReforgingTable
# accepts exactly the loot categories returned by LootCategory.forItem.
# There is NO hard Apotheosis class linkage when it is not installed.
cmd=root/"powerarmor/PowerArmorCommands.java"
s=cmd.read_text(encoding="utf-8")
marker='''   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException())))'''
assert s.count(marker)==1
s=s.replace(marker,
 '''   .then(Commands.literal("compat").executes(c->apotheosis(c.getSource().getPlayerOrException())))
'''+marker,1)
method=r'''
 /** Reports the exact category that the Apotheosis Reforging Table observes. */
 public static int apotheosis(ServerPlayer p){
  if(!net.neoforged.fml.ModList.get().isLoaded("apotheosis")){
   p.sendSystemMessage(Component.literal("Apotheosis is not loaded on this server."));
   return 0;
  }
  try{
   var categoryType=Class.forName("dev.shadowsoffire.apotheosis.loot.LootCategory");
   var classify=categoryType.getMethod("forItem",ItemStack.class);
   net.minecraft.world.item.Item[] items={
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_HELMET.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_CHESTPLATE.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_LEGGINGS.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_BOOTS.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_HELMET.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_CHESTPLATE.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_LEGGINGS.get(),
    dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_MK2_BOOTS.get()
   };
   int failures=0;
   for(int i=0;i<items.length;i++){
    String slot=new String[]{"helmet","chestplate","leggings","boots"}[i%4];
    String observed=String.valueOf(classify.invoke(null,new ItemStack(items[i])));
    boolean supported=observed.endsWith("apotheosis:"+slot+"]");
    if(!supported)failures++;
    p.sendSystemMessage(Component.literal(
     (i<4?"MK1 ":"MK2 ")+slot+" -> "+observed+
     (supported?" [OK]":" [WRONG CATEGORY]")));
   }
   if(failures==0)p.sendSystemMessage(Component.literal(
    "8/8 categories recognized. Check Reforging Table rarity material/recipe if output is missing."));
   return failures==0?1:0;
  }catch(ReflectiveOperationException|LinkageError ex){
   p.sendSystemMessage(Component.literal(
    "Apotheosis category API unavailable: "+ex.getClass().getSimpleName()));
   return 0;
  }
 }
'''
idx=s.rfind("}")
assert idx>=0
cmd.write_text(s[:idx]+method+s[idx:],encoding="utf-8")
world=(root/"powerarmor/PowerArmorSuitWorld.java").read_text(encoding="utf-8")
command=cmd.read_text(encoding="utf-8")
assert "public static int deploy(" not in world
assert 'Commands.literal("deploy")' not in command
assert "backup==null?ItemStack.EMPTY:backup.previous().get(i).copy()" in world
assert "if(!spawn(player,suit))return 0;" in world
assert "if(PowerArmorRuntime.full(player))" in world
print("BUILD59_SAFE_EXIT_AND_ENTER PASS: deploy removed, first V exit, no second suit backup, 8 Apotheosis probes")
