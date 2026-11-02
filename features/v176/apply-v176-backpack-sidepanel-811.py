#!/usr/bin/env python3
"""B811: separate, visible four-slot Backpack sidebar beside main GUI.

This is a render/layout patch after B810, not a claim that Crafting Terminal
listing, search, or crafting is already integrated. Keep build lock active.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
screen=J/"client/V176BackpackScreen.java"
screen.parent.mkdir(parents=True,exist_ok=True)
assert not screen.exists(),"B811_BACKPACK_SCREEN_ALREADY_PRESENT"
screen.write_text('''package dev.obsidiannetwork.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;

/** Four dedicated module slots are visually OUTSIDE the 176px main terminal.
 * No extra item storage is created. Menu slot indices remain 0..3.
 */
public final class V176BackpackScreen extends ContainerScreen {
 private static final int SIDE_X=183;
 private static final int SIDE_W=88;
 public V176BackpackScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
 }
 @Override protected void init(){
  super.init();
  // Center the 176px main GUI AND its separate right-hand 88px module panel.
  leftPos=(width-(imageWidth+95))/2;
 }
 @Override protected void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();
  // Main GUI remains visually independent of all four upgrade/cell slots.
  g.fill(x-3,y-3,x+179,y+h+3,0xff477c96);
  g.fill(x,y,x+176,y+h,0xff132638);
  g.fill(x+7,y+17,x+169,y+119,0xff091b2a);
  g.fill(x+7,y+122,x+169,y+135,0xff274a5b);
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?139+(i/9)*18:197);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff386177);
   g.fill(sx,sy,sx+17,sy+17,0xff203c4b);
  }
  // An explicit seven-pixel GAP separates the panels.
  int sx=x+SIDE_X,sy=y+8;
  g.fill(sx-2,sy-2,sx+SIDE_W,sy+116,0xff4b829d);
  g.fill(sx,sy,sx+SIDE_W-2,sy+114,0xff142d3e);
  for(int i=0;i<4;i++){
   int ax=x+195,ay=y+20+i*24;
   g.fill(ax-2,ay-2,ax+19,ay+19,0xff547a92);
   g.fill(ax-1,ay-1,ax+18,ay+18,0xff203749);
  }
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"NETWORK BACKPACK",8,6,0xffa4edff);
  g.text(font,"MODULES",187,11,0xffa7d9f0);
  g.text(font,"MAGNET",216,26,0xff9df5b0);
  g.text(font,"CELL 1",216,50,0xffcfdfef);
  g.text(font,"CELL 2",216,74,0xffcfdfef);
  g.text(font,"CELL 3",216,98,0xffcfdfef);
  g.text(font,"INVENTORY",8,127,0xffa3bbcc);
 }
}
''',encoding="utf-8")

# Existing PowerArmorExitKeyClient is already a Dist.CLIENT event subscriber.
# Preserve its Power Monitor hook and add a separate Backpack-specific handler.
owner=J/"powerarmor/PowerArmorExitKeyClient.java"
src=owner.read_text(encoding="utf-8")
assert src.endswith("}\n") and "xsxV176BackpackScreen" not in src
src=src[:-2]+''' @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV176BackpackScreen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(e.getNewScreen() instanceof dev.obsidiannetwork.client.V176BackpackScreen)return;
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().equals("xSxLabs Network Backpack"))return;
  var game=net.minecraft.client.Minecraft.getInstance();
  if(game.player!=null&&chest.getMenu() instanceof net.minecraft.world.inventory.ChestMenu menu)
   e.setNewScreen(new dev.obsidiannetwork.client.V176BackpackScreen(
       menu,game.player.getInventory(),chest.getTitle()));
 }
}
'''
owner.write_text(src,encoding="utf-8")
assert "i<4?195:-100,i<4?20+i*24:-100" in (J/"backpack/V176BackpackMenu.java").read_text(encoding="utf-8")
print("V176_B811_SEPARATE_RIGHT_PANEL_MAGNET_CELL1_CELL2_CELL3_READY")
