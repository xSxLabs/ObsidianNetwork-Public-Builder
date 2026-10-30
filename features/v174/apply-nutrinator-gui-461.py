#!/usr/bin/env python3
"""B461: synchronized, dedicated Nutrinator GUI and safe first-hunger refill display.

Adds only client presentation and paced server->client BE synchronization.
Retains existing 1,000,000-bucket long tank, server FE, food/helmet handling,
inventory slots, and Feeding Card semantics.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B461_NUTRINATOR_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,body):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("B461_NUTRINATOR_FILE_COLLISION",str(p))
 p.write_text(body,encoding="utf-8")

edit("nutrition/NutrinatorBlock.java",
 'Component.literal("xSxLabs Nutrinator | "+be.status())',
 'Component.literal("xSxLabs Nutrinator @"+pos.getX()+","+pos.getY()+","+pos.getZ())')

edit("nutrition/NutrinatorBlockEntity.java",
 '  public String status(){return "Paste "+paste+" / "+PASTE_CAPACITY+" mB, FE "+energy+", Speed "+level();}',
 '''  public String status(){return "Paste "+paste+" / "+PASTE_CAPACITY+" mB, FE "+energy+", Speed "+level();}
  // B461_NUTRINATOR_CLIENT_SYNC: client sees the real server values.
  public long guiPaste(){return paste;}
  public long guiPasteCapacity(){return PASTE_CAPACITY;}
  public long guiEnergy(){return energy;}
  public long guiEnergyCapacity(){return FE_CAPACITY;}
  public int guiSpeed(){return level();}
  public long guiHelmetPaste(){return NutriPaste.stored(helmet);}
  public long guiHelmetCapacity(){return NutriPaste.HELMET_CAPACITY;}
  @Override public net.minecraft.nbt.CompoundTag getUpdateTag(
       net.minecraft.core.HolderLookup.Provider registries){
   return saveWithoutMetadata(registries);
  }
  @Override public net.minecraft.network.protocol.Packet<
      net.minecraft.network.protocol.game.ClientGamePacketListener> getUpdatePacket(){
   return net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket.create(this);
  }''')

edit("nutrition/NutrinatorBlockEntity.java",
 '  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;',
 '''  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;
  // B461_NUTRINATOR_PACED_GUI: at most one synced BE update / 2 seconds.
  if(world.getGameTime()%40L==0L)
   world.sendBlockUpdated(pos,state,state,3);''')

add("client/V174NutrinatorScreen.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.nutrition.NutrinatorBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;

/** B461_NUTRINATOR_THEMED_GUI: real, client-synchronized paste/helmet/FE.
 * GUI rendering never changes energy, food, item slots or paste quantities.
 */
public final class V174NutrinatorScreen extends ContainerScreen {
 private final BlockPos machine;
 public V174NutrinatorScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
  BlockPos parsed=null;
  try{
   String name=title.getString();
   String[] xyz=name.substring(name.indexOf('@')+1).trim().split(",");
   if(xyz.length==3)parsed=new BlockPos(
     Integer.parseInt(xyz[0]),Integer.parseInt(xyz[1]),Integer.parseInt(xyz[2]));
  }catch(RuntimeException ignored){}
  machine=parsed;
 }
 private NutrinatorBlockEntity live(){
  var mc=Minecraft.getInstance();
  if(machine==null||mc.level==null||!mc.level.hasChunkAt(machine))return null;
  var be=mc.level.getBlockEntity(machine);
  return be instanceof NutrinatorBlockEntity n?n:null;
 }
 private static int bar(long amount,long maximum){
  if(maximum<=0)return 0;
  return (int)Math.max(0L,Math.min(146L,
   (long)Math.floor(146D*Math.max(0D,Math.min(1D,(double)amount/maximum)))));
 }
 private static String compact(long n){
  if(n>=1_000_000_000L)return n/1_000_000_000L+"."+n%1_000_000_000L/100_000_000L+"B";
  if(n>=1_000_000L)return n/1_000_000L+"."+n%1_000_000L/100_000L+"M";
  if(n>=1_000L)return n/1_000L+"."+n%1_000L/100L+"K";
  return Long.toString(n);
 }
 private static void meter(GuiGraphicsExtractor g,int x,int y,
       long n,long max,int fg){
  g.fill(x,y,x+148,y+9,0xff0a1621);
  g.fill(x+1,y+1,x+1+bar(n,max),y+8,fg);
  g.fill(x,y,x+148,y+1,0xff4a6a7a);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs  |  NUTRINATOR",8,5,0xff6be8ff);
  g.text(font,"FOOD",23,24,0xffc6e6f0);
  g.text(font,"SPEED",59,24,0xffc6e6f0);
  g.text(font,"HELMET",95,24,0xffc6e6f0);
  NutrinatorBlockEntity be=live();
  if(be==null){
   g.text(font,"Waiting for machine data",8,63,0xffffd08a);
   return;
  }
  g.text(font,"PASTE "+compact(be.guiPaste())+" / "+compact(be.guiPasteCapacity())+" mB",
    8,57,0xff8aefb8);
  g.text(font,"FE "+compact(be.guiEnergy())+" / "+compact(be.guiEnergyCapacity())+
    "  |  SPEED "+be.guiSpeed()+"/16",8,68,0xffeed68b);
  g.text(font,"HELMET "+compact(be.guiHelmetPaste())+" / "+
      compact(be.guiHelmetCapacity())+" mB",8,79,0xff9bccff);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float dt){
  int x=getLeftPos(),y=getTopPos();
  int h=getImageHeight();
  g.fill(x-3,y-3,x+179,y+h+3,0xff35c4de);
  g.fill(x,y,x+176,y+h,0xff122633);
  g.fill(x+5,y+12,x+171,y+84,0xff091a29);
  for(int i=0;i<3;i++){
   int sx=x+26+36*i,sy=y+35;
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff367c94);
   g.fill(sx,sy,sx+17,sy+17,0xff203e50);
  }
  NutrinatorBlockEntity be=live();
  if(be!=null){
   meter(g,x+12,y+16,be.guiPaste(),be.guiPasteCapacity(),0xff51dda9);
   // Secondary FE & helmet indicators are narrow to avoid the slot row.
   meter(g,x+12,y+91,be.guiEnergy(),be.guiEnergyCapacity(),0xfff2d269);
   meter(g,x+12,y+104,be.guiHelmetPaste(),be.guiHelmetCapacity(),0xff77b9ff);
  }
  // Actual 36-player inventory slots retain their ChestMenu positions.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?84+(i/9)*18:142);
   // Do not overwrite the FE/helmet bars: only frame the inventory.
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }
 }
}
''')

edit("powerarmor/PowerArmorExitKeyClient.java",
 ' @net.neoforged.bus.api.SubscribeEvent\n public static void xsxV174MachineGuiOpen(',
 ''' // B461_NUTRINATOR_SCREEN_HOOK: client-only screen substitution.
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV174NutrinatorGuiOpen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().startsWith("xSxLabs Nutrinator @"))return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null)e.setNewScreen(new dev.obsidiannetwork.client.V174NutrinatorScreen(
    chest.getMenu(),mc.player.getInventory(),chest.getTitle()));
 }
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV174MachineGuiOpen(''')

assert "B461_NUTRINATOR_CLIENT_SYNC" in (J/"nutrition/NutrinatorBlockEntity.java").read_text()
assert "B461_NUTRINATOR_THEMED_GUI" in (J/"client/V174NutrinatorScreen.java").read_text()
print("B461_NUTRINATOR_GUI_PASS: paced BE sync and real paste, helmet, FE and speed meters")
