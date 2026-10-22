#!/usr/bin/env python3
"""Clean v1.7 stage 2: separately crafted suit-card modules, protection and keybinds."""
import json, os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=Path(os.environ["V1_RESOURCE_ROOT"])
cards=["flight","night_vision","water_breathing","protection","fire_protection","blast_protection",
       "projectile_protection","feather_falling","respiration","aqua_affinity","thorns",
       "unbreaking","mending","depth_strider","frost_walker","soul_speed","swift_sneak"]
def replace(path,old,new):
 p=j/path
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1, "v1.7 stage2 changed anchor in "+path+": "+str(s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def put(path,d):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

# Each armor-compatible enchantment owns a real separate registry ID/card item.
register=""
tab=""
for name in cards:
 field="POWER_CARD_"+name.upper()
 register+=f'''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> {field} =
      ITEMS.registerItem("power_card_{name}",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"{name}"));
'''
 tab+=f'            output.accept((ItemLike){field}.get());\n'
replace("ObsidianNetwork.java",
 '''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE =''',
 register+'''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE =''')
replace("ObsidianNetwork.java",
 '            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());',
 '            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());\n'+tab.rstrip())

replace("powerarmor/UpgradeCardItem.java",
 ''' public UpgradeCardItem(Properties p){super(p.stacksTo(16));}''',
 ''' public final String upgradeId;
 public UpgradeCardItem(Properties p){this(p,"blank");}
 public UpgradeCardItem(Properties p,String id){super(p.stacksTo(16));this.upgradeId=id;}''')
p=j/"powerarmor/PowerArmorCards.java"
assert not p.exists()
lookup="\n".join(f'   case "{name}" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_{name.upper()}.get();' for name in cards)
p.write_text('''package dev.obsidiannetwork.powerarmor;
import net.minecraft.world.item.Item;
/** Registry-based original upgrade cards; never reuse deprecated v1.7 sources. */
public final class PowerArmorCards {
 public static Item item(String id){
  return switch(id){
'''+lookup+'''
   default -> null;
  };
 }
}
''',encoding="utf-8")

# The station installs exactly one specific card at a time in its suit
# chest core. Sneak + empty hand removes and returns the LAST installed card.
guard='''  // First test prototype: the four suit items go into the stand via sneak + right-click.
  if(p.isShiftKeyDown()){'''
addition='''  // CLEAN_V17_CARDS_V1: installation/deinstallation is station-only.
  ItemStack held=p.getMainHandItem();
  if(held.getItem() instanceof UpgradeCardItem card && !"blank".equals(card.upgradeId)){
   if(!station.complete())return InteractionResult.FAIL;
   ItemStack chest=station.get(1).copy();
   String installed=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(installed==null)installed="";
   String[] entries=installed.isEmpty()?new String[0]:installed.split(",");
   // No duplicate effect cards, except protection (8 levels maximum).
   int count=0;for(String id:entries)if(id.equals(card.upgradeId))count++;
   if(entries.length>=12||count>=(card.upgradeId.equals("protection")?8:1))return InteractionResult.FAIL;
   chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
       installed.isEmpty()?card.upgradeId:installed+","+card.upgradeId);
   station.put(1,chest);
   if(!p.isCreative())held.shrink(1);
   p.sendSystemMessage(Component.literal("Armor Station: installed "+card.upgradeId));
   return InteractionResult.SUCCESS;
  }
  if(p.isShiftKeyDown()&&held.isEmpty()&&station.complete()){
   ItemStack chest=station.get(1).copy();
   String installed=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(installed!=null&&!installed.isEmpty()){
    String[] entries=installed.split(",");
    int i=entries.length-1;
    // Skip persistent toggle metadata; only actual installed cards are removable.
    while(i>=0&&PowerArmorCards.item(entries[i])==null)i--;
    if(i>=0){
     String removed=entries[i];java.util.List<String> left=new java.util.ArrayList<>(java.util.Arrays.asList(entries));
     left.remove(i);
     chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
          String.join(",",left));
     station.put(1,chest);
     var cardItem=PowerArmorCards.item(removed);
     if(!p.getInventory().add(new ItemStack(cardItem)))
       net.minecraft.world.level.block.Block.popResource(level,pos,new ItemStack(cardItem));
     p.sendSystemMessage(Component.literal("Armor Station: removed "+removed));
     return InteractionResult.SUCCESS;
    }
   }
  }
  // Install actual armor pieces with sneak-right-click; no client-side item loss.
  if(p.isShiftKeyDown()){'''
replace("powerarmor/ArmorStationBlock.java",guard,addition)

# Explicit safety: do not install a duplicate helmet into a legs slot etc.
replace("powerarmor/ArmorStationBlock.java",
 '''    if(station.get(i).isEmpty()){
     if(!p.isCreative())station.put(i,stack.split(1));''',
 '''    boolean matching=switch(i){
     case 0 -> stack.is(ObsidianNetwork.POWER_ARMOR_HELMET.get());
     case 1 -> stack.is(ObsidianNetwork.POWER_ARMOR_CHESTPLATE.get());
     case 2 -> stack.is(ObsidianNetwork.POWER_ARMOR_LEGGINGS.get());
     case 3 -> stack.is(ObsidianNetwork.POWER_ARMOR_BOOTS.get());
     default -> false; };
    if(matching&&station.get(i).isEmpty()){
     if(!p.isCreative())station.put(i,stack.split(1));''')
replace("powerarmor/ArmorStationBlockEntity.java",
 '''  for(ItemStack stack:suit)if(!(stack.getItem() instanceof PowerArmorItem))return false;''',
 '''  if(!suit[0].is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_HELMET.get()))return false;
  if(!suit[1].is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_CHESTPLATE.get()))return false;
  if(!suit[2].is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_LEGGINGS.get()))return false;
  if(!suit[3].is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_BOOTS.get()))return false;''')

runtime=j/"powerarmor/PowerArmorRuntime.java"
s=runtime.read_text(encoding="utf-8")
assert s.count("public final class PowerArmorRuntime {")==1
s=s.replace("public final class PowerArmorRuntime {",'''public final class PowerArmorRuntime {
 private static final java.util.Set<java.util.UUID> GRANTED_FLIGHT=
     java.util.concurrent.ConcurrentHashMap.newKeySet();
''',1)
old='''  if(canFly&&!p.getAbilities().mayfly){p.getAbilities().mayfly=true;p.onUpdateAbilities();}
  if(!canFly&&!natural&&p.getAbilities().mayfly){
   p.getAbilities().flying=false;p.getAbilities().mayfly=false;p.onUpdateAbilities();
  }
  if(powered(p)){
   for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
  }'''
new='''  if(canFly&&!p.getAbilities().mayfly){
   GRANTED_FLIGHT.add(p.getUUID());
   p.getAbilities().mayfly=true;p.onUpdateAbilities();
  }
  if(!canFly&&!natural&&GRANTED_FLIGHT.remove(p.getUUID())){
   p.getAbilities().flying=false;p.getAbilities().mayfly=false;p.onUpdateAbilities();
  }
  if(powered(p)){
   for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
   if(hasCard(p,"water_breathing"))
    p.addEffect(new net.minecraft.world.effect.MobEffectInstance(
      net.minecraft.world.effect.MobEffects.WATER_BREATHING,125,0,true,false,false));
   if(hasCard(p,"night_vision")&&hasCard(p,"nightvision_on"))
    p.addEffect(new net.minecraft.world.effect.MobEffectInstance(
      net.minecraft.world.effect.MobEffects.NIGHT_VISION,225,0,true,false,false));
  }'''
assert s.count(old)==1
s=s.replace(old,new,1)
idx=s.rfind("}")
extra=''' @SubscribeEvent public static void onDamage(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre event){
  if(!(event.getEntity() instanceof ServerPlayer player)||!powered(player))return;
  float amount=event.getNewDamage();
  if(!Float.isFinite(amount)||amount<=0)return;
  int protection=0,fire=0,blast=0,projectile=0,feather=0;
  for(EquipmentSlot slot:SLOTS){
   String upgrades=player.getItemBySlot(slot).get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(upgrades==null)continue;
   for(String card:upgrades.split(",")){
    if(card.equals("protection"))protection++;
    else if(card.equals("fire_protection"))fire++;
    else if(card.equals("blast_protection"))blast++;
    else if(card.equals("projectile_protection"))projectile++;
    else if(card.equals("feather_falling"))feather++;
   }
  }
  // Stronger than Netherite/Protection at higher power-card tiers,
  // but never full invulnerability. Damage-type cards are additive, capped.
  float reduction=0.20f+Math.min(8,protection)*0.08f;
  var source=event.getSource();
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_FIRE))reduction+=fire*0.04f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_EXPLOSION))reduction+=blast*0.04f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_PROJECTILE))reduction+=projectile*0.04f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_FALL))reduction+=feather*0.04f;
  reduction=Math.min(0.94f,reduction);
  long cost=Math.max(80,(long)(amount*80.0f));
  for(EquipmentSlot slot:SLOTS)if(EnergyTool.energy(player.getItemBySlot(slot))<cost)return;
  for(EquipmentSlot slot:SLOTS)EnergyTool.consume(player.getItemBySlot(slot),cost);
  event.setNewDamage(amount*(1-reduction));
 }
'''
s=s[:idx]+extra+s[idx:]
runtime.write_text(s,encoding="utf-8")
# User-rebindable exit hotkey, and Night Vision separately toggleable.
key=j/"client/PowerArmorHotkeys.java"
assert not key.exists()
key.write_text('''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import net.minecraft.client.KeyMapping;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.glfw.GLFW;
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorHotkeys {
 public static final KeyMapping EXIT=new KeyMapping("key.obsidiannetwork.power_armor_exit",
     InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_J,KeyMapping.Category.MISC);
 public static final KeyMapping NIGHT=new KeyMapping("key.obsidiannetwork.power_armor_nightvision",
     InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_V,KeyMapping.Category.MISC);
 @SubscribeEvent public static void onTick(ClientTickEvent.Post event){
  var mc=Minecraft.getInstance();
  if(mc.player==null||mc.player.connection==null)return;
  while(EXIT.consumeClick())mc.player.connection.sendCommand("powerarmor exit");
  while(NIGHT.consumeClick())mc.player.connection.sendCommand("powerarmor nightvision");
 }
}
''',encoding="utf-8")
client=j/"client/ClientModEvents.java"
s=client.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "PowerArmorHotkeys.EXIT" not in s
client.write_text(s[:-1]+'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxRegisterPowerArmorKeys(net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent event){
  event.register(PowerArmorHotkeys.EXIT);
  event.register(PowerArmorHotkeys.NIGHT);
 }
}
''',encoding="utf-8")
replace("powerarmor/PowerArmorCommands.java",
 '''   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException()))));''',
 '''   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException())))
   .then(Commands.literal("nightvision").executes(c->night(c.getSource().getPlayerOrException()))));''')
p=j/"powerarmor/PowerArmorCommands.java"
s=p.read_text(encoding="utf-8").rstrip()
assert s.endswith("}")
s=s[:-1]+''' public static int night(ServerPlayer p){
  if(!PowerArmorRuntime.powered(p)||!PowerArmorRuntime.hasCard(p,"night_vision"))return 0;
  ItemStack chest=p.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST);
  String old=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(old==null)return 0;
  java.util.List<String> cards=new java.util.ArrayList<>(java.util.Arrays.asList(old.split(",")));
  if(cards.contains("nightvision_on"))cards.remove("nightvision_on");
  else cards.add("nightvision_on");
  chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",cards));
  return Command.SINGLE_SUCCESS;
 }
}
'''
p.write_text(s,encoding="utf-8")

for card in cards:
 # Item icon + in-game localized card name.
 put(r/f"assets/obsidiannetwork/models/item/power_card_{card}.json",
     {"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/nether_star"}})
 put(r/f"assets/obsidiannetwork/items/power_card_{card}.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_"+card}})
 # Each special module uses the blank base upgrade board.
 recipe={
  "type":"minecraft:crafting_shapeless",
  "ingredients":["obsidiannetwork:power_armor_upgrade","minecraft:lapis_lazuli"],
  "result":{"id":"obsidiannetwork:power_card_"+card,"count":1}
 }
 put(r/f"data/obsidiannetwork/recipe/power_card_{card}.json",recipe)
for lang in ("en_us","de_de"):
 path=r/f"assets/obsidiannetwork/lang/{lang}.json"
 obj=json.loads(path.read_text(encoding="utf-8"))
 for card in cards:
  obj["item.obsidiannetwork.power_card_"+card]=card.replace("_"," ").title()+" Upgrade Card"
 obj["key.obsidiannetwork.power_armor_exit"]="Exit Power Armor" if lang=="en_us" else "Power-Rüstung verlassen"
 obj["key.obsidiannetwork.power_armor_nightvision"]="Toggle Armor Night Vision" if lang=="en_us" else "Rüstungs-Nachtsicht umschalten"
 put(path,obj)
print("CLEAN_V17_UPGRADE_CARDS_V1 PASS modules=",len(cards))
