#!/usr/bin/env python3
"""Clean v1.7 stage 2: separately crafted suit-card modules, protection and keybinds."""
import json, os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=Path(os.environ["V1_RESOURCE_ROOT"])
cards=["flight","night_vision","water_breathing","protection","fire_protection","blast_protection",
       "projectile_protection","feather_falling","respiration","aqua_affinity","thorns",
       "unbreaking","mending","depth_strider","frost_walker","soul_speed","swift_sneak","strength","resistance","speed","haste","regeneration","fire_resistance","jump_boost","network_elytra"]
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
guard='''  // Sneak + right click mounts a component into its matching suit slot.
  // Empty hand retrieves one installed item without overwriting an occupied inventory.
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
   if(entries.length>=15||count>=(card.upgradeId.equals("protection")?4:1))return InteractionResult.FAIL;
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
     String removed=entries[i];
     var cardItem=PowerArmorCards.item(removed);
     // Keep installed cards intact when the player has no free inventory slot.
     if(!p.getInventory().add(new ItemStack(cardItem))){
      p.sendSystemMessage(Component.literal("Armor Station: inventory full; upgrade retained."));
      return InteractionResult.FAIL;
     }
     java.util.List<String> left=new java.util.ArrayList<>(java.util.Arrays.asList(entries));
     left.remove(i);
     chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
          String.join(",",left));
     station.put(1,chest);
     p.sendSystemMessage(Component.literal("Armor Station: removed "+removed));
     return InteractionResult.SUCCESS;
    }
   }
  }
  // Sneak + right click mounts a component into its matching suit slot.
  // Empty hand retrieves one installed item without overwriting an occupied inventory.
  if(p.isShiftKeyDown()){'''
replace("powerarmor/ArmorStationBlock.java",guard,addition)

# Stage1 now enforces exact slot identities and safe item retrieval.
runtime=j/"powerarmor/PowerArmorRuntime.java"
s=runtime.read_text(encoding="utf-8")
assert s.count("public final class PowerArmorRuntime {")==1
# Stage1 owns its own flight grants, preserving flight from other mods.
assert "OWNED_FLIGHT" in s, "Stage1 flight ownership guard missing"

old='''  if(powered(p)){
   for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
  }'''
new='''  if(powered(p)){
   for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
   // Build 72: apply enhancement effects only while the powered suit is worn.
   String installedCards="";
   for(EquipmentSlot armorSlot:SLOTS){
    String value=p.getItemBySlot(armorSlot).get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
    if(value!=null)installedCards+=","+value;
   }
   for(String effectId:new String[]{"strength","resistance","speed","haste","regeneration","fire_resistance","jump_boost"}){
    int count=0;
    for(String entry:installedCards.split(","))if(entry.equals(effectId))count++;
    if(count==0)continue;
    int max=switch(effectId){case "strength","speed","haste"->3;case "resistance","regeneration","jump_boost"->2;default->1;};
    var effect=switch(effectId){
     case "strength"->net.minecraft.world.effect.MobEffects.STRENGTH;
     case "resistance"->net.minecraft.world.effect.MobEffects.RESISTANCE;
     case "speed"->net.minecraft.world.effect.MobEffects.SPEED;
     case "haste"->net.minecraft.world.effect.MobEffects.HASTE;
     case "regeneration"->net.minecraft.world.effect.MobEffects.REGENERATION;
     case "fire_resistance"->net.minecraft.world.effect.MobEffects.FIRE_RESISTANCE;
     default->net.minecraft.world.effect.MobEffects.JUMP_BOOST;
    };
    p.addEffect(new net.minecraft.world.effect.MobEffectInstance(effect,125,Math.min(max,count)-1,true,false,false));
    for(EquipmentSlot armorSlot:SLOTS)EnergyTool.consume(p.getItemBySlot(armorSlot),25L*count);
   }
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
  float reduction=Math.min(0.995f,Math.min(5,protection)*0.195f);
  var source=event.getSource();
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_FIRE))reduction+=Math.min(5,fire)*0.02f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_EXPLOSION))reduction+=Math.min(5,blast)*0.02f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_PROJECTILE))reduction+=Math.min(5,projectile)*0.02f;
  if(source.is(net.minecraft.tags.DamageTypeTags.IS_FALL))reduction+=Math.min(5,feather)*0.02f;
  reduction=Math.min(0.995f,reduction);
  long cost=Math.max(400,(long)(amount*1200.0f*(1.0f+protection*0.5f)));
  for(EquipmentSlot slot:SLOTS)if(EnergyTool.energy(player.getItemBySlot(slot))<cost)return;
  for(EquipmentSlot slot:SLOTS)EnergyTool.consume(player.getItemBySlot(slot),cost);
  event.setNewDamage(amount*(1-reduction));
 }
'''
s=s[:idx]+extra+s[idx:]
runtime.write_text(s,encoding="utf-8")
# Extend the Stage-1 server-validated exit payload, not a second exit key.
# Register both keys in the EXISTING mod-bus client registry, preventing duplicates.
exitKey=j/"powerarmor/PowerArmorExitKeyClient.java"
text=exitKey.read_text(encoding="utf-8")
old=''' private static final KeyMapping EXIT=new KeyMapping(
   "key.obsidiannetwork.power_armor_exit",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_V,KeyMapping.Category.MISC);'''
new=''' public static final KeyMapping EXIT=new KeyMapping(
   "key.obsidiannetwork.power_armor_exit",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_V,KeyMapping.Category.create(net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("obsidiannetwork","xsxlabs")));
 public static final KeyMapping NIGHT=new KeyMapping(
   "key.obsidiannetwork.power_armor_nightvision",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_J,KeyMapping.Category.create(net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("obsidiannetwork","xsxlabs")));'''
assert text.count(old)==1,"Stage1 exit key changed"
text=text.replace(old,new,1)
old=''' @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){
  e.register(EXIT);
 }'''
assert text.count(old)==1
text=text.replace(old,"",1)
old='''   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(new PowerArmorExitPayload());
  }
 }'''
new='''   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(new PowerArmorExitPayload());
  }
  while(NIGHT.consumeClick()){
   Minecraft mc=Minecraft.getInstance();
   if(mc.player!=null && mc.screen==null && mc.player.connection!=null)
    mc.player.connection.sendCommand("powerarmor nightvision");
  }
 }'''
assert text.count(old)==1
exitKey.write_text(text.replace(old,new,1),encoding="utf-8")
client=j/"client/ClientModEvents.java"
s=client.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "PowerArmorExitKeyClient.EXIT" not in s
client.write_text(s[:-1]+'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxRegisterPowerArmorKeys(net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent event){
  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.EXIT);
  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.NIGHT);
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
  if(cards.contains("nightvision_on")){ cards.remove("nightvision_on"); p.removeEffect(net.minecraft.world.effect.MobEffects.NIGHT_VISION); }
  else cards.add("nightvision_on");
  chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",cards));
  return Command.SINGLE_SUCCESS;
 }
}
'''
p.write_text(s,encoding="utf-8")

ingredients={
 "flight":"minecraft:feather",
 "night_vision":"minecraft:golden_carrot",
 "water_breathing":"minecraft:pufferfish",
 "protection":"minecraft:netherite_scrap",
 "fire_protection":"minecraft:magma_cream",
 "blast_protection":"minecraft:obsidian",
 "projectile_protection":"minecraft:shield",
 "feather_falling":"minecraft:phantom_membrane",
 "respiration":"minecraft:nautilus_shell",
 "aqua_affinity":"minecraft:prismarine_crystals",
 "thorns":"minecraft:cactus",
 "unbreaking":"minecraft:anvil",
 "mending":"minecraft:experience_bottle",
 "depth_strider":"minecraft:heart_of_the_sea",
 "frost_walker":"minecraft:blue_ice",
 "soul_speed":"minecraft:soul_soil",
 "swift_sneak":"minecraft:echo_shard",
 "strength":"minecraft:blaze_rod",
 "resistance":"minecraft:nether_star",
 "speed":"minecraft:sugar",
 "haste":"minecraft:beacon",
 "regeneration":"minecraft:totem_of_undying",
 "fire_resistance":"minecraft:ancient_debris",
 "jump_boost":"minecraft:rabbit_foot",
 "network_elytra":"obsidiannetwork:network_elytra"
}
assert set(ingredients)==set(cards) and len(set(ingredients.values()))==len(cards), "Distinct recipes required"
for card in cards:
 # Item icon + in-game localized card name.
 put(r/f"assets/obsidiannetwork/models/item/power_card_{card}.json",
     {"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/nether_star"}})
 put(r/f"assets/obsidiannetwork/items/power_card_{card}.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_"+card}})
 # Each special module uses the blank base upgrade board.
 recipe={
  "type":"minecraft:crafting_shapeless",
  "ingredients":["obsidiannetwork:power_armor_upgrade",ingredients[card]] + (["minecraft:netherite_ingot","minecraft:diamond_block"] if card in {"strength","resistance","speed","haste","regeneration","fire_resistance","jump_boost","network_elytra"} else []),
  "result":{"id":"obsidiannetwork:power_card_"+card,"count":1}
 }
 if card not in {"mending","unbreaking"}:
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
