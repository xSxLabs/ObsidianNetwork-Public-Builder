#!/usr/bin/env python3
"""Add the two-block wireless network menu, network management and wireless charging.

Must run AFTER apply-wireless-runtime.py. Server-only menu actions; the five
charging categories are independent. Curios support is lazy/optional.
"""
import os
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def update(path,old,new):
 p=j/path;s=p.read_text()
 assert s.count(old)==1, "changed generated source "+path+" :: "+old[:80]
 p.write_text(s.replace(old,new,1))

# Add network names and selection UI via shared menu on both types of antenna.
(j/"menu/WirelessNetworkMenu.java").write_text(r'''package dev.obsidiannetwork.menu;

import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import dev.obsidiannetwork.registry.ModMenus;
import dev.obsidiannetwork.wireless.WirelessNetworkData;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;
import java.util.*;

public final class WirelessNetworkMenu extends AbstractContainerMenu {
 private final BlockPos pos;
 private final ContainerData data;
 private final WirelessNetworkBlockEntity device;
 private final List<String> names=new ArrayList<>();
 public WirelessNetworkMenu(int id,Inventory inv,RegistryFriendlyByteBuf buf){
  this(id,inv,buf.readBlockPos(),null);
  int count=Math.min(128,Math.max(0,buf.readVarInt()));
  for(int k=0;k<count;k++)names.add(buf.readUtf(40));
 }
 public WirelessNetworkMenu(int id,Inventory inv,BlockPos p,WirelessNetworkBlockEntity be){
  this(id,inv,p,be,be==null?new SimpleContainerData(4):new ContainerData(){
   public int get(int index){
    if(!(inv.player instanceof ServerPlayer player))return 0;
    var sd=WirelessNetworkData.get(player.level().getServer());
    var nets=sd.available(player);
    var selected=sd.find(be.networkId());
    return switch(index){
     case 0 -> {
      int n=0;for(int x=0;x<nets.size();x++)if(nets.get(x).id().equals(be.networkId()))n=x;
      yield n;
     }
     case 1 -> nets.size();
     case 2 -> selected==null?0:selected.chargingMask();
     case 3 -> (int)Math.min(32767,be.stored()/1000);
     default -> 0;
    };
   }
   public void set(int index,int value){}
   public int getCount(){return 4;}
  });
  if(be!=null&&inv.player instanceof ServerPlayer p2)
   for(var e:WirelessNetworkData.get(p2.level().getServer()).available(p2))names.add(e.name());
 }
 private WirelessNetworkMenu(int id,Inventory inv,BlockPos p,WirelessNetworkBlockEntity be,ContainerData d){
  super((net.minecraft.world.inventory.MenuType)ModMenus.WIRELESS_NETWORK.get(),id);
  pos=p.immutable();device=be;data=d;addDataSlots(d);
 }
 public int selection(){return data.get(0);}
 public int count(){return data.get(1);}
 public int chargingMask(){return data.get(2);}
 public int energyInThousands(){return data.get(3);}
 public String displayName(){
  int i=selection();
  return i>=0&&i<names.size()?names.get(i):"Network "+(i+1);
 }
 @Override public boolean clickMenuButton(Player player,int button){
  if(!(player instanceof ServerPlayer p)||device==null||!stillValid(player))return false;
  var storage=WirelessNetworkData.get(p.level().getServer());
  if(button==0){
   var list=storage.available(p);
   if(list.isEmpty())return false;
   int index=0;for(int k=0;k<list.size();k++)if(list.get(k).id().equals(device.networkId()))index=k+1;
   device.selectNetwork(list.get(index%list.size()).id());return true;
  }
  if(button==1){
   var created=storage.create(p,"Network "+(storage.entries().size()+1));
   if(created==null)return false;
   device.selectNetwork(created.id());return true;
  }
  if(button>=2&&button<=6){
   int bit=1<<(button-2);
   var current=storage.find(device.networkId());
   return current!=null&&storage.setCharging(p,current.id(),current.chargingMask()^bit);
  }
  return false;
 }
 public boolean stillValid(Player p){
  return p.distanceToSqr(pos.getX()+0.5,pos.getY()+0.5,pos.getZ()+0.5)<=64.0;
 }
 public ItemStack quickMoveStack(Player p,int index){return ItemStack.EMPTY;}
}
''')

(j/"client/WirelessNetworkScreen.java").write_text(r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.menu.WirelessNetworkMenu;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

public final class WirelessNetworkScreen extends AbstractContainerScreen<WirelessNetworkMenu> {
 private static final String[] CATEGORIES={"Inventory","Curios","Armor","Offhand","Hotbar"};
 public WirelessNetworkScreen(WirelessNetworkMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title,224,175);titleLabelX=-10000;inventoryLabelX=-10000;
 }
 @Override protected void init(){
  super.init();
  addRenderableWidget(Button.builder(Component.literal("Next network"),button->click(0)).bounds(leftPos+12,topPos+39,111,20).build());
  addRenderableWidget(Button.builder(Component.literal("Create network"),button->click(1)).bounds(leftPos+128,topPos+39,85,20).build());
  for(int i=0;i<5;i++){
   final int action=i+2;
   addRenderableWidget(Button.builder(Component.literal(CATEGORIES[i]),button->click(action))
     .bounds(leftPos+12,topPos+70+i*19,117,18).build());
  }
 }
 private void click(int id){
  if(minecraft!=null&&minecraft.gameMode!=null)
   minecraft.gameMode.handleInventoryButtonClick(menu.containerId,id);
 }
 public void extractBackground(GuiGraphicsExtractor g,int x,int y,float partial){
  g.fill(leftPos,topPos,leftPos+imageWidth,topPos+imageHeight,-267317992);
  g.outline(leftPos,topPos,imageWidth,imageHeight,-9681017);
 }
 public void extractContents(GuiGraphicsExtractor g,int x,int y,float partial){
  super.extractContents(g,x,y,partial);
  g.text(font,"WIRELESS ENERGY NETWORK",leftPos+12,topPos+7,-1,false);
  g.text(font,menu.displayName()+" ("+menu.count()+")",leftPos+12,topPos+24,-1,false);
  int mask=menu.chargingMask();
  for(int i=0;i<5;i++)
   g.text(font,(mask&(1<<i))!=0?"ON":"OFF",leftPos+150,topPos+75+i*19,(mask&(1<<i))!=0?0xff71e7b4:0xffdf9696,false);
  g.text(font,"Sender buffer: "+menu.energyInThousands()+"k FE",leftPos+12,topPos+163,-1,false);
 }
}
''')

# A user can name new networks exactly via the server-validated command.
(j/"wireless/WirelessNetworkCommands.java").write_text(r'''package dev.obsidiannetwork.wireless;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

public final class WirelessNetworkCommands {
 private WirelessNetworkCommands(){}
 public static void register(RegisterCommandsEvent event){
  event.getDispatcher().register(Commands.literal("wirelessnet")
    .then(Commands.literal("create").then(Commands.argument("name",StringArgumentType.greedyString())
      .executes(ctx->{
       var player=ctx.getSource().getPlayerOrException();
       var name=StringArgumentType.getString(ctx,"name");
       var network=WirelessNetworkData.get(player.level().getServer()).create(player,name);
       player.sendSystemMessage(Component.literal(network==null?"Network could not be created":"Created wireless network: "+network.name()));
       return network==null?0:1;
      })))
    .then(Commands.literal("list").executes(ctx->{
     var player=ctx.getSource().getPlayerOrException();
     var available=WirelessNetworkData.get(player.level().getServer()).available(player);
     for(var net:available)
      player.sendSystemMessage(Component.literal(net.name()+" ["+net.id()+"]"));
     return available.size();
    }))
  );
 }
}
''')

# Player-owned item categories are scanned at most once per 20 server ticks;
# never once per receiver/transmitter BE.
(j/"wireless/WirelessPlayerCharging.java").write_text(r'''package dev.obsidiannetwork.wireless;

import dev.obsidiannetwork.core.EnergyTool;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.transfer.transaction.Transaction;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.fml.ModList;

public final class WirelessPlayerCharging {
 private static final int MAX_PER_PLAYER_TICK=16000;
 private WirelessPlayerCharging(){}
 @net.neoforged.bus.api.SubscribeEvent
 public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)||player.level().getGameTime()%20!=0)return;
  var saved=WirelessNetworkData.get(player.level().getServer());
  int remaining=MAX_PER_PLAYER_TICK;
  // Each network is evaluated once, even with hundreds of receivers.
  for(var net:saved.available(player)){
   if(remaining<=0)break;
   int mask=net.chargingMask();
   if(mask==0||WirelessEnergyRuntime.available(player.level().getServer(),net.id())==0)continue;
   var inventory=player.getInventory().getNonEquipmentItems();
   for(int i=0;i<inventory.size()&&remaining>0;i++){
    int bit=i<9?WirelessNetworkData.HOTBAR:WirelessNetworkData.INVENTORY;
    if((mask&bit)!=0)remaining-=chargeOne(player,net.id(),inventory.get(i),remaining);
   }
   if((mask&WirelessNetworkData.ARMOR)!=0)
    for(EquipmentSlot slot:new EquipmentSlot[]{EquipmentSlot.HEAD,EquipmentSlot.CHEST,EquipmentSlot.LEGS,EquipmentSlot.FEET})
     if(remaining>0)remaining-=chargeOne(player,net.id(),player.getItemBySlot(slot),remaining);
   if((mask&WirelessNetworkData.OFFHAND)!=0&&remaining>0)
    remaining-=chargeOne(player,net.id(),player.getItemBySlot(EquipmentSlot.OFFHAND),remaining);
   if((mask&WirelessNetworkData.CURIOS)!=0&&remaining>0&&ModList.get().isLoaded("curios"))
    remaining-=WirelessCuriosCharging.charge(player,net.id(),remaining);
  }
 }
 static int chargeOne(ServerPlayer player,String network,ItemStack stack,int budget){
  if(stack.isEmpty()||budget<=0)return 0;
  var energy=net.neoforged.neoforge.transfer.access.ItemAccess.forStack(stack).getCapability(Capabilities.Energy.ITEM);
  if(energy!=null){
   int requested;
   try(var sample=Transaction.openRoot()){
    requested=energy.insert(budget,sample);
   }
   if(requested<=0)return 0;
   try(var tx=Transaction.openRoot()){
    int drawn=WirelessEnergyRuntime.pull(player.level().getServer(),network,requested,tx);
    int received=drawn>0?energy.insert(drawn,tx):0;
    if(drawn>0&&drawn==received){tx.commit();return received;}
   }
   return 0;
  }
  // Existing Obsidian EnergyTool items use a custom component, not an FE capability.
  if(EnergyTool.eligible(stack)){
   long missing=Math.max(0,EnergyTool.capacity(stack)-EnergyTool.energy(stack));
   if(missing<=0)return 0;
   int required=(int)Math.min((long)budget,missing);
   try(var tx=Transaction.openRoot()){
    int drawn=WirelessEnergyRuntime.pull(player.level().getServer(),network,required,tx);
    if(drawn<=0)return 0;
    tx.commit();
    EnergyTool.setEnergy(stack,EnergyTool.energy(stack)+drawn);
    return drawn;
   }
  }
  return 0;
 }
}
''')

(j/"wireless/WirelessCuriosCharging.java").write_text(r'''package dev.obsidiannetwork.wireless;

import net.minecraft.server.level.ServerPlayer;
import top.theillusivec4.curios.api.CuriosApi;

/** Loaded only when Curios is actually present; no mandatory Curios classes in core. */
final class WirelessCuriosCharging {
 private WirelessCuriosCharging(){}
 static int charge(ServerPlayer player,String netId,int limit){
  int used=0;
  var optional=CuriosApi.getCuriosInventory(player);
  if(optional.isEmpty())return 0;
  for(var handler:optional.get().getCurios().values()){
   var stacks=handler.getStacks();
   for(int i=0;i<stacks.getSlots()&&used<limit;i++)
    used+=WirelessPlayerCharging.chargeOne(player,netId,stacks.getStackInSlot(i),limit-used);
  }
  return used;
 }
}
''')

# Replace the temporary shift-cycle feedback UI with an actual shared GUI.
p=j/"block/WirelessNetworkBlock.java"
s=p.read_text()
needle=" @Override protected InteractionResult useWithoutItem("
i=s.find(needle)
assert i>0
head=s[:i]
tail=''' @Override protected InteractionResult useWithoutItem(BlockState state,Level level,BlockPos pos,Player player,BlockHitResult hit){
  if(!(level.getBlockEntity(pos) instanceof WirelessNetworkBlockEntity device))return InteractionResult.PASS;
  if(level.isClientSide())return InteractionResult.SUCCESS;
  player.openMenu(new net.minecraft.world.SimpleMenuProvider(
   (id,inv,p)->new dev.obsidiannetwork.menu.WirelessNetworkMenu(id,inv,pos,device),
   Component.literal(transmitter?"Network Transmitter":"Network Receiver")),
   b->{
    b.writeBlockPos(pos);
    if(player instanceof ServerPlayer sp){
     var available=WirelessNetworkData.get(sp.level().getServer()).available(sp);
     b.writeVarInt(available.size());
     for(var network:available)b.writeUtf(network.name(),40);
    }else b.writeVarInt(0);
   });
  return InteractionResult.SUCCESS;
 }
}
'''
assert s.rstrip().endswith("}")
p.write_text(head+tail)

p="registry/ModMenus.java"
f=j/p; s=f.read_text()
anchor='public static final DeferredHolder<MenuType<?>, MenuType<WirelessChargerMenu>> WIRELESS_CHARGER = TYPES.register('
idx=s.find(anchor)
assert idx>0
end=s.find("   );",idx)
assert end>idx
end+=len("   );")
s=s[:end]+'''
   public static final DeferredHolder<MenuType<?>, MenuType<dev.obsidiannetwork.menu.WirelessNetworkMenu>> WIRELESS_NETWORK = TYPES.register(
      "wireless_network", () -> IMenuTypeExtension.create(dev.obsidiannetwork.menu.WirelessNetworkMenu::new)
   );'''+s[end:]
f.write_text(s)

update("client/ClientModEvents.java",
       "event.register((MenuType)ModMenus.WIRELESS_CHARGER.get(), WirelessChargerScreen::new);",
       "event.register((MenuType)ModMenus.WIRELESS_CHARGER.get(), WirelessChargerScreen::new);\n"+
       "      event.register((MenuType)ModMenus.WIRELESS_NETWORK.get(), dev.obsidiannetwork.client.WirelessNetworkScreen::new);")

p=j/"ObsidianNetwork.java";s=p.read_text()
needle="NeoForge.EVENT_BUS.register(EnergyToolEvents.class);"
# Decompiler can show fully-qualified call or import; look for original string.
if needle not in s:
 needle="net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.core.EnergyToolEvents.class);"
assert needle in s, "Cannot locate NeoForge event bus setup"
s=s.replace(needle,needle+'''
      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.wireless.WirelessPlayerCharging.class);
      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(dev.obsidiannetwork.wireless.WirelessNetworkCommands::register);''',1)
p.write_text(s)
print("WIRELESS_NETWORK_UI_CHARGING_V1 PASS: server-authoritative GUI, named networks, five-category wireless charging")
