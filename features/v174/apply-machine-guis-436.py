#!/usr/bin/env python3
"""v1.7.4 B436: dedicated reactor/powerbank/pump GUI with live energy/tank bars.

Server still owns all game data. Client only reads synchronized BE status.
No extra client-only class is touched on dedicated server code paths.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V174_MACHINE_GUI_SOURCE_DRIFT",path,s.count(old),old[:85])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def java(path,content):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_text(content,encoding="utf-8")

# Existing native container + three real slots: do not touch server inventory.
change("reactor/ReactorControllerBlock.java",
 'Component.literal("Reactor | "+be.status())',
 'Component.literal("xSxLabs Reactor @"+p.getX()+","+p.getY()+","+p.getZ())')
change("pump/ElectricWaterPumpBlock.java",
 'Component.literal(be.status())));',
 'Component.literal("xSxLabs Water Pump @"+pos.getX()+","+pos.getY()+","+pos.getZ())));')

# Powerbank is FE-only. A restricted top 9x3 utility menu allows the same
# vanilla player inventory and renders a real FE gauge without fake item slots.
change("powerbank/PowerbankBlock.java",
 'import net.minecraft.network.chat.Component;',
 'import net.minecraft.network.chat.Component;\nimport net.minecraft.world.SimpleMenuProvider;')
change("powerbank/PowerbankBlock.java",
 '  }else sp.sendSystemMessage(Component.literal("xSxLabs Powerbank: "+be.status()));',
 '''  }else sp.openMenu(new SimpleMenuProvider((id,inventory,player)->
      new PowerbankMenu(id,inventory,be),
      Component.literal("xSxLabs Powerbank @"+p.getX()+","+p.getY()+","+p.getZ())));''')
java("powerbank/PowerbankMenu.java",r'''package dev.obsidiannetwork.powerbank;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** FE-only; top slots are hidden, immutable, not fake storage. */
public final class PowerbankMenu extends ChestMenu {
 private final PowerbankBlockEntity bank;
 public PowerbankMenu(int id,Inventory inv,PowerbankBlockEntity be){
  super(MenuType.GENERIC_9x3,id,inv,new SimpleContainer(27),3);
  bank=be;
  for(int i=0;i<27;i++){
   final int idx=i;
   slots.set(i,new Slot(new SimpleContainer(27),idx,-100,-100){
    @Override public boolean mayPlace(ItemStack s){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player player){
  return !bank.isRemoved()&&player.distanceToSqr(
   bank.getBlockPos().getX()+.5,bank.getBlockPos().getY()+.5,
   bank.getBlockPos().getZ()+.5)<=64D;
 }
}
''')
# The top disabled slots must share the same backing Container, not 27
# unrelated inventories, to preserve normal ChestMenu slot semantics.
change("powerbank/PowerbankMenu.java",
 '  super(MenuType.GENERIC_9x3,id,inv,new SimpleContainer(27),3);\n  bank=be;',
 '  super(MenuType.GENERIC_9x3,id,inv,new SimpleContainer(27),3);\n  bank=be;')
change("powerbank/PowerbankMenu.java",
 '   slots.set(i,new Slot(new SimpleContainer(27),idx,-100,-100){',
 '   slots.set(i,new Slot(slots.get(i).container,idx,-100,-100){')
# Use BlockEntity#saveWithoutMetadata for initial chunk loading and
# getUpdatePacket for periodic live GUI updates; only 1 packet per 2 secs.
sync=r''' @Override public net.minecraft.nbt.CompoundTag getUpdateTag(net.minecraft.core.HolderLookup.Provider lookup){
  return saveWithoutMetadata(lookup);
 }
 @Override public net.minecraft.network.protocol.Packet<net.minecraft.network.protocol.game.ClientGamePacketListener> getUpdatePacket(){
  return net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket.create(this);
 }
''';
change("reactor/ReactorControllerBlockEntity.java",
 ' public String status(){return status+" | "+storedFe+" FE | "+waterMb+" mB water";}',
 ''' public String status(){return status+" | "+storedFe+" FE | "+waterMb+" mB water";}
 public long guiEnergy(){return storedFe;}
 public long guiEnergyCapacity(){return FE_CAPACITY;}
 public int guiWater(){return waterMb;}
 public int guiWaterCapacity(){return WATER_CAPACITY;}
 public int guiFuelTicks(){return fuelTicks;}
 public int guiRodAssemblies(){return rodAssemblies;}
'''+sync)
change("powerbank/PowerbankBlockEntity.java",
 ' public String status(){',
 ''' public long guiEnergy(){return amount;}
 public long guiCapacity(){return capacity;}
'''+sync+''' public String status(){''')
change("pump/ElectricWaterPumpBlockEntity.java",
 ' public String status(){return "Electric Water Pump | "+energy+" FE | "+water+" mB | Speed "+speedLevel();}',
 ''' public String status(){return "Electric Water Pump | "+energy+" FE | "+water+" mB | Speed "+speedLevel();}
 public long guiEnergy(){return energy;}
 public long guiEnergyCapacity(){return MAX_FE;}
 public int guiWater(){return water;}
 public int guiWaterCapacity(){return MAX_WATER;}
 public int guiSpeed(){return speedLevel();}
'''+sync)

# GUI refresh in the already-ticking server BE logic: 1 packet per 2 seconds
# per machine instead of 20 packets per second for every cable transfer.
change("reactor/ReactorControllerBlockEntity.java",
 '  if(!(level instanceof ServerLevel sl)||sl.getGameTime()%20L!=0L)return;',
 '''  if(!(level instanceof ServerLevel sl)||sl.getGameTime()%20L!=0L)return;
  if(sl.getGameTime()%40L==0L)sl.sendBlockUpdated(pos,state,state,3);''')
change("pump/ElectricWaterPumpBlockEntity.java",
 '  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;',
 '''  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;
  if(world.getGameTime()%40L==0L)world.sendBlockUpdated(pos,state,state,3);''')
change("powerbank/PowerbankBlockEntity.java",
 '  long phase=Math.floorMod(at.asLong(),400L);',
 '''  if(sl.getGameTime()%40L==0L)sl.sendBlockUpdated(at,state,state,3);
  long phase=Math.floorMod(at.asLong(),400L);''')

java("client/V174MachineScreen.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.reactor.ReactorControllerBlockEntity;
import dev.obsidiannetwork.powerbank.PowerbankBlockEntity;
import dev.obsidiannetwork.pump.ElectricWaterPumpBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.level.block.entity.BlockEntity;

/** B436_MACHINE_GUI: client-only live FE, fuel and coolant gauges.
 * Does NOT change actual storage: server-synchronized block entity state.
 */
public final class V174MachineScreen extends ContainerScreen {
 private enum Machine {REACTOR,POWERBANK,PUMP}
 private final Machine machine;
 private final BlockPos devicePos;
 public V174MachineScreen(ChestMenu menu,Inventory player,Component title){
  super(menu,player,title);
  String name=title.getString();
  machine=name.startsWith("xSxLabs Reactor @")?Machine.REACTOR:
    name.startsWith("xSxLabs Powerbank @")?Machine.POWERBANK:Machine.PUMP;
  BlockPos parsed=null;
  try{
   int i=name.indexOf('@');
   String[] xyz=name.substring(i+1).trim().split(",");
   if(xyz.length==3)parsed=new BlockPos(Integer.parseInt(xyz[0]),
     Integer.parseInt(xyz[1]),Integer.parseInt(xyz[2]));
  }catch(RuntimeException ignored){}
  devicePos=parsed;
 }
 private BlockEntity live(){
  var mc=Minecraft.getInstance();
  return devicePos==null||mc.level==null||!mc.level.hasChunkAt(devicePos)?
    null:mc.level.getBlockEntity(devicePos);
 }
 private static String compact(long value){
  if(value>=1_000_000_000L)return (value/1_000_000_000L)+"."+
    ((value%1_000_000_000L)/100_000_000L)+"B";
  if(value>=1_000_000L)return (value/1_000_000L)+"."+
    ((value%1_000_000L)/100_000L)+"M";
  if(value>=1_000L)return (value/1_000L)+"."+
    ((value%1_000L)/100L)+"K";
  return Long.toString(value);
 }
 private static int pixels(long value,long cap){
  if(cap<=0L)return 0;
  return (int)Math.max(0L,Math.min(150L,(long)Math.floor(150D*
     Math.max(0D,Math.min(1D,(double)value/(double)cap)))));
 }
 private void meter(GuiGraphicsExtractor g,int x,int y,
                    long value,long cap,int fg){
  g.fill(x,y,x+152,y+9,0xff08131e);
  g.fill(x+1,y+1,x+1+pixels(value,cap),y+8,fg);
  g.fill(x,y,x+152,y+1,0xff456275);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs | "+switch(machine){
   case REACTOR->"MULTIBLOCK REACTOR";
   case POWERBANK->"POWERBANK";
   case PUMP->"ELECTRIC WATER PUMP";
  },8,6,0xff64e4f8);
  BlockEntity be=live();
  if(machine==Machine.REACTOR){
   if(be instanceof ReactorControllerBlockEntity reactor){
    g.text(font,"FE  "+compact(reactor.guiEnergy())+" / "+compact(reactor.guiEnergyCapacity()),8,50,0xffc1ebf8);
    g.text(font,"COOLANT  "+reactor.guiWater()+" / "+reactor.guiWaterCapacity()+" mB",8,62,0xff70baff);
    g.text(font,"RODS  "+reactor.guiRodAssemblies()+"  |  FUEL "+reactor.guiFuelTicks()+" ticks",8,74,0xffb1d98a);
   }else g.text(font,"Waiting for controller data",8,56,0xffffc779);
  }else if(machine==Machine.POWERBANK){
   if(be instanceof PowerbankBlockEntity bank){
    g.text(font,"ENERGY STORAGE",8,31,0xffa1d6ec);
    g.text(font,compact(bank.guiEnergy())+" / "+compact(bank.guiCapacity())+" FE",8,44,0xffffffff);
    g.text(font,"Input / output via dedicated ports",8,72,0xffb0d5e0);
   }else g.text(font,"Waiting for powerbank data",8,55,0xffffc779);
  }else{
   if(be instanceof ElectricWaterPumpBlockEntity pump){
    g.text(font,"FE  "+compact(pump.guiEnergy())+" / "+compact(pump.guiEnergyCapacity()),8,49,0xffc1ebf8);
    g.text(font,"WATER  "+pump.guiWater()+" / "+pump.guiWaterCapacity()+" mB",8,61,0xff70baff);
    g.text(font,"SPEED UPGRADES  "+pump.guiSpeed()+" / 16",8,74,0xffb1d98a);
   }else g.text(font,"Waiting for pump data",8,55,0xffffc779);
  }
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos();
  int height=getImageHeight();
  g.fill(x-3,y-3,x+179,y+height+3,0xff38b9d8);
  g.fill(x,y,x+176,y+height,0xff122332);
  g.fill(x+5,y+12,x+171,y+82,0xff091b28);
  BlockEntity be=live();
  if(machine==Machine.REACTOR){
   for(int i=0;i<3;i++){
    int sx=x+(i==0?26:i==1?62:98),sy=y+35;
    g.fill(sx-1,sy-1,sx+18,sy+18,0xff367991);
    g.fill(sx,sy,sx+17,sy+17,0xff1f3947);
   }
   if(be instanceof ReactorControllerBlockEntity r)
    meter(g,x+10,y+20,r.guiEnergy(),r.guiEnergyCapacity(),0xffc6da46);
  }else if(machine==Machine.POWERBANK){
   if(be instanceof PowerbankBlockEntity b)
    meter(g,x+10,y+58,b.guiEnergy(),b.guiCapacity(),0xff57efbd);
  }else{
   g.fill(x+79,y+34,x+98,y+53,0xff367991);
   g.fill(x+80,y+35,x+97,y+52,0xff1f3947);
   if(be instanceof ElectricWaterPumpBlockEntity p)
    meter(g,x+10,y+20,p.guiEnergy(),p.guiEnergyCapacity(),0xfff7d05d);
  }
  // Actual vanilla inventory remains at the registered ChestMenu coordinates.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?84+(i/9)*18:142);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }
 }
}
''')

# Reuse the pre-existing client-only screen event listener. Never import client
# classes from the server registry.
p=J/"powerarmor/PowerArmorExitKeyClient.java"
s=p.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "xsxV174MachineGuiOpen" not in s
s=s[:-1]+r'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV174MachineGuiOpen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  String title=chest.getTitle().getString();
  if(!title.startsWith("xSxLabs Reactor @")
     &&!title.startsWith("xSxLabs Powerbank @")
     &&!title.startsWith("xSxLabs Water Pump @"))return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null)e.setNewScreen(new dev.obsidiannetwork.client.V174MachineScreen(
    chest.getMenu(),mc.player.getInventory(),chest.getTitle()));
 }
}
'''
p.write_text(s,encoding="utf-8")
print("V174_MACHINE_GUI_B436_PASS: synced FE/tank displays for three machines")
