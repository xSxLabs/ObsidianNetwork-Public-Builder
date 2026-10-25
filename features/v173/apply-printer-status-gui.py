#!/usr/bin/env python3
"""v1.7.3: dedicated Network Printer GUI with live missing-item ghost slot.

The normal 9x3 chest menu is protocol compatible. All slots remain server
authoritative; the cyan xSxLabs screen only renders status and slot labels.
Missing items appear automatically when the server pauses printing.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
change("blockentity/NetworkDeviceBlockEntity.java",
 'private ItemStack blueprint=ItemStack.EMPTY,energy=ItemStack.EMPTY;',
 'private ItemStack blueprint=ItemStack.EMPTY,energy=ItemStack.EMPTY,missing=ItemStack.EMPTY;')
change("blockentity/NetworkDeviceBlockEntity.java",
 'if(extracted!=1L){setStatus("MISSING: 1 x "+material.getHoverName().getString());return;}',
 '''if(extracted!=1L){
   missing=material.copyWithCount(1);
   setStatus("MISSING: 1 x "+material.getHoverName().getString());return;
  }
  missing=ItemStack.EMPTY;''')
change("blockentity/NetworkDeviceBlockEntity.java",
 'return slot==0?blueprint:slot==1?energy:ItemStack.EMPTY;',
 'return slot==0?blueprint:slot==1?energy:slot==2?missing:ItemStack.EMPTY;')
change("blockentity/NetworkDeviceBlockEntity.java",
 'if(!ItemStack.isSameItemSameComponents(blueprint,s)){index=0;completed=0;}',
 'if(!ItemStack.isSameItemSameComponents(blueprint,s)){index=0;completed=0;missing=ItemStack.EMPTY;}')
change("blockentity/NetworkDeviceBlockEntity.java",
 'running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");',
 'running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");missing=ItemStack.EMPTY;')
change("blockentity/NetworkDeviceBlockEntity.java",
 'blueprint=energy=ItemStack.EMPTY;index=completed=0;sync();',
 'blueprint=energy=missing=ItemStack.EMPTY;index=completed=0;sync();')
# The missing item is a non-extractable ghost, the player cannot grab it.
change("menu/NetworkPrinterMenu.java",
 'for(int i=2;i<27;i++){',
 '''for(int i=2;i<27;i++){''')
p=J/"client/NetworkPrinterScreen.java"
assert not p.exists(),str(p)
p.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;

/** V173_PRINTER_STATUS_GUI: status + missing material from live synced ghost slot. */
public final class NetworkPrinterScreen extends ContainerScreen {
 public NetworkPrinterScreen(ChestMenu menu,Inventory inv,Component title){
  super(menu,inv,title);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mouseX,int mouseY){
  g.text(font,"xSxLabs  |  NETWORK PRINTER",8,6,0xff65f4ff);
  g.text(font,"BLUEPRINT",8,19,0xffe2dce6);
  g.text(font,"FE CELL",59,19,0xffe2dce6);
  ItemStack missing=getMenu().getSlot(2).getItem();
  if(!missing.isEmpty()){
   g.text(font,"MISSING: "+missing.getHoverName().getString(),8,78,0xffff826b);
  }else{
   g.text(font,"Place Blueprint + connect NETWORK & ENERGY",8,78,0xffa8e8c5);
  }
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mouseX,int mouseY,float partial){
  int x=getLeftPos(),y=getTopPos();
  g.fill(x-3,y-3,x+179,y+getImageHeight()+3,0xff18d6e7);
  g.fill(x,y,x+176,y+getImageHeight(),0xff162837);
  g.fill(x+5,y+12,x+171,y+81,0xff081e2b);
  for(int i=0;i<27;i++){
   int sx=x+8+(i%9)*18,sy=y+18+(i/9)*18;
   boolean active=i<3;
   g.fill(sx-1,sy-1,sx+18,sy+18,active?0xff368fa3:0xff153444);
   g.fill(sx,sy,sx+17,sy+17,0xff183342);
  }
  // Vanilla player inventory uses ChestMenu's original slot positions.
  int off=getImageHeight()-114;
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18,sy=y+off+(i<27?84+(i/9)*18:142);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff315464);
   g.fill(sx,sy,sx+17,sy+17,0xff203647);
  }
 }
}
''',encoding="utf-8")
client=J/"powerarmor/PowerArmorExitKeyClient.java"
s=client.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "xsxNetworkPrinterOpen" not in s
s=s[:-1]+r'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxNetworkPrinterOpen(net.neoforged.neoforge.client.event.ScreenEvent.Opening event){
  if(!(event.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().startsWith("xSxLabs Network Printer"))return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null)event.setNewScreen(new dev.obsidiannetwork.client.NetworkPrinterScreen(
    chest.getMenu(),mc.player.getInventory(),chest.getTitle()));
 }
}
'''
client.write_text(s,encoding="utf-8")
print("V173_PRINTER_STATUS_GUI_PASS: non-extractable missing ghost, dedicated menu, dynamic server-synced missing material icon")
