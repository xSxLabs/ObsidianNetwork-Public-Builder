#!/usr/bin/env python3
"""B817: live Magnet ON/OFF, whitelist/blacklist and 54 editable ghost filters.

The filter editor is a *mode* in the same main item-list panel, not a crafting
grid or another inventory. All writes use the real installed Magnet upgrade
inside the real backpack ItemStack; player items are NOT consumed as samples.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(path,old,new):
 file=J/path
 source=file.read_text(encoding="utf-8")
 assert source.count(old)==1,("B817_SOURCE_DRIFT",path,source.count(old),old[:100])
 file.write_text(source.replace(old,new,1),encoding="utf-8")

menu="backpack/V176BackpackMenu.java"
patch(menu,'''  private int page=0;
  private ItemStack cacheSource''',
'''  private int page=0;
  private boolean filterEditor=false;
  private ItemStack cacheSource''')
patch(menu,'''   if(slot<4)return V176BackpackCells.slots(source.current()).get(slot).copy();
   var entry=viewed(slot);''',
'''   if(slot<4)return V176BackpackCells.slots(source.current()).get(slot).copy();
   if(filterEditor){
    if(slot>=49)return ItemStack.EMPTY;
    var magnet=V176BackpackCells.magnet(source.current());
    if(magnet.isEmpty())return ItemStack.EMPTY;
    var templates=magnet.getOrDefault(
       net.minecraft.core.component.DataComponents.CONTAINER,
       net.minecraft.world.item.component.ItemContainerContents.EMPTY);
    int position=page*45+slot-4;
    return position>=0&&position<templates.getSlots()
       ?templates.getStackInSlot(position).copy():ItemStack.EMPTY;
   }
   var entry=viewed(slot);''')
patch(menu,'''   int last=Math.max(0,(resultEntries().size()-1)/45);''',
'''   int last=filterEditor?1:Math.max(0,(resultEntries().size()-1)/45);''')
patch(menu,''' public boolean search(ServerPlayer player,String query){''',
''' public boolean toggleFilterEditor(ServerPlayer player){
  if(player.containerMenu!=this||!storage.source.valid())return false;
  storage.filterEditor=!storage.filterEditor;
  storage.page=0;
  broadcastChanges();
  return true;
 }
 public boolean editFilter(ServerPlayer player,int filterIndex,int invIndex){
  if(player.containerMenu!=this||!storage.filterEditor||!storage.source.valid()
      ||filterIndex<0||filterIndex>=V176BackpackCells.FILTER_SLOTS
      ||invIndex<-1||invIndex>=36)return false;
  if(V176BackpackCells.magnet(storage.source.current()).isEmpty())return false;
  ItemStack sample=invIndex==-1?ItemStack.EMPTY:player.getInventory().getItem(invIndex);
  if(sample.getItem() instanceof NetworkBackpackItem)return false;
  if(invIndex>=0&&sample.isEmpty())return false;
  ItemStack next=storage.source.current().copy();
  if(!V176BackpackCells.setMagnetFilter(next,filterIndex,sample))return false;
  if(!storage.source.save(next))return false;
  broadcastChanges();
  return true;
 }
 public boolean search(ServerPlayer player,String query){''')
patch(menu,'''  if(player.containerMenu!=this||!storage.source.valid()
     ||index<0||index>=45||wanted<=0||wanted>64)return false;''',
'''  if(player.containerMenu!=this||!storage.source.valid()
     ||storage.filterEditor||index<0||index>=45||wanted<=0||wanted>64)return false;''')
patch(menu,'''  if(!(p instanceof ServerPlayer player)||!storage.source.valid()
     ||index<54||index>=slots.size())return ItemStack.EMPTY;''',
'''  if(!(p instanceof ServerPlayer player)||!storage.source.valid()
     ||storage.filterEditor||index<54||index>=slots.size())return ItemStack.EMPTY;''')

commands="backpack/V176BackpackCommands.java"
patch(commands,'''    .then(Commands.literal("magnet")''',
'''    .then(Commands.literal("filters").executes(ctx->{
      var player=ctx.getSource().getPlayerOrException();
      return player.containerMenu instanceof V176BackpackMenu menu
          &&menu.toggleFilterEditor(player)?1:0;
    }))
    .then(Commands.literal("setfilter")
      .then(Commands.argument("filterIndex",IntegerArgumentType.integer(0,53))
       .then(Commands.argument("inventoryIndex",IntegerArgumentType.integer(0,35))
        .executes(ctx->setFilter(ctx.getSource().getPlayerOrException(),
          IntegerArgumentType.getInteger(ctx,"filterIndex"),
          IntegerArgumentType.getInteger(ctx,"inventoryIndex"))))))
    .then(Commands.literal("clearfilter")
      .then(Commands.argument("filterIndex",IntegerArgumentType.integer(0,53))
       .executes(ctx->setFilter(ctx.getSource().getPlayerOrException(),
         IntegerArgumentType.getInteger(ctx,"filterIndex"),-1))))
    .then(Commands.literal("magnet")''')
patch(commands,''' private static int search(ServerPlayer p,String term){''',
''' private static int setFilter(ServerPlayer p,int filter,int inventory){
  return p.containerMenu instanceof V176BackpackMenu menu
     &&menu.editFilter(p,filter,inventory)?1:0;
 }
 private static int search(ServerPlayer p,String term){''')

screen="client/V176BackpackScreen.java"
patch(screen,''' private boolean countSort=false;
 private static final int SIDE_X''',
''' private boolean countSort=false;
 private boolean filterEditor=false;
 private int selectedFilter=-1;
 private int filterPage=0;
 private static final int SIDE_X''')
patch(screen,'''  if(autoFocus)setFocused(searchBox);
 }
 private static void command''',
'''  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("MAGNET"),b->{
       var module=menu.getSlot(0).getItem();
       var tag=module.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
          net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
       command(tag.getBooleanOr("xsx_v176_magnet_on",false)
         ?"networkbackpack magnet off":"networkbackpack magnet on");
      }).bounds(leftPos+187,topPos+128,77,17).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("WHITE/BLACK"),b->{
       var module=menu.getSlot(0).getItem();
       var tag=module.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
          net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
       command(tag.getBooleanOr("xsx_v176_magnet_whitelist",false)
         ?"networkbackpack magnet blacklist":"networkbackpack magnet whitelist");
      }).bounds(leftPos+187,topPos+149,77,17).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("EDIT FILTERS"),b->{
       filterEditor=!filterEditor;
       searchBox.setEditable(!filterEditor);
       filterPage=0;
       selectedFilter=-1;
       command("networkbackpack filters");
       if(!filterEditor&&autoFocus)setFocused(searchBox);
      }).bounds(leftPos+187,topPos+170,77,17).build());
  if(autoFocus)setFocused(searchBox);
 }
 private static void command''')
patch(screen,'''  if((button==0||button==1)&&x>=8&&x<170&&y>=38&&y<128){''',
'''  if(filterEditor&&selectedFilter>=0&&button==0
       &&x>=8&&x<170&&y>=139&&y<216){
   int col=(x-8)/18, row=(y-139)/18;
   if(col<9&&(row<3||(row==3&&y>=197))){
    int slot=row==3?col:9+row*9+col;
    if(!menu.getSlot(54+(row==3?27+col:row*9+col)).getItem().isEmpty()){
     command("networkbackpack setfilter "+selectedFilter+" "+slot);
     return true;
    }
   }
  }
  if((button==0||button==1)&&x>=8&&x<170&&y>=38&&y<128){''')
patch(screen,'''    if(!menu.getSlot(4+entry).getItem().isEmpty()){
     command("networkbackpack take "+entry+" "+(button==1?1:64));
     return true;
    }''',
'''    if(filterEditor){
     selectedFilter=filterPage*45+entry;
     if(selectedFilter>=54){selectedFilter=-1;return true;}
     if(button==1)command("networkbackpack clearfilter "+selectedFilter);
     return true;
    }
    if(!menu.getSlot(4+entry).getItem().isEmpty()){
     command("networkbackpack take "+entry+" "+(button==1?1:64));
     return true;
    }''')
patch(screen,'''  for(int index=0;index<45;index++){
   var preview=menu.getSlot(index+4).getItem();''',
'''  for(int index=0;index<45&&!filterEditor;index++){
   var preview=menu.getSlot(index+4).getItem();''')
patch(screen,'''  g.text(font,"MODULES",187,11,0xffa7d9f0);''',
'''  g.text(font,filterEditor?"MAGNET FILTER (select a slot, then an inventory item)":
      "STORED ITEMS",8,31,0xffa7d9f0);
  if(filterEditor&&selectedFilter>=0)
   g.text(font,"Filter #"+(selectedFilter+1)+" selected",7,128,0xffa6efab);
  g.text(font,"MODULES",187,11,0xffa7d9f0);''')
# When switching page the client and server must track the same 45-slot filter page.
patch(screen,'''Component.literal("<"),b->command("networkbackpack previous"))''',
'''Component.literal("<"),b->{
       command("networkbackpack previous");
       if(filterEditor)filterPage=Math.max(0,filterPage-1);
      })''')
patch(screen,'''Component.literal(">"),b->command("networkbackpack next"))''',
'''Component.literal(">"),b->{
       command("networkbackpack next");
       if(filterEditor)filterPage=Math.min(1,filterPage+1);
      })''')
patch(screen,'''  g.fill(sx-2,sy-2,sx+SIDE_W,sy+116,0xff4b829d);
  g.fill(sx,sy,sx+SIDE_W-2,sy+114,0xff142d3e);''',
'''  g.fill(sx-2,sy-2,sx+SIDE_W,sy+194,0xff4b829d);
  g.fill(sx,sy,sx+SIDE_W-2,sy+192,0xff142d3e);''')
patch(screen,'''       countSort=!countSort;
       command("networkbackpack sort");''',
'''       if(!filterEditor){
        countSort=!countSort;
        command("networkbackpack sort");
       }''')
print("V176_B817_MAGNET_POWER_WHITE_BLACK_AND_54_FILTER_GHOSTS_STAGED")
