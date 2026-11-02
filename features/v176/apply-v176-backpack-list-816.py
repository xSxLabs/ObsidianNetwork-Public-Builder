#!/usr/bin/env python3
"""B816: stored-item list, live search, sort, autofocus; NO crafting field.

Builds on B810/B811 real 3-cell Source and separate right module panel.
Menu has 45 READ-ONLY virtual listing slots (zero duplicate inventories).
Server handles withdrawal, quick-move deposit and search/sort/page actions.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(path,old,new):
 file=J/path
 text=file.read_text(encoding="utf-8")
 assert text.count(old)==1,("B816_SOURCE_DRIFT",path,text.count(old),old[:100])
 file.write_text(text.replace(old,new,1),encoding="utf-8")

menu="backpack/V176BackpackMenu.java"
patch(menu,''' private static final class Storage extends SimpleContainer {
  private final Source source;
  Storage(Source source){super(54);this.source=source;}''',
''' private static final class Storage extends SimpleContainer {
  private final Source source;
  private String query="";
  private boolean countSort=false;
  private int page=0;
  Storage(Source source){super(54);this.source=source;}
  private java.util.List<V176BackpackCells.Entry> resultEntries(){
   if(!source.valid())return java.util.List.of();
   var result=new java.util.ArrayList<>(V176BackpackCells.entries(source.current()));
   result.removeIf(e->{
    var id=e.descriptor().key().itemId().toString().toLowerCase(java.util.Locale.ROOT);
    return !id.contains(query);
   });
   if(countSort)result.sort(java.util.Comparator
      .comparingLong(V176BackpackCells.Entry::count).reversed()
      .thenComparing(e->e.descriptor().key().itemId().toString()));
   // The default is a stable item-identity sort, not unordered HashMap order.
   else result.sort(java.util.Comparator.comparing(
      e->e.descriptor().key().itemId().toString()));
   return result;
  }
  private V176BackpackCells.Entry viewed(int slot){
   if(slot<4||slot>=49)return null;
   var entries=resultEntries();
   int position=page*45+slot-4;
   return position>=0&&position<entries.size()?entries.get(position):null;
  }
  private boolean search(String value){
   if(!source.valid()||value.length()>48)return false;
   query=value.toLowerCase(java.util.Locale.ROOT);
   page=0;
   return true;
  }
  private boolean sort(){
   if(!source.valid())return false;
   countSort=!countSort;page=0;return true;
  }
  private boolean page(int delta){
   if(!source.valid())return false;
   int last=Math.max(0,(resultEntries().size()-1)/45);
   page=Math.max(0,Math.min(last,page+delta));
   return true;
  }''');
patch(menu,'''   if(slot<0||slot>=4||!source.valid())return ItemStack.EMPTY;
   return V176BackpackCells.slots(source.current()).get(slot).copy();''',
'''   if(slot<0||slot>=54||!source.valid())return ItemStack.EMPTY;
   if(slot<4)return V176BackpackCells.slots(source.current()).get(slot).copy();
   var entry=viewed(slot);
   if(entry==null||!(source instanceof ItemSource item))return ItemStack.EMPTY;
   var world=item.player.level();
   var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(world.registryAccess());
   var preview=codec.recreate(entry.descriptor(),1);
   var tag=preview.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
   tag.putLong("xsx_v176_preview_total",entry.count());
   preview.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.of(tag));
   return preview;''');
/* fix placed-item viewing - need world access in source independent of type */
patch(menu,'''   if(entry==null||!(source instanceof ItemSource item))return ItemStack.EMPTY;
   var world=item.player.level();''',
'''   if(entry==null)return ItemStack.EMPTY;
   var world=source instanceof ItemSource item?item.player.level()
        :((BlockSource)source).player.level();''');
patch(menu,'''  for(int i=0;i<54;i++){
   final int slot=i;
   // The other 50 placeholder slots must be completely inaccessible.
   slots.set(i,new Slot(storage,i,i<4?195:-100,i<4?20+i*24:-100){''',
'''   for(int i=0;i<54;i++){
    final int slot=i;
    // 0..3 = external right-side magnet/cells.
    // 4..48 = real Storage Cell item previews, read-only and NOT copied to inventory.
    // 49..53 = unused. Player inventory starts after the 54 top slots.
   int sx=i<4?195:i<49?8+((i-4)%9)*18:-100;
   int sy=i<4?20+i*24:i<49?38+((i-4)/9)*18:-100;
   slots.set(i,new Slot(storage,i,sx,sy){''');
patch(menu,'''  // A future transaction-aware transfer will implement shift-click; until then
  // fail CLOSED rather than duplicating a filled cell or recursive backpack.
  return ItemStack.EMPTY;''',
'''  if(!(p instanceof ServerPlayer player)||!storage.source.valid()
     ||index<54||index>=slots.size())return ItemStack.EMPTY;
  Slot slot=slots.get(index);
  ItemStack current=slot.getItem();
  if(current.isEmpty()||current.getItem() instanceof NetworkBackpackItem)
   return ItemStack.EMPTY;
  ItemStack updated=storage.source.current().copy();
  V176BackpackCells.Transfer result=V176BackpackCells.insert(
     player.level(),updated,current,current.getCount());
  if(result.accepted()<=0||!storage.source.save(updated))return ItemStack.EMPTY;
  int count=(int)result.accepted();
  ItemStack moved=current.copy();moved.setCount(count);
  current.shrink(count);
  slot.setChanged();
  broadcastChanges();
  return moved;''');
patch(menu,''' public boolean magnetEnabled(){return storage.source.valid()''',
''' public boolean search(ServerPlayer player,String query){
  if(player.containerMenu!=this)return false;
  boolean result=storage.search(query);
  if(result)broadcastChanges();
  return result;
 }
 public boolean sort(ServerPlayer player){
  if(player.containerMenu!=this)return false;
  boolean result=storage.sort();
  if(result)broadcastChanges();
  return result;
 }
 public boolean page(ServerPlayer player,int direction){
  if(player.containerMenu!=this)return false;
  boolean result=storage.page(direction);
  if(result)broadcastChanges();
  return result;
 }
 public boolean withdraw(ServerPlayer player,int index,int wanted){
  if(player.containerMenu!=this||!storage.source.valid()
     ||index<0||index>=45||wanted<=0||wanted>64)return false;
  var entry=storage.viewed(index+4);
  if(entry==null)return false;
  ItemStack candidate=storage.source.current().copy();
  int count=(int)Math.min((long)wanted,entry.count());
  var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(player.level().registryAccess());
  ItemStack output=codec.recreate(entry.descriptor(),count);
  var transferred=V176BackpackCells.extract(player.level(),candidate,entry.descriptor(),count);
  if(transferred.accepted()!=count||!storage.source.save(candidate))return false;
  // After committing removal from actual cells, player inventory insertion
  // or world drop owns the withdrawn stack. No virtual slot can give items.
  if(!player.getInventory().add(output))
   net.minecraft.world.Containers.dropItemStack(player.level(),
       player.getX(),player.getY(),player.getZ(),output);
  broadcastChanges();
  return true;
 }
 public boolean magnetEnabled(){return storage.source.valid()''');
const commands="backpack/V176BackpackCommands.java";
patch(commands,'''import net.minecraft.commands.Commands;''',
'''import net.minecraft.commands.Commands;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;''');
patch(commands,'''    .then(Commands.literal("magnet")''',
'''    .then(Commands.literal("search")
      .then(Commands.literal("clear").executes(ctx->search(ctx.getSource().getPlayerOrException(),"")))
      .then(Commands.argument("query",StringArgumentType.greedyString())
        .executes(ctx->search(ctx.getSource().getPlayerOrException(),
                StringArgumentType.getString(ctx,"query")))))
    .then(Commands.literal("sort").executes(ctx->{
      var player=ctx.getSource().getPlayerOrException();
      return player.containerMenu instanceof V176BackpackMenu bag&&bag.sort(player)?1:0;
    }))
    .then(Commands.literal("next").executes(ctx->page(ctx.getSource().getPlayerOrException(),1)))
    .then(Commands.literal("previous").executes(ctx->page(ctx.getSource().getPlayerOrException(),-1)))
    .then(Commands.literal("take")
      .then(Commands.argument("index",IntegerArgumentType.integer(0,44))
       .then(Commands.argument("amount",IntegerArgumentType.integer(1,64))
        .executes(ctx->{
         var player=ctx.getSource().getPlayerOrException();
         return player.containerMenu instanceof V176BackpackMenu bag
            &&bag.withdraw(player,IntegerArgumentType.getInteger(ctx,"index"),
                                  IntegerArgumentType.getInteger(ctx,"amount"))?1:0;
        }))))
    .then(Commands.literal("magnet")''');
patch(commands,''' private static int change(ServerPlayer p,Boolean enabled,Boolean whitelist){''',
''' private static int search(ServerPlayer p,String term){
  return p.containerMenu instanceof V176BackpackMenu bag&&bag.search(p,term)?1:0;
 }
 private static int page(ServerPlayer p,int delta){
  return p.containerMenu instanceof V176BackpackMenu bag&&bag.page(p,delta)?1:0;
 }
 private static int change(ServerPlayer p,Boolean enabled,Boolean whitelist){''');

# Client receives 54 vanilla ChestMenu slots. Replace their LOCAL locations to
# match server geometry, so item-list and right-side modules line up visually.
screen="client/V176BackpackScreen.java"
patch(screen,''' private static final int SIDE_X=183;''',
''' private static boolean autoFocus=true;
 private net.minecraft.client.gui.components.EditBox searchBox;
 private boolean countSort=false;
 private static final int SIDE_X=183;''');
patch(screen,'''  leftPos=(width-(imageWidth+95))/2;
 }''',
'''  leftPos=(width-(imageWidth+95))/2;
  for(int i=0;i<54;i++){
   var original=this.menu.getSlot(i);
   int sx=i<4?195:i<49?8+((i-4)%9)*18:-100;
   int sy=i<4?20+i*24:i<49?38+((i-4)/9)*18:-100;
   this.menu.slots.set(i,new net.minecraft.world.inventory.Slot(
      original.container,original.getContainerSlot(),sx,sy){
     @Override public boolean mayPlace(net.minecraft.world.item.ItemStack stack){return false;}
     @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return false;}
   });
  }
  searchBox=new net.minecraft.client.gui.components.EditBox(
      font,leftPos+8,topPos+18,92,15,Component.literal("Search"));
  searchBox.setMaxLength(48);
  searchBox.setResponder(value->command(
      value.isBlank()?"networkbackpack search clear":"networkbackpack search "+value));
  addRenderableWidget(searchBox);
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
     Component.literal(autoFocus?"A:ON":"A:OFF"),b->{
       autoFocus=!autoFocus;b.setMessage(Component.literal(autoFocus?"A:ON":"A:OFF"));
       if(autoFocus)setFocused(searchBox);
     }).bounds(leftPos+102,topPos+18,35,15).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
     Component.literal("SORT"),b->{
       countSort=!countSort;
       command("networkbackpack sort");
     }).bounds(leftPos+138,topPos+18,32,15).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("<"),b->command("networkbackpack previous"))
       .bounds(leftPos+123,topPos+127,22,13).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal(">"),b->command("networkbackpack next"))
       .bounds(leftPos+147,topPos+127,22,13).build());
  if(autoFocus)setFocused(searchBox);
 }
 private static void command(String command){
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand(command);
 }
 @Override public boolean mouseClicked(double mx,double my,int button){
  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if((button==0||button==1)&&x>=8&&x<170&&y>=38&&y<128){
   int col=(x-8)/18,row=(y-38)/18;
   if(col<9&&row<5){
    int entry=row*9+col;
    if(!menu.getSlot(4+entry).getItem().isEmpty()){
     command("networkbackpack take "+entry+" "+(button==1?1:64));
     return true;
    }
   }
  }
  return super.mouseClicked(mx,my,button);
 }''');
patch(screen,'''  g.fill(x+7,y+17,x+169,y+119,0xff091b2a);''',
'''  // No crafting grid: all five grid rows display stored items.
  g.fill(x+7,y+36,x+169,y+128,0xff091b2a);
  for(int row=0;row<5;row++)for(int col=0;col<9;col++){
   int sx=x+8+18*col,sy=y+38+18*row;
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff38586b);
   g.fill(sx,sy,sx+17,sy+17,0xff203748);
  }''');
patch(screen,'''  g.text(font,"NETWORK BACKPACK",8,6,0xffa4edff);''',
'''  g.text(font,"NETWORK BACKPACK",8,6,0xffa4edff);
  // The server owns the exact 64-bit amounts stored as preview-only metadata.
  for(int index=0;index<45;index++){
   var preview=menu.getSlot(index+4).getItem();
   if(preview.isEmpty())continue;
   var tag=preview.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
       net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
   long count=tag.getLongOr("xsx_v176_preview_total",0L);
   if(count<=1)continue;
   String label=count>=1000000?count/1000000+"M":
       count>=1000?count/1000+"k":Long.toString(count);
   g.text(font,label,8+(index%9)*18+16-font.width(label),
       38+(index/9)*18+9,0xffeffaff);
  }''');
# Preserve after-modules labels; no craft slots or autocrafting.
assert "crafting" not in (J/screen).read_text(encoding="utf-8").lower().replace("no crafting grid","").replace("crafting terminal","")
print("V176_B816_BACKPACK_REAL_LIST_SEARCH_SORT_AUTOFOCUS_WITHOUT_CRAFTING_STAGED")
