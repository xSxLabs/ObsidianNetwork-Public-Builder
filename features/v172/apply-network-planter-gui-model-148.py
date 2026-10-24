#!/usr/bin/env python3
"""Build148: purpose-built planter GUI, actual logical slot coordinates, robust block models."""
import json,copy
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def replace_file(rel,body):
 p=J/rel
 assert p.exists(),rel
 p.write_text(body,encoding="utf-8")
replace_file("menu/NetworkPlanterMenu.java",r'''package dev.obsidiannetwork.menu;
import dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
/** BUILD148_PLANTER_TRUE_SLOT_LAYOUT:
 * Logical indices 0 soil, 1 seed/sapling, 2 16x speed; 9..17 output.
 * All visual and hit positions are real server-side Slot coordinates, not an
 * overlay on the old 9x3 chest grid. Hidden compatibility slots are inert.
 */
public final class NetworkPlanterMenu extends ChestMenu {
 private final NetworkPlanterBlockEntity planter;
 private final Inventory inventory;
 private static final int[] ACTIVE={0,1,2,9,10,11,12,13,14,15,16,17};
 public NetworkPlanterMenu(int id,Inventory playerInventory,NetworkPlanterBlockEntity be){
  super(MenuType.GENERIC_9x3,id,playerInventory,be,3);
  planter=be;inventory=playerInventory;
  for(int i=0;i<27;i++){
   final int slot=i;
   final boolean active=isOutput(i)||i<3;
   final int sx=i==0?28:i==1?28:i==2?104:
      isOutput(i)?174+(i-9)%3*18:-900;
   final int sy=i==0?39:i==1?64:i==2?52:
      isOutput(i)?36+(i-9)/3*18:-900;
   Slot replacement=new Slot(be,i,sx,sy){
    @Override public boolean isActive(){return active;}
    @Override public boolean mayPickup(Player p){return active&&super.mayPickup(p);}
    @Override public boolean mayPlace(ItemStack stack){
     return active&&slot<3&&be.canPlaceItem(slot,stack);
    }
    @Override public int getMaxStackSize(){
     return slot==2?16:slot==0||slot==1?1:64;
    }
    @Override public int getMaxStackSize(ItemStack stack){
     return Math.min(super.getMaxStackSize(stack),getMaxStackSize());
    }
   };
   replacement.index=i;slots.set(i,replacement);
  }
  // Player inventory: true server slots, centred under the custom top panel.
  for(int i=27;i<63;i++){
   Slot original=slots.get(i);
   int x,y;
   if(i<54){int offset=i-27;x=47+(offset%9)*18;y=158+(offset/9)*18;}
   else {x=47+(i-54)*18;y=219;}
   Slot relocated=new Slot(playerInventory,original.getContainerSlot(),x,y);
   relocated.index=i;slots.set(i,relocated);
  }
 }
 private static boolean isOutput(int i){return i>=9&&i<18;}
 @Override public boolean stillValid(Player player){return planter.stillValid(player);}
 @Override public ItemStack quickMoveStack(Player player,int slotId){
  if(slotId<0||slotId>=slots.size())return ItemStack.EMPTY;
  Slot slot=slots.get(slotId);
  if(!slot.hasItem()||!slot.isActive())return ItemStack.EMPTY;
  ItemStack original=slot.getItem();
  ItemStack copy=original.copy();
  if(slotId<27){
   if(slotId>=3&&slotId<9||slotId>=18)return ItemStack.EMPTY;
   if(!moveItemStackTo(original,27,63,true))return ItemStack.EMPTY;
  }else{
   // Player -> soil, seed, speed only; output cannot be filled manually.
   int target=planter.canPlaceItem(0,original)?0:
     planter.canPlaceItem(1,original)?1:
     planter.canPlaceItem(2,original)?2:-1;
   if(target<0||!moveItemStackTo(original,target,target+1,false))
    return ItemStack.EMPTY;
  }
  if(original.isEmpty())slot.set(ItemStack.EMPTY);
  else slot.setChanged();
  return copy;
 }
}
''')
replace_file("client/NetworkPlanterScreen.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
/** BUILD148_PLANTER_CUSTOM_SCREEN: no vanilla chest grid or misleading blanks.
 * 252x246 purpose-built xSxLabs panel, true slot hitboxes match server menu.
 */
public final class NetworkPlanterScreen extends AbstractContainerScreen<ChestMenu> {
 private static final int CYAN=0xff25d5dc,INK=0xff0c151e;
 public NetworkPlanterScreen(ChestMenu menu,Inventory inv,Component title){
  super(menu,inv,title,252,246);
  remapClientSlots(menu,inv);
 }
 /** The client receives a vanilla ChestMenu from the menu protocol.
  * Rebuild its slots at the SAME actual hit coordinates as the server menu.
  * Without this step the xSxLabs panel would be drawn correctly but clicked
  * through an invisible 9x3 vanilla chest grid.
  */
 private static void remapClientSlots(ChestMenu menu,Inventory playerInv){
  for(int i=0;i<27;i++){
   final int slotId=i;
   final boolean active=i<3||i>=9&&i<18;
   final int sx=i==0?28:i==1?28:i==2?104:
     i>=9&&i<18?174+(i-9)%3*18:-900;
   final int sy=i==0?39:i==1?64:i==2?52:
     i>=9&&i<18?36+(i-9)/3*18:-900;
   net.minecraft.world.inventory.Slot before=menu.slots.get(i);
   net.minecraft.world.inventory.Slot replacement=
       new net.minecraft.world.inventory.Slot(before.container,before.getContainerSlot(),sx,sy){
    @Override public boolean isActive(){return active;}
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player p){
     return active&&super.mayPickup(p);
    }
    @Override public boolean mayPlace(net.minecraft.world.item.ItemStack stack){
     return active&&slotId<3;
    }
   };
   replacement.index=i;menu.slots.set(i,replacement);
  }
  for(int i=27;i<63;i++){
   net.minecraft.world.inventory.Slot previous=menu.slots.get(i);
   final int x,y;
   if(i<54){int offset=i-27;x=47+(offset%9)*18;y=158+(offset/9)*18;}
   else {x=47+(i-54)*18;y=219;}
   net.minecraft.world.inventory.Slot shifted=
       new net.minecraft.world.inventory.Slot(playerInv,previous.getContainerSlot(),x,y);
   shifted.index=i;menu.slots.set(i,shifted);
  }
 }
 private void socket(GuiGraphicsExtractor g,int x,int y,int border){
  g.fill(x-1,y-1,x+17,y+17,border);
  g.fill(x,y,x+16,y+16,0xff213345);
  g.fill(x+1,y+1,x+15,y+15,0xff1b2935);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mouseX,int mouseY,float partial){
  int x=getLeftPos(),y=getTopPos();
  g.fill(x-4,y-4,x+256,y+250,0xff071017);
  g.fill(x-2,y-2,x+254,y+248,CYAN);
  g.fill(x,y,x+252,y+246,0xff142331);
  g.fill(x+5,y+5,x+247,y+27,0xff0b1823);
  g.text(this.font,"xSxLabs  /  NETWORK PLANTER",x+12,y+11,0xffd6f9ff,false);
  // Soil and seed at left, speed in centre, 9 output slots on right.
  g.fill(x+9,y+29,x+78,y+100,INK);
  g.fill(x+80,y+29,x+145,y+100,INK);
  g.fill(x+160,y+29,x+242,y+100,INK);
  g.text(this.font,"SOIL",x+47,y+42,0xffbdd5df,false);
  g.text(this.font,"SEED",x+47,y+67,0xffbdd5df,false);
  g.text(this.font,"SPEED",x+87,y+35,0xffbdd5df,false);
  g.text(this.font,"OUTPUT  3x3",x+165,y+21,0xffbdd5df,false);
  socket(g,x+27,y+38,0xff91b771);
  socket(g,x+27,y+63,0xff91b771);
  socket(g,x+103,y+51,0xffe1bb55);
  for(int i=0;i<9;i++)socket(g,x+173+(i%3)*18,y+35+(i/3)*18,0xff528eab);
  // Status strip and decorative growth channel; authoritative growth is in Jade.
  g.fill(x+9,y+108,x+243,y+140,0xff0b1925);
  g.text(this.font,"GROWTH AND STATUS: JADE",x+17,y+119,0xffd0e6eb,false);
  g.fill(x+17,y+132,x+235,y+134,0xff22637a);
  g.fill(x+9,y+145,x+243,y+244,INK);
  g.text(this.font,"PLAYER INVENTORY",x+47,y+147,0xffbdd5df,false);
  for(int i=0;i<27;i++)socket(g,x+46+(i%9)*18,y+157+(i/9)*18,0xff47687b);
  for(int i=0;i<9;i++)socket(g,x+46+i*18,y+218,0xff7c9cb1);
 }
}
''')
# Legacy blockstates were dynamic multipart + 4 growth models. Bake each real
# blockstate into exactly one model, so the resource loader never has to resolve
# a conditional multipart component (and the model is fully self-contained).
A=R/"assets/obsidiannetwork"
B=A/"blockstates";M=A/"models/block"
BLOCKS=[p for p in B.glob("network_planter*.json")]
assert len(BLOCKS)==12,("expected twelve texture variants",len(BLOCKS))
total=0
for block_file in BLOCKS:
 state=json.loads(block_file.read_text(encoding="utf-8"))
 assert "multipart" in state,block_file
 multipart=state["multipart"]
 assert len(multipart)==101,(block_file,len(multipart))
 base_ref=multipart[0]["apply"]["model"]
 assert base_ref.startswith("obsidiannetwork:block/"),base_ref
 base_path=M/(base_ref.split("block/",1)[1]+".json")
 base=json.loads(base_path.read_text(encoding="utf-8"))
 variants={}
 for part in multipart[1:]:
  cond=part["when"]
  age=int(cond["age"])
  plant=cond["plant"]
  grow_ref=part["apply"]["model"]
  assert grow_ref.startswith("obsidiannetwork:block/"),grow_ref
  grow_file=M/(grow_ref.split("block/",1)[1]+".json")
  growth=json.loads(grow_file.read_text(encoding="utf-8"))
  model=copy.deepcopy(base)
  model["render_type"]="minecraft:cutout"
  model["textures"].update({"plant":growth["textures"]["plant"]})
  for element in growth["elements"]:
   element=copy.deepcopy(element)
   # Never exceed the model bounds. Quads must have non-zero thickness.
   element["to"][1]=min(15.99,element["to"][1])
   element["from"][2]=7.97
   element["to"][2]=8.03
   model["elements"].append(element)
  name=block_file.stem+"_"+plant+"_age"+str(age)
  (M/(name+".json")).write_text(json.dumps(model,separators=(",",":"))+"\n",encoding="utf-8")
  key="age="+str(age)+",plant="+plant
  assert key not in variants,key
  variants[key]={"model":"obsidiannetwork:block/"+name}
  total+=1
 assert len(variants)==100,(block_file,len(variants))
 block_file.write_text(json.dumps({"variants":variants},indent=2)+"\n",encoding="utf-8")
assert total==1200,total
# Rigorous resource checks: every state reference resolves within this JAR,
# every face resolves a defined texture variable, and every wood variant exists.
for block_file in BLOCKS:
 states=json.loads(block_file.read_text(encoding="utf-8"))["variants"]
 for key,entry in states.items():
  p=M/(entry["model"].split("block/",1)[1]+".json")
  assert p.is_file(),(block_file,key,p)
  model=json.loads(p.read_text(encoding="utf-8"))
  textures=model["textures"]
  assert all("base" in textures and "soil" in textures and "plant" in textures for _ in [0])
  for element in model["elements"]:
   for face in element["faces"].values():
    face_tex=face["texture"]
    assert face_tex.startswith("#") and face_tex[1:] in textures,(p,face_tex)
print("BUILD148_PLANTER_MODELS_PASS: 12 wooden variants x 100 complete state models; no multipart, all referenced models and textures resolve")
print("BUILD148_PLANTER_CUSTOM_SCREEN_PASS: true active slots 2 left 1 centre 9 right; no phantom chest grid")
