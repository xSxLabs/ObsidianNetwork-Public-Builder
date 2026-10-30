#!/usr/bin/env python3
"""v1.7.4 B442: obtainable interactive in-game multiblock building guidebook.

A real usable guide item opens a server-authorized ChestMenu (non-item top),
then the client replaces the screen with a four-page layer-diagram view.
No packets for cursor/navigation; menus never expose fake inventory slots.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def change(rel,a,b):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(a)==1,("B442_SOURCE_DRIFT",rel,s.count(a),a[:90])
 p.write_text(s.replace(a,b,1),encoding="utf-8")
def java(rel,s):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_text(s,encoding="utf-8")
def resource(rel,obj):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
change("ObsidianNetwork.java",
    "    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.",
    '''    // B442_GUIDEBOOK: obtainable in-game layer-by-layer builder.
    public static final DeferredItem<dev.obsidiannetwork.guide.NetworkGuidebookItem> NETWORK_GUIDEBOOK =
      ITEMS.registerItem("network_guidebook",dev.obsidiannetwork.guide.NetworkGuidebookItem::new);
    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.''')
change("ObsidianNetwork.java",
    '            output.accept((ItemLike)ELECTRIC_WATER_PUMP_ITEM.get());',
    '''            output.accept((ItemLike)ELECTRIC_WATER_PUMP_ITEM.get());
            output.accept((ItemLike)NETWORK_GUIDEBOOK.get());''')
java("guide/NetworkGuidebookItem.java",r'''package dev.obsidiannetwork.guide;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** B442_GUIDEBOOK_USE: right-click in air opens server-validated view. */
public final class NetworkGuidebookItem extends Item {
 public NetworkGuidebookItem(Properties properties){super(properties.stacksTo(1));}
 @Override public InteractionResult use(Level world,Player player,InteractionHand hand){
  if(!world.isClientSide()&&player instanceof ServerPlayer sp){
   sp.openMenu(new SimpleMenuProvider((id,inventory,p)->new NetworkGuidebookMenu(id,inventory),
      Component.literal("xSxLabs Multiblock Guidebook")));
  }
  return InteractionResult.SUCCESS;
 }
}
''')
java("guide/NetworkGuidebookMenu.java",r'''package dev.obsidiannetwork.guide;

import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** No top inventory (only vanilla player inventory below the plans). */
public final class NetworkGuidebookMenu extends ChestMenu {
 public NetworkGuidebookMenu(int id,Inventory inv){
  super(MenuType.GENERIC_9x3,id,inv,new SimpleContainer(27),3);
  for(int i=0;i<27;i++){
   final int index=i;
   slots.set(i,new Slot(slots.get(i).container,index,-100,-100){
    @Override public boolean mayPlace(ItemStack s){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
}
''')
java("client/V174GuidebookScreen.java",r'''package dev.obsidiannetwork.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;

/** Interactive layer plans for exactly valid minimum 5x5x5 / 3x3x3 builds.
 * # = shell casing/glass, . = empty interior, R = fuel assembly,
 * C = controller, I = item input, W = water, E = FE out,
 * + = Powerbank FE input, - = Powerbank FE output.
 */
public final class V174GuidebookScreen extends ContainerScreen {
 private int page=0;
 private static final String[] TITLE={
  "REACTOR 5x5x5 : FLOOR Y0",
  "REACTOR 5x5x5 : PORTS Y1",
  "REACTOR 5x5x5 : Y2-Y3",
  "REACTOR 5x5x5 : ROOF Y4",
  "POWERBANK 3x3x3 : FLOOR",
  "POWERBANK 3x3x3 : MIDDLE",
  "POWERBANK 3x3x3 : ROOF",
  "LARGER BUILDS & WIRING"
 };
 private static final String[][] PLAN={
  {"#####","#####","#####","#####","#####"},
  {"##C##","#...#","I.R.W","#...#","##E##"},
  {"#####","#...#","#.R.#","#...#","#####"},
  {"#####","#####","#####","#####","#####"},
  {"###","###","###"},
  {"#C#","+. -","###"},
  {"###","###","###"},
  {"Reactor: sides 5..64 blocks","Powerbank: 3x3x3..12","Fuel rods inside reactor","Connect FE and fluid cables","Pump requires FE + water"}
 };
 private static final String[] NOTE={
  "Solid casing or reactor glass",
  "C controller / I item / W water / E FE",
  "Repeat middle without other ports",
  "Close exterior; no holes",
  "3x3x3 minimum, air inside",
  "Input +, output -, center is air",
  "Powerbank top shell is solid",
  "Use real ports; loaded chunks only"
 };
 public V174GuidebookScreen(ChestMenu menu,Inventory inv,Component title){
  super(menu,inv,title);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs  |  BUILDER GUIDE",8,4,0xff5ce9ff);
  g.text(font,TITLE[page],8,15,0xfff5d68c);
  String[] rows=PLAN[page];
  for(int i=0;i<rows.length;i++)
   g.text(font,rows[i],12,27+i*9,0xffd7f8e3);
  g.text(font,NOTE[page],8,73,0xffb2d1dc);
  g.text(font,"< PREV",8,91,0xffa1f7ff);
  g.text(font,"PAGE "+(page+1)+"/"+PLAN.length,67,91,0xffffffff);
  g.text(font,"NEXT >",131,91,0xffa1f7ff);
 }
 @Override protected void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=getLeftPos(),y=getTopPos();
  int height=getImageHeight();
  g.fill(x-4,y-5,x+180,y+height+5,0xff2dc3d6);
  g.fill(x,y,x+176,y+height,0xff102936);
  g.fill(x+5,y+22,x+171,y+72,0xff09212d);
  g.fill(x+5,y+85,x+171,y+103,0xff1d4153);
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18,sy=y+(i<27?84+(i/9)*18:142);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff36687a);
   g.fill(sx,sy,sx+17,sy+17,0xff1f3846);
  }
 }
 @Override public boolean mouseClicked(MouseButtonEvent e,boolean doubleClick){
  if(e.button()==0){
   double x=e.x()-getLeftPos(),y=e.y()-getTopPos();
   if(y>=85D&&y<=107D){
    if(x>=5D&&x<58D){page=(page+PLAN.length-1)%PLAN.length;return true;}
    if(x>=119D&&x<=175D){page=(page+1)%PLAN.length;return true;}
   }
  }
  return super.mouseClicked(e,doubleClick);
 }
}
''')

# Correct the 3x3x3 cross-section labels: one controller and two ports on
# exterior, the middle cell must stay air and never be marked as a port.
change("client/V174GuidebookScreen.java",
   '{"#C#","+. -","###"},',
   '{"#C#","+. -","###"},')
# The 5-character middle row fits GUI but 3x3 layout needs exactly 3 chars:
change("client/V174GuidebookScreen.java",
   '{"#C#","+. -","###"},',
   '{"#C#","+. -","###"},')
# User-facing guide draws the 3x3 center as air. The left/right symbols
# show FE input/output; spaces are not blocks and do not affect validation.
change("client/V174GuidebookScreen.java",
   '{"#C#","+. -","###"},',
   '{"#C#","+-#","###"},')
# The above shows + and - as adjacent surface ports and # for third cell.
# Provide explicit geometric cross-section using + . - contiguous.
change("client/V174GuidebookScreen.java",
   '{"#C#","+-#","###"},',
   '{"#C#","+.-","###"},')
p=J/"powerarmor/PowerArmorExitKeyClient.java"
s=p.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "xsxV174GuidebookOpen" not in s
s=s[:-1]+r'''
 @net.neoforged.bus.api.SubscribeEvent
 public static void xsxV174GuidebookOpen(net.neoforged.neoforge.client.event.ScreenEvent.Opening e){
  if(!(e.getNewScreen() instanceof net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!"xSxLabs Multiblock Guidebook".equals(chest.getTitle().getString()))return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null)e.setNewScreen(new dev.obsidiannetwork.client.V174GuidebookScreen(
    chest.getMenu(),mc.player.getInventory(),chest.getTitle()));
 }
}
'''
p.write_text(s,encoding="utf-8")

resource("assets/obsidiannetwork/models/item/network_guidebook.json",{
 "parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/book"}})
resource("assets/obsidiannetwork/items/network_guidebook.json",{
 "model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_guidebook"}})
resource("data/obsidiannetwork/recipe/network_guidebook.json",{
 "type":"minecraft:crafting_shaped","category":"misc",
 "pattern":["PPP","PBP","PPP"],
 "key":{"P":"minecraft:paper","B":"minecraft:book"},
 "result":{"id":"obsidiannetwork:network_guidebook","count":1}})
for lang,label in (("de_de","Multiblock-Baubuch"),("en_us","Multiblock Building Guide")):
 p=R/f"assets/obsidiannetwork/lang/{lang}.json";obj=json.loads(p.read_text(encoding="utf-8"))
 assert "item.obsidiannetwork.network_guidebook" not in obj
 obj["item.obsidiannetwork.network_guidebook"]=label
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V174_GUIDEBOOK_442_PASS: real item, 8 interactive plan pages and client-only GUI")
