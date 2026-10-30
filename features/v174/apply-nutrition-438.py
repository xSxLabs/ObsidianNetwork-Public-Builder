#!/usr/bin/env python3
"""v1.7.4 B438 NutriPaste: consumable-food Nutrinator and helmet Feeding Card.

Milestone covers persisted 1,000,000-bucket tank, FE-driven all FOOD-component
conversion, 16 real speed slots, direct helmet refill and 1-point server feeding.
A custom nutrient fluid type and a themed synced GUI follow in later stages.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def patch_one(path,needle,replace):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(needle)==1,("B438_NUTRITION_SOURCE_DRIFT",path,s.count(needle),needle[:90])
 p.write_text(s.replace(needle,replace,1),encoding="utf-8")
def java(path,content):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("B438_NUTRITION_SOURCE_COLLISION",str(p))
 p.write_text(content,encoding="utf-8")
def res(path,payload):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("B438_NUTRITION_ASSET_COLLISION",str(p))
 p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

patch_one("ObsidianNetwork.java",
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_PORTAL =',
 '''   // B438_POWER_ARMOR_FEEDING: install in actual Armor Station, helmet only.
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_FEEDING =
     ITEMS.registerItem("power_card_feeding",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"feeding"));
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_PORTAL =''')
patch_one("powerarmor/PowerArmorCards.java",
 '   case "portal" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_PORTAL.get();',
 '''   case "portal" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_PORTAL.get();
   case "feeding" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_FEEDING.get();''')
patch_one("ObsidianNetwork.java",
 '    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.',
 '''    // B438_NUTRINATOR: real feeding machine and upgrade slot.
    public static final DeferredBlock<dev.obsidiannetwork.nutrition.NutrinatorBlock> NUTRINATOR =
      BLOCKS.registerBlock("nutrinator",dev.obsidiannetwork.nutrition.NutrinatorBlock::new,
        p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F).requiresCorrectToolForDrops());
    public static final DeferredItem<BlockItem> NUTRINATOR_ITEM =
      ITEMS.registerSimpleBlockItem("nutrinator",NUTRINATOR);
    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.''')
patch_one("ObsidianNetwork.java",
 '            output.accept((ItemLike)ELECTRIC_WATER_PUMP_ITEM.get());',
 '''            output.accept((ItemLike)ELECTRIC_WATER_PUMP_ITEM.get());
            output.accept((ItemLike)NUTRINATOR_ITEM.get());
            output.accept((ItemLike)POWER_CARD_FEEDING.get());''')
patch_one("registry/ModBlockEntities.java",
 '   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.',
 '''   // B438_NUTRINATOR_BE: server-authoritative food->paste, FE, helmet fill.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.nutrition.NutrinatorBlockEntity>> NUTRINATOR =
     TYPES.register("nutrinator",()->new BlockEntityType(
       dev.obsidiannetwork.nutrition.NutrinatorBlockEntity::new,
       new Block[]{(Block)ObsidianNetwork.NUTRINATOR.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.''')
java("nutrition/NutriPaste.java",r'''package dev.obsidiannetwork.nutrition;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

/** B438_NUTRIPASTE_NBT: persisted long mB, no custom block/item registration.
 * 1000 mB = one restored hunger point, max 1000 buckets per helmet.
 */
public final class NutriPaste {
 public static final String KEY="xsxlabs_nutripaste_mb";
 public static final long HUNGER_COST=1_000L,HELMET_CAPACITY=1_000_000L;
 private NutriPaste(){}
 public static long stored(ItemStack stack){
  if(stack.isEmpty())return 0L;
  CustomData data=stack.get(DataComponents.CUSTOM_DATA);
  if(data==null)return 0L;
  return Math.max(0L,Math.min(HELMET_CAPACITY,data.copyTag().getLongOr(KEY,0L)));
 }
 public static long add(ItemStack stack,long offered){
  if(offered<=0L||stack.isEmpty())return 0L;
  long previous=stored(stack);
  long added=Math.min(offered,HELMET_CAPACITY-previous);
  if(added>0L)set(stack,previous+added);
  return added;
 }
 public static boolean consume(ItemStack stack,long amount){
  if(amount<=0L||stored(stack)<amount)return false;
  set(stack,stored(stack)-amount);
  return true;
 }
 private static void set(ItemStack stack,long amount){
  CustomData original=stack.get(DataComponents.CUSTOM_DATA);
  CompoundTag tag=original==null?new CompoundTag():original.copyTag();
  tag.putLong(KEY,Math.max(0L,Math.min(HELMET_CAPACITY,amount)));
  stack.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
 }
}
''')
java("nutrition/PowerArmorFeeding.java",r'''package dev.obsidiannetwork.nutrition;

import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** B438_FEED_FIRST_HUNGER_POINT: server-only; no food duplication.
 * Requires Feeding Card installed on the helmet, actual stored paste, not
 * simulated FE. Checks once per tick; does not wait for multiple lost points.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorFeeding {
 private PowerArmorFeeding(){}
 @SubscribeEvent public static void feed(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)||player.isSpectator())return;
  var hunger=player.getFoodData();
  if(hunger.getFoodLevel()>=20)return;
  ItemStack helm=player.getItemBySlot(EquipmentSlot.HEAD);
  if(helm.isEmpty()||PowerArmorRuntime.tier(helm,0)<1)return;
  String installed=helm.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(installed==null||!java.util.Arrays.asList(installed.split(",")).contains("feeding"))return;
  // Atomic from the caller's perspective: feed only after complete paste debit.
  if(!NutriPaste.consume(helm,NutriPaste.HUNGER_COST))return;
  hunger.setFoodLevel(Math.min(20,hunger.getFoodLevel()+1));
 }
}
''')
java("nutrition/NutrinatorBlock.java",r'''package dev.obsidiannetwork.nutrition;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;
public final class NutrinatorBlock extends BaseEntityBlock {
 private static final MapCodec<NutrinatorBlock> CODEC=simpleCodec(NutrinatorBlock::new);
 public NutrinatorBlock(Properties props){super(props);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new NutrinatorBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level,BlockState state,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.NUTRINATOR.get(),NutrinatorBlockEntity::tick);
 }
 private InteractionResult use(Level world,BlockPos pos,Player player){
  if(world.isClientSide())return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer sp)
      ||!(world.getBlockEntity(pos) instanceof NutrinatorBlockEntity be))return InteractionResult.PASS;
  sp.openMenu(new SimpleMenuProvider((id,inv,p)->new NutrinatorMenu(id,inv,be),
      Component.literal("xSxLabs Nutrinator | "+be.status())));
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level w,BlockPos p,Player player,BlockHitResult hit){
  return use(w,p,player);
 }
 @Override protected InteractionResult useItemOn(ItemStack held,BlockState s,Level world,BlockPos pos,
     Player player,net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?use(world,pos,player):InteractionResult.PASS;
 }
}
''')
java("nutrition/NutrinatorMenu.java",r'''package dev.obsidiannetwork.nutrition;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
/** Slot 0 = edible food, 1 = 16 speed cards, 2 = Power Armor helmet. */
public final class NutrinatorMenu extends ChestMenu {
 private final NutrinatorBlockEntity machine;
 public NutrinatorMenu(int id,Inventory inv,NutrinatorBlockEntity be){
  super(MenuType.GENERIC_9x3,id,inv,be,3);
  machine=be;
  for(int i=0;i<3;i++){
   final int slot=i;
   slots.set(i,new Slot(be,i,26+36*i,35){
    @Override public boolean mayPlace(ItemStack item){return be.canPlaceItem(slot,item);}
   });
  }
  for(int i=3;i<27;i++){
   int slot=i;
   slots.set(i,new Slot(be,slot,-100,-100){
    @Override public boolean mayPlace(ItemStack s){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player p){return machine.stillValid(p);}
}
''')
java("nutrition/NutrinatorBlockEntity.java",r'''package dev.obsidiannetwork.nutrition;

import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** B438_NUTRINATOR: 1,000,000 buckets (1 billion mB) internal paste,
 * FE-driven conversion of foods including modded items using FOOD component.
 * Existing armor helmet receives paste in its item DATA component.
 */
public final class NutrinatorBlockEntity extends BlockEntity implements Container {
 public static final long PASTE_CAPACITY=1_000_000_000L;
 public static final long FE_CAPACITY=250_000L;
 private long paste=0L,energy=0L;
 private ItemStack food=ItemStack.EMPTY,speed=ItemStack.EMPTY,helmet=ItemStack.EMPTY;
 public NutrinatorBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.NUTRINATOR.get(),p,s);
 }
 public static boolean isFood(ItemStack stack){
  return !stack.isEmpty()&&stack.get(DataComponents.FOOD)!=null;
 }
 public static boolean isSpeed(ItemStack stack){
  if(stack.isEmpty())return false;
  var key=BuiltInRegistries.ITEM.getKey(stack.getItem());
  return key!=null&&"obsidiannetwork".equals(key.getNamespace())
       &&key.getPath().contains("speed_upgrade");
 }
 public static boolean isHelmet(ItemStack stack){
  return !stack.isEmpty()&&PowerArmorRuntime.tier(stack,0)>0;
 }
 private int level(){return isSpeed(speed)?Math.min(16,speed.getCount()):0;}
 public String status(){return "Paste "+paste+" / "+PASTE_CAPACITY+" mB, FE "+energy+", Speed "+level();}
 public static void tick(Level level,BlockPos pos,BlockState state,NutrinatorBlockEntity be){
  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;
  boolean dirty=false;
  int actions=1+be.level();
  // Never fabricate paste: debit one actual food and 100 FE per operation.
  for(int i=0;i<actions&&be.energy>=100L&&!be.food.isEmpty();i++){
   var props=be.food.get(DataComponents.FOOD);
   if(props==null||props.nutrition()<=0)break;
   long made=Math.max(1L,props.nutrition())*1000L;
   if(made>PASTE_CAPACITY-be.paste)break;
   be.food.shrink(1);
   if(be.food.isEmpty())be.food=ItemStack.EMPTY;
   be.energy-=100L;
   be.paste+=made;
   dirty=true;
  }
  // Helmet refill needs no fake fluid transfer; it moves exact mB amount.
  if(be.paste>0L&&isHelmet(be.helmet)){
   long offer=Math.min(be.paste,(long)actions*10_000L);
   long inserted=NutriPaste.add(be.helmet,offer);
   if(inserted>0L){be.paste-=inserted;dirty=true;}
  }
  if(dirty)be.setChanged();
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> energyJournal =
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected Long createSnapshot(){return energy;}
    @Override protected void revertToSnapshot(Long old){energy=old;}
    @Override protected void onRootCommit(Long old){if(old!=energy)setChanged();}
   };
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort =
   new net.neoforged.neoforge.transfer.energy.EnergyHandler(){
    @Override public long getAmountAsLong(){return energy;}
    @Override public long getCapacityAsLong(){return FE_CAPACITY;}
    @Override public int insert(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(n<=0)return 0;
     int received=(int)Math.min((long)n,FE_CAPACITY-energy);
     if(received>0){energyJournal.updateSnapshots(tx);energy+=received;}
     return received;
    }
    @Override public int extract(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
   };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}
 private final net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.item.ItemResource> itemHandler =
    net.neoforged.neoforge.transfer.item.VanillaContainerWrapper.of(this);
 public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.item.ItemResource> itemPort(){return itemHandler;}
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putLong("nutrinatorPaste",paste);
  out.putLong("nutrinatorFE",energy);
  if(!food.isEmpty())out.store("nutrinatorFood",ItemStack.CODEC,food);
  if(!speed.isEmpty())out.store("nutrinatorSpeed",ItemStack.CODEC,speed);
  if(!helmet.isEmpty())out.store("nutrinatorHelmet",ItemStack.CODEC,helmet);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  paste=Math.max(0L,Math.min(PASTE_CAPACITY,in.getLongOr("nutrinatorPaste",0L)));
  energy=Math.max(0L,Math.min(FE_CAPACITY,in.getLongOr("nutrinatorFE",0L)));
  food=in.read("nutrinatorFood",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  speed=in.read("nutrinatorSpeed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  helmet=in.read("nutrinatorHelmet",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  if(!isSpeed(speed))speed=ItemStack.EMPTY;
  if(!isHelmet(helmet))helmet=ItemStack.EMPTY;
 }
 @Override public void preRemoveSideEffects(BlockPos pos,BlockState state){
  if(level instanceof ServerLevel world)for(ItemStack item:new ItemStack[]{food,speed,helmet}){
   if(!item.isEmpty())Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,item.copy());
  }
  super.preRemoveSideEffects(pos,state);
 }
 @Override public int getContainerSize(){return 27;}
 @Override public boolean isEmpty(){return food.isEmpty()&&speed.isEmpty()&&helmet.isEmpty();}
 @Override public ItemStack getItem(int i){return i==0?food:i==1?speed:i==2?helmet:ItemStack.EMPTY;}
 @Override public ItemStack removeItem(int slot,int amount){
  if(amount<=0||slot>2||slot<0)return ItemStack.EMPTY;
  ItemStack current=getItem(slot),taken=current.split(amount);
  if(current.isEmpty())setItem(slot,ItemStack.EMPTY);
  setChanged();return taken;
 }
 @Override public ItemStack removeItemNoUpdate(int i){
  ItemStack old=getItem(i).copy();
  setItem(i,ItemStack.EMPTY);
  return old;
 }
 @Override public void setItem(int i,ItemStack stack){
  if(i==0&&(stack.isEmpty()||isFood(stack)))food=stack.copy();
  else if(i==1&&(stack.isEmpty()||isSpeed(stack)))speed=stack.copy();
  else if(i==2&&(stack.isEmpty()||isHelmet(stack)))helmet=stack.copy();
  setChanged();
 }
 @Override public boolean canPlaceItem(int i,ItemStack stack){
  return i==0?isFood(stack):i==1?isSpeed(stack):i==2&&isHelmet(stack);
 }
 @Override public boolean stillValid(Player player){
  return !isRemoved()&&player.distanceToSqr(worldPosition.getX()+.5,
     worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;
 }
 @Override public void clearContent(){food=speed=helmet=ItemStack.EMPTY;setChanged();}
}
''')
java("nutrition/NutrinatorCapabilities.java",r'''package dev.obsidiannetwork.nutrition;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
@EventBusSubscriber(modid="obsidiannetwork")
public final class NutrinatorCapabilities {
 private NutrinatorCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent e){
  e.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.NUTRINATOR.get(),
    (be,side)->be.energyPort());
  e.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.NUTRINATOR.get(),
    (be,side)->be.itemPort());
 }
}
''')
for name in ("nutrinator",):
 res("assets/obsidiannetwork/blockstates/"+name+".json",{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 res("assets/obsidiannetwork/models/block/"+name+".json",{"parent":"minecraft:block/cube_all","textures":{"all":"minecraft:block/smooth_stone"}})
 res("assets/obsidiannetwork/items/"+name+".json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:block/"+name}})
 res("data/obsidiannetwork/loot_table/blocks/"+name+".json",{
  "type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+name}]}]})
res("data/obsidiannetwork/recipe/nutrinator.json",{
  "type":"minecraft:crafting_shaped","category":"misc","pattern":["IRI","BMB","IRI"],
  "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone_block","B":"minecraft:bucket","M":"minecraft:golden_carrot"},
  "result":{"id":"obsidiannetwork:nutrinator","count":1}})
res("assets/obsidiannetwork/models/item/power_card_feeding.json",{"parent":"minecraft:item/generated","textures":{"layer0":"obsidiannetwork:item/power_armor_upgrade"}})
res("assets/obsidiannetwork/items/power_card_feeding.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_feeding"}})
res("data/obsidiannetwork/recipe/power_card_feeding.json",{
  "type":"minecraft:crafting_shaped","category":"misc","pattern":["GFG","DBD","GRG"],
  "key":{"G":"minecraft:gold_ingot","F":"minecraft:golden_carrot","D":"minecraft:diamond","B":"obsidiannetwork:power_armor_upgrade","R":"minecraft:redstone_block"},
  "result":{"id":"obsidiannetwork:power_card_feeding","count":1}})
for lang,labels in {
 "en_us":{"block.obsidiannetwork.nutrinator":"Nutrinator",
          "item.obsidiannetwork.power_card_feeding":"Feeding Upgrade Card"},
 "de_de":{"block.obsidiannetwork.nutrinator":"Nutrinator",
          "item.obsidiannetwork.power_card_feeding":"Nahrungs-Upgrade-Karte"}}.items():
 p=R/f"assets/obsidiannetwork/lang/{lang}.json";d=json.loads(p.read_text(encoding="utf-8"))
 for key,val in labels.items():
  assert key not in d,(lang,key)
  d[key]=val
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
p=R/"data/minecraft/tags/block/mineable/pickaxe.json"
d=json.loads(p.read_text(encoding="utf-8"))
d["values"].append("obsidiannetwork:nutrinator")
p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
print("V174_NUTRITION_438_PASS: real Nutrinator, energy/food/cable, feeding upgrade, paste in helmet")
