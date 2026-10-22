#!/usr/bin/env python3
"""Clean v1.7 / Stage 1: real FE suit, armor station, preserved loadout and recover."""
import os, json
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=Path(os.environ["V1_RESOURCE_ROOT"])
mod=j/"ObsidianNetwork.java"
s=mod.read_text(encoding="utf-8")
assert 'XSXLABS_POWER_ARMOR_V17' not in s
start='   public static final DeferredItem<dev.obsidiannetwork.item.NetworkElytraItem> NETWORK_ELYTRA = ITEMS.registerItem('
assert s.count(start)==1, "Elytra registration changed"
# Insert BEFORE Elytra so the original implementation/identifiers survive.
registration=r"""
   // XSXLABS_POWER_ARMOR_V17: distinct FE suit (original v1.6 Elytra untouched).
   public static final DeferredBlock<dev.obsidiannetwork.powerarmor.ArmorStationBlock> ARMOR_STATION =
      BLOCKS.registerBlock("armor_station", dev.obsidiannetwork.powerarmor.ArmorStationBlock::new,
         p -> p.mapColor(MapColor.METAL).strength(4.0F,3600000.0F)
          .pushReaction(net.minecraft.world.level.material.PushReaction.BLOCK).noOcclusion());
   public static final DeferredItem<BlockItem> ARMOR_STATION_ITEM=ITEMS.registerSimpleBlockItem("armor_station",ARMOR_STATION);
"""
for name,slot in [("helmet","HEAD"),("chestplate","CHEST"),("leggings","LEGS"),("boots","FEET")]:
 registration+=f'''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.PowerArmorItem> POWER_ARMOR_{name.upper()} =
      ITEMS.registerItem("power_armor_{name}", p -> new dev.obsidiannetwork.powerarmor.PowerArmorItem(
        p.stacksTo(1).durability(4000000)
          .component(net.minecraft.core.component.DataComponents.UNBREAKABLE, net.minecraft.util.Unit.INSTANCE)
          .component(net.minecraft.core.component.DataComponents.EQUIPPABLE,
            net.minecraft.world.item.equipment.Equippable.builder(net.minecraft.world.entity.EquipmentSlot.{slot})
              .setAsset(net.minecraft.resources.ResourceKey.create(
                net.minecraft.world.item.equipment.EquipmentAssets.ROOT_ID,
                net.minecraft.resources.Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor")))
              .build())
          .component(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get(),0L)
      ));
'''
registration+='''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE =
      ITEMS.registerItem("power_armor_upgrade",dev.obsidiannetwork.powerarmor.UpgradeCardItem::new);
'''
s=s.replace(start,registration+"\n"+start,1)
tab="output.accept((ItemLike)NETWORK_ELYTRA.get());"
assert s.count(tab)==1
s=s.replace(tab,tab+'''\\n            output.accept((ItemLike)ARMOR_STATION_ITEM.get());
            output.accept((ItemLike)POWER_ARMOR_HELMET.get());
            output.accept((ItemLike)POWER_ARMOR_CHESTPLATE.get());
            output.accept((ItemLike)POWER_ARMOR_LEGGINGS.get());
            output.accept((ItemLike)POWER_ARMOR_BOOTS.get());
            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());'''.replace("\\n","\n"),1)
bus="net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.item.NetworkElytraItem.class);"
assert s.count(bus)==1
s=s.replace(bus,bus+'''
      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.class);
      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(dev.obsidiannetwork.powerarmor.PowerArmorCommands::register);''',1)
mod.write_text(s,encoding="utf-8")

p=j/"registry/ModDataComponents.java";s=p.read_text(encoding="utf-8")
assert "POWER_ARMOR_UPGRADES" not in s
s=s.rstrip()
assert s.endswith("}")
s=s[:-1]+'''
   // Clean v1.7: validated comma-separated installed suit-card IDs.
   public static final java.util.function.Supplier<net.minecraft.core.component.DataComponentType<String>> POWER_ARMOR_UPGRADES =
      COMPONENTS.registerComponentType("power_armor_upgrades",
       builder -> builder.persistent(com.mojang.serialization.Codec.STRING));
}
'''
p.write_text(s,encoding="utf-8")

p=j/"registry/ModBlockEntities.java";s=p.read_text(encoding="utf-8")
anchor='   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity>> NETWORK_TRANSMITTER = TYPES.register('
assert s.count(anchor)==1
s=s.replace(anchor,'''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity>> ARMOR_STATION =
     TYPES.register("armor_station", () -> new BlockEntityType(
       dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity::new,
       new Block[]{(Block)ObsidianNetwork.ARMOR_STATION.get()}));
'''+anchor,1)
p.write_text(s,encoding="utf-8")

java=j/"powerarmor"
java.mkdir(exist_ok=True)
def write(name,content):
 p=java/name
 assert not p.exists(),f"refusing to overwrite {p}"
 p.write_text(content,encoding="utf-8")

write("PowerArmorItem.java",r'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.world.item.Item;
public final class PowerArmorItem extends Item {
 public PowerArmorItem(Properties p){super(p);}
}
''')
write("UpgradeCardItem.java",r'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.world.item.Item;
public final class UpgradeCardItem extends Item {
 public UpgradeCardItem(Properties p){super(p.stacksTo(16));}
}
''')
write("PowerArmorRuntime.java",r'''package dev.obsidiannetwork.powerarmor;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** Single server tick, one four-slot lookup. FE-empty armor does not grant flight. */
public final class PowerArmorRuntime {
 public static final EquipmentSlot[] SLOTS={EquipmentSlot.HEAD,EquipmentSlot.CHEST,
  EquipmentSlot.LEGS,EquipmentSlot.FEET};
 // The suit must never revoke flight granted by another installed mod.
 private static final java.util.Set<java.util.UUID> OWNED_FLIGHT=
   java.util.concurrent.ConcurrentHashMap.newKeySet();
 private PowerArmorRuntime(){}
 public static boolean full(ServerPlayer p){
  for(int i=0;i<SLOTS.length;i++)
   if(!p.getItemBySlot(SLOTS[i]).is(ArmorStationBlockEntity.expected(i)))return false;
  return true;
 }
 @SubscribeEvent public static void protectLoadedStand(net.neoforged.neoforge.event.level.block.BreakBlockEvent event){
  if(!(event.getState().getBlock() instanceof ArmorStationBlock))return;
  if(event.getLevel().getBlockEntity(event.getPos()) instanceof ArmorStationBlockEntity station
      && station.occupied()){
    event.setCanceled(true);
    if(event.getPlayer() instanceof ServerPlayer p)
      p.sendSystemMessage(net.minecraft.network.chat.Component.literal(
        "Power Armor: remove all suit pieces before dismantling the station."));
  }
 }
 public static boolean powered(ServerPlayer p){
  if(!full(p))return false;
  for(EquipmentSlot slot:SLOTS)
   if(EnergyTool.energy(p.getItemBySlot(slot))<20L)return false;
  return true;
 }
 public static boolean hasCard(ServerPlayer p,String name){
  for(EquipmentSlot slot:SLOTS){
   ItemStack armor=p.getItemBySlot(slot);
   if(armor.getItem() instanceof PowerArmorItem){
    String cards=armor.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
    if(cards!=null && java.util.Arrays.asList(cards.split(",")).contains(name))return true;
   }
  }
  return false;
 }
 @SubscribeEvent public static void logout(
    net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedOutEvent event){
  OWNED_FLIGHT.remove(event.getEntity().getUUID());
 }
 @SubscribeEvent public static void playerTick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer p))return;
  if(p.tickCount%5!=0)return;
  boolean canFly=powered(p)&&hasCard(p,"flight");
  // Suit-only Creative flight is removed when the suit empties. Never revoke
  // creative or spectator permissions.
  boolean natural=p.isCreative()||p.isSpectator();
  if(canFly&&!p.getAbilities().mayfly){
   OWNED_FLIGHT.add(p.getUUID());
   p.getAbilities().mayfly=true;p.onUpdateAbilities();
  }
  if(natural)OWNED_FLIGHT.remove(p.getUUID());
  if(!canFly&&!natural&&OWNED_FLIGHT.remove(p.getUUID())){
   p.getAbilities().flying=false;p.getAbilities().mayfly=false;p.onUpdateAbilities();
  }
  if(powered(p)){
   for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
  }
 }
}
''')
write("ArmorLoadoutData.java",r'''package dev.obsidiannetwork.powerarmor;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import java.util.*;

/** World-persisted loadout recovery, keyed by player UUID.
 * A pending record is NEVER discarded on error; recovery is player-owned.
 */
public final class ArmorLoadoutData extends SavedData {
 public record Backup(String owner,List<ItemStack> previous){
  public static final Codec<Backup> CODEC=RecordCodecBuilder.create(i->i.group(
    Codec.STRING.fieldOf("owner").forGetter(Backup::owner),
    ItemStack.OPTIONAL_CODEC.listOf().fieldOf("previous").forGetter(Backup::previous)
  ).apply(i,Backup::new));
 }
 public static final SavedDataType<ArmorLoadoutData> TYPE=new SavedDataType<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","armor_loadout_backup"),
   ArmorLoadoutData::new,
   Backup.CODEC.listOf().xmap(ArmorLoadoutData::new,ArmorLoadoutData::all));
 private final LinkedHashMap<String,Backup> pending=new LinkedHashMap<>();
 public ArmorLoadoutData(){}
 private ArmorLoadoutData(List<Backup> list){
  for(Backup b:list)if(b.previous().size()==4)pending.putIfAbsent(b.owner(),b);
 }
 public static ArmorLoadoutData get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 public List<Backup> all(){return List.copyOf(pending.values());}
 public boolean has(ServerPlayer p){return pending.containsKey(p.getUUID().toString());}
 public Backup get(ServerPlayer p){return pending.get(p.getUUID().toString());}
 public boolean save(ServerPlayer p,List<ItemStack> previous){
  if(has(p)||previous.size()!=4)return false;
  List<ItemStack> safe=previous.stream().map(ItemStack::copy).toList();
  pending.put(p.getUUID().toString(),new Backup(p.getUUID().toString(),safe));
  setDirty();return true;
 }
 public void finish(ServerPlayer p){
  pending.remove(p.getUUID().toString());setDirty();
 }
 /**
  * Never overwrite an occupied slot, never restore while a suit is still worn.
  * The backup is left intact after any refusal.
  */
 public boolean recover(ServerPlayer p){
  Backup backup=get(p);if(backup==null||PowerArmorRuntime.full(p))return false;
  for(var slot:PowerArmorRuntime.SLOTS)if(!p.getItemBySlot(slot).isEmpty())return false;
  for(int i=0;i<4;i++)p.setItemSlot(PowerArmorRuntime.SLOTS[i],backup.previous().get(i).copy());
  finish(p);return true;
 }
}
''')
write("ArmorStationBlockEntity.java",r'''package dev.obsidiannetwork.powerarmor;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import java.util.*;

/** Stores the actual four suit pieces in the world, including FE and cards. */
public final class ArmorStationBlockEntity extends BlockEntity {
 private final ItemStack[] suit={ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY};
 public ArmorStationBlockEntity(BlockPos p,BlockState state){
  super(ModBlockEntities.ARMOR_STATION.get(),p,state);
 }
 public ItemStack get(int i){return suit[i];}
 public static net.minecraft.world.item.Item expected(int i){
  return switch(i){
   case 0->dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_HELMET.get();
   case 1->dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_CHESTPLATE.get();
   case 2->dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_LEGGINGS.get();
   case 3->dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_BOOTS.get();
   default->throw new IndexOutOfBoundsException(i);
  };
 }
 public boolean occupied(){
  for(ItemStack stack:suit)if(!stack.isEmpty())return true;
  return false;
 }
 public boolean complete(){
  for(int i=0;i<4;i++)if(!suit[i].is(expected(i)))return false;
  return true;
 }
 public void put(int i,ItemStack stack){
  if(!stack.isEmpty()&&!stack.is(expected(i)))
   throw new IllegalArgumentException("Incorrect suit piece for armor slot "+i);
  suit[i]=stack.copy();setChanged();
 }
 public ItemStack take(int i){
  ItemStack current=suit[i].copy();
  suit[i]=ItemStack.EMPTY;
  setChanged();
  return current;
 }
 public List<ItemStack> snapshot(){
  return Arrays.stream(suit).map(ItemStack::copy).toList();
 }
 public void clear(){
  for(int i=0;i<4;i++)suit[i]=ItemStack.EMPTY;
  setChanged();
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.store("armor_suit",ItemStack.OPTIONAL_CODEC.listOf(),snapshot());
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  var list=in.read("armor_suit",ItemStack.OPTIONAL_CODEC.listOf()).orElse(List.of());
  for(int i=0;i<4;i++)suit[i]=i<list.size()?list.get(i).copy():ItemStack.EMPTY;
 }
}
''')
write("ArmorStationBlock.java",r'''package dev.obsidiannetwork.powerarmor;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;
import java.util.*;

/**
 * Right click inserts a matching armor component, or enters once all four are
 * installed. Never silently removes an existing player's equipment.
 */
public final class ArmorStationBlock extends BaseEntityBlock {
 private static final MapCodec<ArmorStationBlock> CODEC=simpleCodec(ArmorStationBlock::new);
 public ArmorStationBlock(Properties p){super(p);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState state){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new ArmorStationBlockEntity(pos,state);
 }
 @Override protected InteractionResult useWithoutItem(BlockState state,Level level,BlockPos pos,
    Player player,BlockHitResult hit){
  if(level.isClientSide())return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer p))return InteractionResult.PASS;
  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;
  // Sneak + right click mounts a component into its matching suit slot.
  // Empty hand retrieves one installed item without overwriting an occupied inventory.
  if(p.isShiftKeyDown()){
   var stack=p.getMainHandItem();
   if(stack.is(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_UPGRADE.get())){
    if(!station.complete())return InteractionResult.FAIL;
    ItemStack chest=station.get(1).copy();
    String upgrades=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
    if(upgrades!=null&&!upgrades.isEmpty())return InteractionResult.FAIL;
    chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),"flight");
    station.put(1,chest);
    if(!p.isCreative())stack.shrink(1);
    p.sendSystemMessage(Component.literal("Power Armor: Flight Upgrade installed."));
    return InteractionResult.SUCCESS;
   }
   if(stack.isEmpty()){
    ItemStack chest=station.get(1).copy();
    String upgrades=chest.get(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
    if("flight".equals(upgrades)){
     ItemStack card=new ItemStack(dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_UPGRADE.get());
     if(!p.getInventory().add(card)){
      p.sendSystemMessage(Component.literal("Power Armor: inventory full; upgrade stays installed."));
      return InteractionResult.FAIL;
     }
     chest.remove(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get());
     station.put(1,chest);
     p.sendSystemMessage(Component.literal("Power Armor: Flight Upgrade returned."));
     return InteractionResult.SUCCESS;
    }
    for(int i=3;i>=0;i--){
     ItemStack stored=station.get(i);
     if(stored.isEmpty())continue;
     ItemStack returned=stored.copy();
     if(!p.getInventory().add(returned)){
       p.sendSystemMessage(Component.literal("Power Armor: inventory full; suit kept safe."));
       return InteractionResult.FAIL;
     }
     station.take(i);
     p.sendSystemMessage(Component.literal("Power Armor: removed component "+(i+1)+"/4"));
     return InteractionResult.SUCCESS;
    }
    return InteractionResult.PASS;
   }
   for(int i=0;i<4;i++){
    if(stack.is(ArmorStationBlockEntity.expected(i))){
     if(!station.get(i).isEmpty())return InteractionResult.FAIL;
     if(!p.isCreative())station.put(i,stack.split(1));
     else station.put(i,stack.copyWithCount(1));
     p.sendSystemMessage(Component.literal("Power Armor: mounted component "+(i+1)+"/4"));
     return InteractionResult.SUCCESS;
    }
   }
   return InteractionResult.PASS;
  }
  if(!station.complete()){
   p.sendSystemMessage(Component.literal("Power Armor: install all four suit parts first"));
   return InteractionResult.SUCCESS;
  }
  var loadouts=ArmorLoadoutData.get(p.level().getServer());
  if(loadouts.has(p)){
   p.sendSystemMessage(Component.literal("Power Armor: unresolved saved loadout. Use /powerarmor recover."));
   return InteractionResult.FAIL;
  }
  List<ItemStack> old=new ArrayList<>();
  for(var slot:PowerArmorRuntime.SLOTS)old.add(p.getItemBySlot(slot).copy());
  if(!loadouts.save(p,old))return InteractionResult.FAIL;
  List<ItemStack> suit=station.snapshot();
  // No destructive operation occurs until all components and backup exist.
  station.clear();
  for(int i=0;i<4;i++)p.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i).copy());
  p.sendSystemMessage(Component.literal("Power Armor engaged. Use /powerarmor exit to return it."));
  return InteractionResult.SUCCESS;
 }
}
''')
write("PowerArmorCommands.java",r'''package dev.obsidiannetwork.powerarmor;
import dev.obsidiannetwork.ObsidianNetwork;
import com.mojang.brigadier.Command;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import java.util.*;

public final class PowerArmorCommands {
 private PowerArmorCommands(){}
 public static void register(net.neoforged.neoforge.event.RegisterCommandsEvent e){
  e.getDispatcher().register(Commands.literal("powerarmor")
   .then(Commands.literal("exit").executes(c->exit(c.getSource().getPlayerOrException())))
   .then(Commands.literal("recover").executes(c->recover(c.getSource().getPlayerOrException()))));
 }
 public static int recover(ServerPlayer p){
  var d=ArmorLoadoutData.get(p.level().getServer());
  if(d.recover(p)){
   p.sendSystemMessage(Component.literal("Original armor restored from saved backup."));
   return Command.SINGLE_SUCCESS;
  }
  p.sendSystemMessage(Component.literal("Recovery refused: backup absent, suit still equipped, or armor slots occupied. No backup was deleted."));
  return 0;
 }
 public static int exit(ServerPlayer p){
  var d=ArmorLoadoutData.get(p.level().getServer());
  var backup=d.get(p);
  if(backup==null||!PowerArmorRuntime.full(p))return 0;
  // Never overwrite another block/entity. Suit stays equipped if no safe room.
  BlockPos pos=null;
  for(var direction:net.minecraft.core.Direction.Plane.HORIZONTAL){
   BlockPos candidate=p.blockPosition().relative(direction);
   if(p.level().isEmptyBlock(candidate)&&p.level().isEmptyBlock(candidate.above())){
    pos=candidate;break;
   }
  }
  if(pos==null){p.sendSystemMessage(Component.literal("Need two empty blocks beside you to exit safely."));return 0;}
  var level=p.level();
  if(!level.setBlock(pos,ObsidianNetwork.ARMOR_STATION.get().defaultBlockState(),3))return 0;
  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity stand)){
   level.removeBlock(pos,false);return 0;
  }
  List<ItemStack> worn=new ArrayList<>();
  for(var slot:PowerArmorRuntime.SLOTS)worn.add(p.getItemBySlot(slot).copy());
  for(int i=0;i<4;i++)stand.put(i,worn.get(i));
  for(int i=0;i<4;i++)p.setItemSlot(PowerArmorRuntime.SLOTS[i],backup.previous().get(i).copy());
  d.finish(p);
  p.sendSystemMessage(Component.literal("Power Armor disengaged. Original armor restored."));
  return Command.SINGLE_SUCCESS;
 }
}
''')

write("PowerArmorExitPayload.java",r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Server-authoritative, empty serverbound exit intent. Never trust client inventory state. */
public record PowerArmorExitPayload() implements CustomPacketPayload {
 public static final Type<PowerArmorExitPayload> TYPE = new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_exit"));
 public static final StreamCodec<RegistryFriendlyByteBuf, PowerArmorExitPayload> STREAM_CODEC =
   StreamCodec.unit(new PowerArmorExitPayload());
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  private Handler(){}
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e) {
   e.registrar("1").playToServer(TYPE,STREAM_CODEC,
     (payload,context)->{
      if(context.player() instanceof ServerPlayer p)PowerArmorCommands.exit(p);
     });
  }
 }
}
''')

write("PowerArmorExitKeyClient.java",r'''package dev.obsidiannetwork.powerarmor;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/** V exits only; entering is by right click on the suit at the station.
 * Registered in vanilla Controls so the player can rebind it.
 */
@EventBusSubscriber(modid="obsidiannetwork", value=Dist.CLIENT)
public final class PowerArmorExitKeyClient {
 private PowerArmorExitKeyClient(){}
 private static final KeyMapping EXIT=new KeyMapping(
   "key.obsidiannetwork.power_armor_exit",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_V,KeyMapping.Category.MISC);
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){
  e.register(EXIT);
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  while(EXIT.consumeClick()){
   Minecraft mc=Minecraft.getInstance();
   if(mc.player==null||mc.screen!=null)continue;
   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(new PowerArmorExitPayload());
  }
 }
}
''')
def put(path,v):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")
# Install the user's supplied red-gold suit textures as shipped resources.
assets=Path(__file__).parent/"assets"/"textures/entity/equipment"
for layer in ("humanoid","humanoid_leggings"):
 src=assets/layer/"power_armor.png"
 assert src.is_file(), "provided power armor texture missing: "+str(src)
 target=r/"assets/obsidiannetwork/textures/entity/equipment"/layer/"power_armor.png"
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(src.read_bytes())
for name in ("helmet","chestplate","leggings","boots","upgrade"):
 put(r/f"assets/obsidiannetwork/models/item/power_armor_{name}.json",
     {"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/netherite_"+("chestplate" if name=="upgrade" else name)}})
 put(r/f"assets/obsidiannetwork/items/power_armor_{name}.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_armor_"+name}})
for name in ["armor_station"]:
 put(r/f"assets/obsidiannetwork/blockstates/{name}.json",
     {"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 put(r/f"assets/obsidiannetwork/models/block/{name}.json",
     {"parent":"minecraft:block/cube_all","textures":{"all":"minecraft:block/iron_block"}})
 put(r/f"assets/obsidiannetwork/models/item/{name}.json",
     {"parent":"obsidiannetwork:block/"+name})
 put(r/f"assets/obsidiannetwork/items/{name}.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+name}})
 put(r/f"data/obsidiannetwork/loot_table/blocks/{name}.json",
     {"type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+name}]}]})
put(r/"assets/obsidiannetwork/equipment/power_armor.json",
    {"layers":{"humanoid":[{"texture":"obsidiannetwork:power_armor"}],
               "humanoid_leggings":[{"texture":"obsidiannetwork:power_armor"}]}})
for locale in ("en_us","de_de"):
 p=r/f"assets/obsidiannetwork/lang/{locale}.json"
 data=json.loads(p.read_text(encoding="utf-8"))
 names={
 "helmet":("Power Armor Helmet","Power-Rüstung Helm"),
 "chestplate":("Power Armor Chestplate","Power-Rüstung Brustpanzer"),
 "leggings":("Power Armor Leggings","Power-Rüstung Beinschutz"),
 "boots":("Power Armor Boots","Power-Rüstung Stiefel"),
 "upgrade":("Power Armor Flight Upgrade","Power-Rüstung Flug-Upgrade")}
 for k,(en,de) in names.items():data["item.obsidiannetwork.power_armor_"+k]=en if locale=="en_us" else de
 data["block.obsidiannetwork.armor_station"]="Armor Station" if locale=="en_us" else "Rüstungsstation"
 put(p,data)
for name,material in (("helmet","netherite_helmet"),("chestplate","netherite_chestplate"),("leggings","netherite_leggings"),("boots","netherite_boots")):
 put(r/f"data/obsidiannetwork/recipe/power_armor_{name}.json",
     {"type":"minecraft:crafting_shaped","pattern":["ABA","CDC","AEA"],
      "key":{"A":"minecraft:netherite_ingot","B":"minecraft:redstone_block",
             "C":"minecraft:diamond","D":"minecraft:"+material,"E":"minecraft:ender_pearl"},
      "result":{"id":"obsidiannetwork:power_armor_"+name,"count":1}})
put(r/"data/obsidiannetwork/recipe/armor_station.json",
    {"type":"minecraft:crafting_shaped","pattern":["IRI","INI","III"],
     "key":{"I":"minecraft:iron_block","R":"minecraft:redstone_block","N":"minecraft:netherite_ingot"},
     "result":{"id":"obsidiannetwork:armor_station","count":1}})
put(r/"data/obsidiannetwork/recipe/power_armor_upgrade.json",
    {"type":"minecraft:crafting_shaped","pattern":["IRI","RDR","IRI"],
     "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone","D":"minecraft:diamond"},
     "result":{"id":"obsidiannetwork:power_armor_upgrade","count":1}})
print("POWER_ARMOR_CLEAN_V17_STAGE1 PASS: four FE armor pieces, persistent backups, protected station, flight card install/remove, configurable server-checked exit key; NO legacy v1.7 scripts")
