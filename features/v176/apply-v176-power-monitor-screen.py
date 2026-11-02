#!/usr/bin/env python3
"""Dedicated central 1.7.6 Power Monitor GUI over a real server-owned menu.

Screen displays one live network's reactors and powerbanks, FE totals,
input/output rates, and ON/OFF for each listed device, with paging.
Server rejects slot writes and revalidates every GUI toggle.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(path,needle,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(needle)==1,("V176_MONITOR_SCREEN_DRIFT",path,s.count(needle))
 p.write_text(s.replace(needle,new,1),encoding="utf-8")
def add(path,code):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_MONITOR_SCREEN_DUPLICATE",path)
 p.write_text(code,encoding="utf-8")

change("power/V176PowerTerminalBlock.java",
 "       ChestMenu.threeRows(id,inv),",
 "       new V176PowerTerminalMenu(id,inv),")
add("power/V176PowerTerminalMenu.java",'''package dev.obsidiannetwork.power;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** All 54 top slots are REAL server-disabled, never virtual drop targets. */
public final class V176PowerTerminalMenu extends ChestMenu {
 public V176PowerTerminalMenu(int id,Inventory inv){
  super(MenuType.GENERIC_9x6,id,inv,new SimpleContainer(54),6);
  for(int slot=0;slot<54;slot++){
   final int index=slot;
   slots.set(slot,new Slot(slots.get(slot).container,index,-100,-100){
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(Player player){return false;}
   });
  }
 }
 @Override public ItemStack quickMoveStack(Player player,int slot){
  // No nonexistent machine slots, no virtual inventory to receive items.
  return ItemStack.EMPTY;
 }
}
''')

add("client/V176PowerMonitorScreen.java",'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.power.V176PowerTerminalBlockEntity;
import dev.obsidiannetwork.power.V176PowerMonitorRules;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import java.util.List;

/** Monitor is entirely read-only, except authenticated server-side toggles. */
public final class V176PowerMonitorScreen extends ContainerScreen {
 private static final int ROWS=4;
 private final BlockPos terminal;
 private int page=0;
 public V176PowerMonitorScreen(ChestMenu menu,Inventory inv,Component title){
  super(menu,inv,title);
  BlockPos pos=null;
  try{
   String s=title.getString();
   int idx=s.lastIndexOf('@');
   String[] xyz=s.substring(idx+1).split(",");
   if(xyz.length==3)pos=new BlockPos(Integer.parseInt(xyz[0]),
     Integer.parseInt(xyz[1]),Integer.parseInt(xyz[2]));
  }catch(RuntimeException ignored){}
  terminal=pos;
 }
 private V176PowerTerminalBlockEntity live(){
  var mc=Minecraft.getInstance();
  if(terminal==null||mc.level==null||!mc.level.hasChunkAt(terminal))return null;
  return mc.level.getBlockEntity(terminal) instanceof V176PowerTerminalBlockEntity be?be:null;
 }
 private static String compact(long v){
  if(v>=1_000_000_000L)return String.format(java.util.Locale.ROOT,"%.1fB",v/1_000_000_000.0);
  if(v>=1_000_000L)return String.format(java.util.Locale.ROOT,"%.1fM",v/1_000_000.0);
  if(v>=1_000L)return String.format(java.util.Locale.ROOT,"%.1fK",v/1_000.0);
  return Long.toString(v);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs | POWER MONITOR",6,6,0xff90f4ff);
  var be=live();
  if(be==null){g.text(font,"Waiting for network status",7,28,0xfff6bc80);return;}
  List<V176PowerMonitorRules.Device> list=be.devices();
  int maxPage=Math.max(0,(list.size()-1)/ROWS);
  if(page>maxPage)page=maxPage;
  if(list.isEmpty())g.text(font,"No connected Reactor / Powerbank",7,35,0xffb7c9d2);
  for(int row=0;row<ROWS;row++){
   int index=page*ROWS+row;
   if(index>=list.size())break;
   var d=list.get(index);
   int y=22+18*row;
   String type=d.type()==V176PowerMonitorRules.DeviceType.REACTOR?"R":"P";
   String state=d.state()==V176PowerMonitorRules.State.ACTIVE?"ON":"OFF";
   g.text(font,type+" "+d.label(),8,y,0xffb0f0ed);
   g.text(font,"IN "+compact(d.inputFePerTick())+" OUT "+compact(d.outputFePerTick())+
       " FE/t",8,y+9,0xffd4dfe5);
   g.text(font,state,153,y+3,d.enabled()?0xff7bffb0:0xffff9595);
  }
  g.text(font,"< "+(page+1)+"/"+Math.max(1,maxPage+1)+" >",62,99,0xff99d4f1);
  if(be.truncated())g.text(font,"Large network: list capped",7,110,0xffffab71);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();
  g.fill(x-3,y-3,x+179,y+h+3,0xff437a9e);
  g.fill(x,y,x+176,y+h,0xff142637);
  g.fill(x+4,y+15,x+172,y+117,0xff081724);
  for(int i=0;i<ROWS;i++){
   int ry=y+20+18*i;
   g.fill(x+5,ry,x+171,ry+17,i%2==0?0xff173242:0xff102633);
   g.fill(x+148,ry+2,x+171,ry+16,0xff30566b);
  }
  g.fill(x+52,y+97,x+112,y+109,0xff244e69);
  // Real vanilla inventory slots retain the same positions as 9x6 ChestMenu.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?139+(i/9)*18:197);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }
 }
 @Override public boolean mouseClicked(double mouseX,double mouseY,int button){
  if(button==0){
   int x=(int)mouseX-getLeftPos(),y=(int)mouseY-getTopPos();
   var be=live();
   if(be!=null){
    var list=be.devices();
    if(y>=20&&y<92&&x>=148&&x<=171){
     int idx=page*ROWS+(y-20)/18;
     if(idx<list.size()&&terminal!=null){
      var d=list.get(idx);
      var mc=Minecraft.getInstance();
      if(mc.player!=null&&mc.player.connection!=null){
       BlockPos target=BlockPos.of(d.position());
       mc.player.connection.sendCommand("powerterminal toggle "+
         terminal.getX()+" "+terminal.getY()+" "+terminal.getZ()+" "+
         target.getX()+" "+target.getY()+" "+target.getZ());
      }
     }
     return true;
    }
    if(y>=96&&y<=111&&x>=52&&x<=112){
     int count=Math.max(1,(list.size()+ROWS-1)/ROWS);
     if(x<82)page=Math.max(0,page-1);
     else page=Math.min(count-1,page+1);
     return true;
    }
   }
  }
  return super.mouseClicked(mouseX,mouseY,button);
 }
}
''')

p=J/"powerarmor/PowerArmorExitKeyClient.java"
s=p.read_text(encoding="utf-8")
assert s.endswith("}\n") and "xsxV176PowerMonitorScreen" not in s
s=s[:-2]+''' @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV176PowerMonitorScreen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().startsWith("xSxLabs Power Monitor @"))return;
  var game=net.minecraft.client.Minecraft.getInstance();
  if(game.player!=null&&chest.getMenu() instanceof net.minecraft.world.inventory.ChestMenu menu)
   e.setNewScreen(new dev.obsidiannetwork.client.V176PowerMonitorScreen(
     menu,game.player.getInventory(),chest.getTitle()));
 }
}
'''
p.write_text(s,encoding="utf-8")
print("V176_POWER_MONITOR_PAGED_LIVE_GUI_SERVER_AUTHENTICATED_TOGGLES_PASS")
