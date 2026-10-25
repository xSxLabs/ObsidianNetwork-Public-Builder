#!/usr/bin/env python3
"""v1.7.3 Build201: make A/B portal travel an installed Power Armor upgrade.

Follows the existing Armor Station upgrade-card system. Hotkey packets are
authenticated on the server, including B activation AND actual entry, and A
placement requires an equipped powered suit with the card installed.
"""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def once(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def emit(rel,body):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),p
 p.write_text(body,encoding="utf-8")
def jwrite(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# A normal upgrade-card installed and uninstalled by the EXISTING Armor Station.
once("ObsidianNetwork.java",
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_NETWORK_VISION =',
 '''   // V173_PORTAL_ARMOR_CARD: installed through the existing Armor Station.
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_PORTAL =
      ITEMS.registerItem("power_card_portal",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"portal"));
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_NETWORK_VISION =''')
once("ObsidianNetwork.java",
 '            output.accept((ItemLike)POWER_CARD_NETWORK_VISION.get());',
 '''            output.accept((ItemLike)POWER_CARD_NETWORK_VISION.get());
            output.accept((ItemLike)POWER_CARD_PORTAL.get());''')
once("powerarmor/PowerArmorCards.java",
 '   case "network_vision" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_NETWORK_VISION.get();',
 '''   case "network_vision" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_NETWORK_VISION.get();
   case "portal" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_PORTAL.get();''')
jwrite(R/"models/item/power_card_portal.json",{
 "parent":"minecraft:item/generated",
 "textures":{"layer0":"obsidiannetwork:item/power_armor_upgrade"}})
jwrite(R/"items/power_card_portal.json",{
 "model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_portal"}})
jwrite(D/"recipe/power_card_portal.json",{
 "type":"minecraft:crafting_shaped",
 "pattern":["ENE","UCU","EAE"],
 "key":{"E":"minecraft:ender_eye","N":"minecraft:nether_star",
        "U":"minecraft:netherite_ingot","C":"obsidiannetwork:power_armor_upgrade",
        "A":"obsidiannetwork:advanced_energy_cell"},
 "result":{"id":"obsidiannetwork:power_card_portal","count":1}})
for lang in ("de_de","en_us"):
 p=R/"lang"/(lang+".json")
 data=json.loads(p.read_text(encoding="utf-8"))
 data["item.obsidiannetwork.power_card_portal"]=(
  "Portal-Upgrade-Karte (Power Armor)" if lang=="de_de" else "Power Armor Portal Upgrade Card")
 data["key.obsidiannetwork.portal_select_a"]=(
  "Power Armor: Portal A auswählen" if lang=="de_de" else "Power Armor: Select Portal A")
 data["key.obsidiannetwork.portal_spawn_b"]=(
  "Power Armor: Portal B erzeugen" if lang=="de_de" else "Power Armor: Summon Portal B")
 jwrite(p,data)

# BlockItem is a real placeable object, but is not usable without the armor
# card. Keeping A as a world block is intentional: physical A survives armor
# removal and can only disappear when mined/broken.
once("ObsidianNetwork.java",
 'ITEMS.registerSimpleBlockItem("network_portal_a",NETWORK_PORTAL_A);',
 'ITEMS.registerItem("network_portal_a",p -> new dev.obsidiannetwork.portal.PortalAItem(NETWORK_PORTAL_A.get(),p));')
emit("portal/PortalAItem.java",r'''package dev.obsidiannetwork.portal;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.Block;

/** V173_PORTAL_A_ARMOR_PLACEMENT: permanent A must be placed while upgraded. */
public final class PortalAItem extends BlockItem {
 public PortalAItem(Block block,Properties p){super(block,p);}
 @Override public InteractionResult useOn(UseOnContext ctx){
  if(!ctx.getLevel().isClientSide()){
   if(!(ctx.getPlayer() instanceof ServerPlayer player) ||
        !PortalActionPayload.hasUpgrade(player)){
    if(ctx.getPlayer()!=null)ctx.getPlayer().sendSystemMessage(
      Component.literal("Requires a powered Power Armor with Portal Upgrade Card."));
    return InteractionResult.FAIL;
   }
  }
  return super.useOn(ctx);
 }
}
''')

# Client does not trust itself: server ALWAYS validates the armor and the card,
# even if another client synthesizes its own packets.
once("portal/PortalActionPayload.java",
 ''' private static void tell(ServerPlayer player,String text){player.sendSystemMessage(Component.literal(text));}
 public static void cycle(ServerPlayer player){''',
 ''' private static void tell(ServerPlayer player,String text){player.sendSystemMessage(Component.literal(text));}
 /** V173_PORTAL_SERVER_ARMOR_GATE: authoritative even for forged hotkey packets. */
 public static boolean hasUpgrade(ServerPlayer player){
  return !player.isSpectator()
     && dev.obsidiannetwork.powerarmor.PowerArmorRuntime.powered(player)
     && dev.obsidiannetwork.powerarmor.PowerArmorRuntime.hasCard(player,"portal");
 }
 public static void cycle(ServerPlayer player){
  if(!hasUpgrade(player)){
   tell(player,"Equip a powered Power Armor and install its Portal Upgrade Card at the Armor Station.");
   return;
  }''')
once("portal/PortalActionPayload.java",
 ''' public static void spawn(ServerPlayer player){
  if(player.isSpectator())return;''',
 ''' public static void spawn(ServerPlayer player){
  if(!hasUpgrade(player)){
   tell(player,"Portal B requires powered Power Armor with Portal Upgrade Card.");
   return;
  }
  if(dev.obsidiannetwork.core.EnergyTool.energy(
       player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST))<10000L){
   tell(player,"Portal B: armor chest cell needs 10,000 FE for travel.");
   return;
  }''')

# One-time return trip FE debit, only AFTER the server reports a successful
# teleport. Removing the armor between opening B and stepping into it disables B.
once("portal/PortalGateBlockEntity.java",
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+1.85)continue;
   try{''',
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+1.85)continue;
   // V173_PORTAL_ENTRY_ARMOR_GATE: no teleport after suit removal / power loss.
   if(!PortalActionPayload.hasUpgrade(player))continue;
   var armor=player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST);
   if(dev.obsidiannetwork.core.EnergyTool.energy(armor)<10000L)continue;
   try{''')
once("portal/PortalGateBlockEntity.java",
 '''         Set.of(),player.getYRot(),player.getXRot(),true)){
     level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());''',
 '''         Set.of(),player.getYRot(),player.getXRot(),true)){
     // Server-authoritative payment happens once, after a successful transfer.
     dev.obsidiannetwork.core.EnergyTool.consume(armor,10000L);
     level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());''')
# Defense-in-depth for places/commands that bypass PortalAItem.useOn:
# invalid / fake A blocks will never be indexed as owned destinations.
once("portal/PortalGateBlock.java",
 '''  if(!temporary && l instanceof ServerLevel sl && e instanceof Player player &&
     l.getBlockEntity(p) instanceof PortalGateBlockEntity be){''',
 '''   if(!temporary && l instanceof ServerLevel sl && e instanceof net.minecraft.server.level.ServerPlayer player
      && PortalActionPayload.hasUpgrade(player)
      && l.getBlockEntity(p) instanceof PortalGateBlockEntity be){''')

print("V173_PORTAL_POWER_ARMOR_UPGRADE_BUILD201_PASS")
