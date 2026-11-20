#!/usr/bin/env python3
"""B1677 mining-only builder: top-down scan, protected wilderness mining,
native synced Shape Card inventory slot, and live operations screen.
Runs AFTER B1666 builder-control-gui.py. Does not change FE, loot, tick or item
transaction budgets.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf8")
 if s.count(old)!=1:
  def shift(value,delta):
   lines=[]
   for line in value.split("\n"):
    if not line.strip():lines.append(line);continue
    n=len(line)-len(line.lstrip(" "))
    if n+delta<0:return None
    lines.append(" "*(n+delta)+line[n:])
   return "\n".join(lines)
  for d in (-1,1,-2,2,-3,3,-4,4):
   a,b=shift(old,d),shift(new,d)
   if a is not None and s.count(a)==1:old,new=a,b;break
 assert s.count(old)==1,("B1677_MINER_PATCH_DRIFT",rel,old[:110],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf8")
def emit(rel,src):
 p=J/rel;assert not p.exists(),("B1677_MINER_DUPLICATE",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(src,encoding="utf8")

# Traverse every X/Z block of the highest layer BEFORE descending by one Y:
# actual global top-down mining, not one vertical column at a time.
patch("mining/V178MiningShapeCard.java",
'''    long plane=(long)width()*height();
    return new BlockPos(minX+(int)(index%width()),
        minY+(int)((index/width())%height()),
        minZ+(int)(index/plane));''',
'''    long layer=(long)width()*depth();
    return new BlockPos(minX+(int)(index%width()),
        maxY-(int)(index/layer),
        minZ+(int)((index/width())%depth()));''')
# The public claim API already supports wilderness + owner + trusted permissions.
# Do not bypass any claimed area owned by another player.
patch("mining/V178MiningBuilderBE.java",
'''   if(owner==null||!owner.equals(V178Claims.owner(world,target)))return "AREA NOT CLAIMED";''',
'''   if(!V178Claims.mayMachineMine(world,target,owner))return "PROTECTED CLAIM";''')
patch("mining/V178MiningBuilderBE.java",
'''    if(!machine.owner.equals(V178Claims.owner(world,target)))return;''',
'''    if(!V178Claims.mayMachineMine(world,target,machine.owner))return;''')

# Vanilla machine menu slot; the card remains in the SAME BlockEntity 'card'
# field (no duplicate store). 26 other fake chest slots reject both insertion
# and extraction; all 36 real player-inventory slots are native synchronized.
patch("mining/V178MiningBuilderBE.java",
'''  public SimpleEnergyHandler energy(){return energy;}''',
'''  public ItemStack installedCard(){return card;}
  public SimpleEnergyHandler energy(){return energy;}''')

emit("mining/V178MiningBuilderMenu.java",r'''package dev.obsidiannetwork.mining;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Vanilla-synchronized, real drag/drop Shape Card slot backed by the BE.
 * Uses the standard 9x3 menu protocol so no unregistered custom menu types.
 * All unused machine positions are server-disabled, not phantom storage.
 */
public final class V178MiningBuilderMenu extends ChestMenu {
 private final V178MiningBuilderBE machine;
 private final ServerPlayer operator;
 private final BlockPos position;
 public V178MiningBuilderMenu(int id,Inventory inv,V178MiningBuilderBE be,ServerPlayer player){
  super(MenuType.GENERIC_9x3,id,inv,new SimpleContainer(27),3);
  this.machine=be;this.operator=player;this.position=be.getBlockPos();
  SimpleContainer cardStorage=new SimpleContainer(1){
   @Override public ItemStack getItem(int index){return be.installedCard();}
   @Override public void setItem(int index,ItemStack next){
    if(next.isEmpty()){
     if(!be.installedCard().isEmpty())be.removeCard(player);
    }else if(be.installedCard().isEmpty()&&next.getItem() instanceof V178MiningShapeCard)
     be.insertCard(player,next);
    setChanged();
   }
   @Override public ItemStack removeItem(int index,int amount){
    if(amount<=0)return ItemStack.EMPTY;
    return be.removeCard(player);
   }
   @Override public ItemStack removeItemNoUpdate(int index){
    return be.removeCard(player);
   }
   @Override public boolean stillValid(Player other){
    return V178MiningBuilderMenu.this.stillValid(other);
   }
  };
  slots.set(0,new Slot(cardStorage,0,20,27){
   @Override public boolean mayPlace(ItemStack item){
    return be.canOperate(player)&&be.installedCard().isEmpty()
     &&item.getItem() instanceof V178MiningShapeCard
     &&V178MiningShapeCard.read(item)!=null;
   }
   @Override public boolean mayPickup(Player other){
    return other==player&&be.canOperate(player);
   }
   @Override public int getMaxStackSize(){return 1;}
  });
  for(int i=1;i<27;i++){
   final Slot previous=slots.get(i);
   slots.set(i,new Slot(previous.container,i,-100,-100){
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(Player player){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player player){
  return player.isAlive()&&player.level()==machine.getLevel()
    &&player.level().getBlockEntity(position)==machine
    &&player.distanceToSqr(position.getX()+.5,position.getY()+.5,position.getZ()+.5)<=64
    &&(operator==null||operator==player)&&
       (operator==null||machine.canOperate(operator));
 }
 @Override public ItemStack quickMoveStack(Player player,int slot){
  // No implicit rearrangement of BE card or 26 fake slots. Manual drag/drop
  // through native Slot 0 supports insert and extraction without item dupes.
  return ItemStack.EMPTY;
 }
}
''')

# The existing Shift+RMB card removal stays available. Empty RMB opens the
# real menu; RMB while holding a valid card can insert it, then open same GUI.
patch("mining/V178MiningBuilderBlock.java",
'''   dev.obsidiannetwork.mining.V178MiningBuilderStatus.send(server,be,true);
   return InteractionResult.SUCCESS;''',
'''   if(!be.canOperate(server)){
    server.sendOverlayMessage(Component.literal("Mining Builder: owner only"));
    return InteractionResult.FAIL;
   }
   server.openMenu(new net.minecraft.world.SimpleMenuProvider(
       (id,inv,user)->new V178MiningBuilderMenu(id,inv,be,server),
       Component.literal("xSxLabs Mining Builder @"+
           pos.getX()+","+pos.getY()+","+pos.getZ())));
   dev.obsidiannetwork.mining.V178MiningBuilderStatus.send(server,be,false);
   return InteractionResult.SUCCESS;''')
patch("mining/V178MiningBuilderBlock.java",
'''    }else server.sendOverlayMessage(Component.literal("Mining Builder: invalid card or owner"));
    return InteractionResult.SUCCESS;''',
'''    }else server.sendOverlayMessage(Component.literal("Mining Builder: invalid card or owner"));
    if(be.canOperate(server)){
     server.openMenu(new net.minecraft.world.SimpleMenuProvider(
         (id,inv,user)->new V178MiningBuilderMenu(id,inv,be,server),
         Component.literal("xSxLabs Mining Builder @"+
           pos.getX()+","+pos.getY()+","+pos.getZ())));
     dev.obsidiannetwork.mining.V178MiningBuilderStatus.send(server,be,false);
    }
    return InteractionResult.SUCCESS;''')

# Adapt the existing stateless network status consumer to an operations menu
# screen that has actual PlayerInventory + one genuine synchronized card slot.
patch("client/V178MiningBuilderClient.java",
'''   if(mc.screen instanceof V178MiningBuilderScreen gui && gui.matches(packet.pos())){
     gui.update(packet);''',
'''   if(mc.screen instanceof V178MiningBuilderOperationsScreen gui
       && gui.matches(packet.pos())){
     gui.update(packet);
    }else if(mc.screen instanceof V178MiningBuilderScreen gui && gui.matches(packet.pos())){
     gui.update(packet);''')
patch("client/V178MiningBuilderClient.java",
''' import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;''',
''' import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;
 import net.neoforged.neoforge.client.event.ScreenEvent;
 import net.minecraft.client.gui.screens.inventory.ContainerScreen;
 import net.minecraft.world.inventory.ChestMenu;
 import net.minecraft.core.BlockPos;''')
patch("client/V178MiningBuilderClient.java",
'''  @SubscribeEvent public static void payload(RegisterClientPayloadHandlersEvent event){''',
'''  @SubscribeEvent public static void opening(ScreenEvent.Opening event){
   if(event.getNewScreen() instanceof V178MiningBuilderOperationsScreen)return;
   if(!(event.getNewScreen() instanceof ContainerScreen chest))return;
   if(!(chest.getMenu() instanceof ChestMenu menu))return;
   String title=chest.getTitle().getString();
   String prefix="xSxLabs Mining Builder @";
   if(!title.startsWith(prefix))return;
   var mc=Minecraft.getInstance();
   if(mc.player==null)return;
   try{
    String[] xyz=title.substring(prefix.length()).split(",",-1);
    if(xyz.length!=3)return;
    BlockPos pos=new BlockPos(Integer.parseInt(xyz[0]),
      Integer.parseInt(xyz[1]),Integer.parseInt(xyz[2]));
    event.setNewScreen(new V178MiningBuilderOperationsScreen(
        menu,mc.player.getInventory(),chest.getTitle(),pos));
   }catch(NumberFormatException ignored){}
  }
  @SubscribeEvent public static void payload(RegisterClientPayloadHandlersEvent event){''')

emit("client/V178MiningBuilderOperationsScreen.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.mining.V178MiningBuilderControl;
import dev.obsidiannetwork.mining.V178MiningBuilderStatus;
import dev.obsidiannetwork.mining.V178MiningShapeCard;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;

/** Real inventory screen, with one native server-owned slot + operations pane. */
public final class V178MiningBuilderOperationsScreen extends ContainerScreen{
 private final BlockPos machine;
 private V178MiningBuilderStatus status;
 private Button redstone;
 private static final String[] MODES={"IGNORE SIGNAL","REQUIRE SIGNAL","PAUSE ON SIGNAL"};
 public V178MiningBuilderOperationsScreen(ChestMenu menu,Inventory player,Component title,BlockPos pos){
  super(menu,player,title);machine=pos;
  // Standard chest menu slots are on the client as well, but only slot zero
  // is a real machine slot; the other 26 must never be clickable.
  Slot base=menu.slots.get(0);
  menu.slots.set(0,new Slot(base.container,0,20,27){
   @Override public boolean mayPlace(ItemStack stack){
    return stack.getItem() instanceof V178MiningShapeCard;
   }
   @Override public int getMaxStackSize(){return 1;}
  });
  for(int i=1;i<27;i++){
   Slot original=menu.slots.get(i);
   final int id=i;
   menu.slots.set(i,new Slot(original.container,id,-100,-100){
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return false;}
   });
  }
 }
 public boolean matches(BlockPos at){return machine.equals(at);}
 public void update(V178MiningBuilderStatus next){
  if(!matches(next.pos()))return;
  boolean modeChanged=status==null||status.mode()!=next.mode();
  status=next;
  if(modeChanged&&redstone!=null)redstone.setMessage(Component.literal(modeLabel()));
 }
 private String modeLabel(){
  return "Redstone: "+(status==null?"SYNC":MODES[Math.max(0,Math.min(2,status.mode()))]);
 }
 @Override protected void init(){
  super.init();
  leftPos=(width-444)/2;
  int x=leftPos+190,y=topPos;
  redstone=Button.builder(Component.literal(modeLabel()),b->{
   if(status!=null)ClientPacketDistributor.sendToServer(
     new V178MiningBuilderControl(machine,(status.mode()+1)%3));
  }).bounds(x+7,y+125,235,20).build();
  addRenderableWidget(redstone);
 }
 @Override protected void containerTick(){
  super.containerTick();
  var mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null)return;
  if(mc.level.getGameTime()%10==0)
    ClientPacketDistributor.sendToServer(new V178MiningBuilderControl(machine,-1));
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float partial){
  int x=leftPos,y=topPos,h=getImageHeight();
  V178UiTheme.panel(g,x-3,y-4,180,h+8);
  // Player's native inventory and hotbar occupy the bottom 84px.
  g.fill(x+5,y+18,x+171,y+78,0xff102335);
  g.fill(x+18,y+25,x+38,y+47,0xff547e93);
  g.fill(x+19,y+26,x+37,y+46,0xff15283a);
  g.text(font,"SHAPE CARD",x+47,y+31,0xffb5e5ef);
  g.text(font,"Drag a configured card",x+14,y+57,0xff8eacbb);
  g.text(font,"into the real card slot",x+14,y+68,0xff8eacbb);
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?84+(i/9)*18:142);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff35516b);
   g.fill(sx,sy,sx+17,sy+17,0xff1d3246);
  }
  int xx=x+190;
  V178UiTheme.panel(g,xx,y-4,252,h+8);
  g.text(font,"MINING BUILDER // OPS",xx+9,y+9,V178UiTheme.CYAN);
  if(status==null){
   g.text(font,"Synchronizing machine status...",xx+9,y+37,0xffffce86);
   return;
  }
  g.text(font,"STATUS: "+status.state(),xx+9,y+32,
    status.state().equals("MINING")?0xff8fecc2:0xffffbf86);
  int energy=Math.max(0,Math.min(2000000,status.energy()));
  g.text(font,"FE "+energy+" / 2,000,000",xx+9,y+48,0xffc5e8f1);
  g.fill(xx+9,y+62,xx+241,y+68,0xff091923);
  g.fill(xx+9,y+62,xx+9+(int)(232L*energy/2000000L),y+68,0xff59dbed);
  long total=Math.max(0,status.total()),done=Math.min(total,status.cursor());
  int pct=total==0?0:(int)(100*done/total);
  g.text(font,"PROGRESS "+pct+"%  / "+done+" of "+total,xx+9,y+77,0xffc3e8f2);
  g.fill(xx+9,y+91,xx+241,y+97,0xff091923);
  g.fill(xx+9,y+91,xx+9+(total==0?0:(int)(232L*done/total)),y+97,0xff7edfaf);
  g.text(font,"OUTPUT: "+status.used()+" / 27 slots",xx+9,y+105,0xffc1e0eb);
  g.text(font,total==0?"CURRENT BLOCK: --":
   "X "+status.targetX()+" Y "+status.targetY()+" Z "+status.targetZ(),
   xx+9,y+115,0xffb1e7f6);
  g.text(font,"Top-down scan | mining only",xx+9,y+153,0xff8aabba);
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){
  g.text(font,"xSxLabs  MINER",7,6,V178UiTheme.CYAN);
  g.text(font,"INVENTORY",8,71,0xffa6c5d4);
 }
}
''')
for token in ("maxY-(int)","V178Claims.mayMachineMine","V178MiningBuilderMenu",
              "V178MiningBuilderOperationsScreen"):
 assert any(token in p.read_text() for p in [J/"mining/V178MiningShapeCard.java",
  J/"mining/V178MiningBuilderBE.java",J/"mining/V178MiningBuilderBlock.java",
  J/"client/V178MiningBuilderClient.java"]),token
print("B1677_NATIVE_SHAPE_CARD_SLOT_WILDERNESS_PROTECTED_TOP_DOWN_OPS_GUI_PASS")
