#!/usr/bin/env python3
"""B1666 xSxLabs Mining Builder operator UI, server-owned redstone control and live cursor.
Executed after the v1.7.8 base, area-map, GUI theme and 3D-model injectors.
No new ticking scans, chunk generation, or client-authoritative mining.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1666_BUILDER_SOURCE_DRIFT",rel,s.count(old),old[:90])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def emit(rel,content):
 p=J/rel
 assert not p.exists(),("B1666_BUILDER_DUPLICATE",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(content,encoding="utf-8")

# Redstone mode and diagnostics are persisted by the block entity.
patch("mining/V178MiningBuilderBE.java",
'''  private int nextOutputSlot=0;''',
'''  private int nextOutputSlot=0;
  // 0 = ignore, 1 = signal needed, 2 = pause on signal.
  private int redstoneMode=0;
  public int redstoneMode(){return redstoneMode;}
  public boolean canOperate(ServerPlayer player){
   return owner==null||owner.equals(player.getUUID());
  }
  public boolean setRedstoneMode(ServerPlayer player,int mode){
   if(!canOperate(player)||mode<0||mode>2)return false;
   if(redstoneMode!=mode){redstoneMode=mode;setChanged();}
   return true;
  }
  public long position(){return cursor;}
  public long total(){return bounds==null?0:bounds.volume();}
  public BlockPos currentTarget(){
   return bounds==null||cursor>=bounds.volume()?null:bounds.at(cursor);
  }
  public int occupiedSlots(){
   int used=0;for(ItemStack item:stacks)if(!item.isEmpty())used++;
   return used;
  }
  public String workState(ServerLevel world){
   if(bounds==null)return "NO SHAPE CARD";
   if(!bounds.dimension().equals(world.dimension().identifier().toString()))return "WRONG DIMENSION";
   if(cursor>=bounds.volume())return "FINISHED";
   if(energy.getAmountAsLong()<ENERGY_PER_BLOCK)return "NO ENERGY";
   boolean signal=world.hasNeighborSignal(worldPosition);
   if(redstoneMode==1&&!signal)return "WAITING FOR REDSTONE";
   if(redstoneMode==2&&signal)return "PAUSED BY REDSTONE";
   BlockPos target=currentTarget();
   if(target==null)return "FINISHED";
   if(!world.hasChunkAt(target))return "CHUNK UNLOADED";
   if(owner==null||!owner.equals(V178Claims.owner(world,target)))return "AREA NOT CLAIMED";
   if(occupiedSlots()>=27)return "OUTPUT MAY BE FULL";
   return "MINING";
  }''')
patch("mining/V178MiningBuilderBE.java",
'''   if(machine.bounds==null)return;
   if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;''',
'''   if(machine.bounds==null)return;
   // Redstone gating precedes world reads and cannot bypass FE/claim checks.
   boolean signal=world.hasNeighborSignal(at);
   if(machine.redstoneMode==1&&!signal)return;
   if(machine.redstoneMode==2&&signal)return;
   if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;''')
patch("mining/V178MiningBuilderBE.java",
'''   out.putInt("xsxMiningOutputSlot",nextOutputSlot);''',
'''   out.putInt("xsxMiningOutputSlot",nextOutputSlot);
   out.putInt("xsxMiningRedstoneMode",redstoneMode);''')
patch("mining/V178MiningBuilderBE.java",
'''   nextOutputSlot=Math.floorMod(in.getIntOr("xsxMiningOutputSlot",0),27);''',
'''   nextOutputSlot=Math.floorMod(in.getIntOr("xsxMiningOutputSlot",0),27);
   redstoneMode=Math.max(0,Math.min(2,in.getIntOr("xsxMiningRedstoneMode",0)));''')
# Existing card actions stay exactly as before; empty-hand right click now opens live GUI.
patch("mining/V178MiningBuilderBlock.java",
'''   server.sendOverlayMessage(Component.literal(be.status()));
   return InteractionResult.SUCCESS;''',
'''   dev.obsidiannetwork.mining.V178MiningBuilderStatus.send(server,be,true);
   return InteractionResult.SUCCESS;''')

emit("mining/V178MiningBuilderStatus.java",r'''package dev.obsidiannetwork.mining;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Only a bounded operator snapshot. The client never controls the mining cursor. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178MiningBuilderStatus(BlockPos pos,boolean open,int mode,
  int energy,long cursor,long total,int used,int targetX,int targetY,int targetZ,
  String state) implements CustomPacketPayload{
 public static final Type<V178MiningBuilderStatus> TYPE=new Type<>(
    Identifier.fromNamespaceAndPath("obsidiannetwork","v178_builder_status"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178MiningBuilderStatus> CODEC=
    StreamCodec.of((buf,p)->{
      buf.writeBlockPos(p.pos);buf.writeBoolean(p.open);buf.writeVarInt(p.mode);
      buf.writeVarInt(p.energy);buf.writeVarLong(p.cursor);buf.writeVarLong(p.total);
      buf.writeVarInt(p.used);buf.writeInt(p.targetX);buf.writeInt(p.targetY);
      buf.writeInt(p.targetZ);buf.writeUtf(p.state,80);
    },buf->new V178MiningBuilderStatus(buf.readBlockPos(),buf.readBoolean(),
      buf.readVarInt(),buf.readVarInt(),buf.readVarLong(),buf.readVarLong(),
      buf.readVarInt(),buf.readInt(),buf.readInt(),buf.readInt(),buf.readUtf(80)));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToClient(TYPE,CODEC);
 }
 public static void send(ServerPlayer player,V178MiningBuilderBE be,boolean open){
   if(!(player.level() instanceof ServerLevel world)||!be.canOperate(player))return;
   BlockPos at=be.currentTarget();
   PacketDistributor.sendToPlayer(player,new V178MiningBuilderStatus(
     be.getBlockPos(),open,be.redstoneMode(),be.energy().getAmountAsInt(),
     be.position(),be.total(),be.occupiedSlots(),
     at==null?0:at.getX(),at==null?0:at.getY(),at==null?0:at.getZ(),
     be.workState(world)));
 }
}
''')
emit("mining/V178MiningBuilderControl.java",r'''package dev.obsidiannetwork.mining;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Server side: mode -1 is read-only poll; only owner may alter settings. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178MiningBuilderControl(BlockPos pos,int mode)
  implements CustomPacketPayload{
 public static final Type<V178MiningBuilderControl> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","v178_builder_control"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178MiningBuilderControl> CODEC=
   StreamCodec.of((buf,p)->{buf.writeBlockPos(p.pos);buf.writeVarInt(p.mode);},
      buf->new V178MiningBuilderControl(buf.readBlockPos(),buf.readVarInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
  e.registrar("1").playToServer(TYPE,CODEC,(msg,ctx)->{
   if(!(ctx.player() instanceof ServerPlayer player))return;
   if(player.distanceToSqr(msg.pos.getX()+.5,msg.pos.getY()+.5,msg.pos.getZ()+.5)>64)return;
   if(!(player.level().getBlockEntity(msg.pos) instanceof V178MiningBuilderBE be))return;
   if(!be.canOperate(player))return;
   if(msg.mode>=0&&!be.setRedstoneMode(player,msg.mode))return;
   V178MiningBuilderStatus.send(player,be,false);
  });
 }
}
''')
emit("client/V178MiningBuilderClient.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.mining.V178MiningBuilderStatus;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;

@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178MiningBuilderClient{
 private V178MiningBuilderClient(){}
 @SubscribeEvent public static void payload(RegisterClientPayloadHandlersEvent event){
  event.register(V178MiningBuilderStatus.TYPE,(packet,context)->{
   Minecraft mc=Minecraft.getInstance();
   if(mc.level==null||mc.player==null)return;
   if(mc.screen instanceof V178MiningBuilderScreen gui && gui.matches(packet.pos())){
    gui.update(packet);
   }else if(packet.open()){
    mc.setScreen(new V178MiningBuilderScreen(packet));
   }
  });
 }
}
''')
emit("client/V178MiningBuilderScreen.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.mining.V178MiningBuilderControl;
import dev.obsidiannetwork.mining.V178MiningBuilderStatus;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;

/** Live read-only diagnostics; only the redstone mode button issues a mutation. */
public final class V178MiningBuilderScreen extends Screen{
 private V178MiningBuilderStatus status;
 private Button modeButton;
 private static final String[] MODES={"IGNORE SIGNAL","REQUIRE SIGNAL","PAUSE ON SIGNAL"};
 public V178MiningBuilderScreen(V178MiningBuilderStatus packet){
  super(Component.literal("xSxLabs | Mining Builder"));status=packet;
 }
 public boolean matches(BlockPos pos){return status.pos().equals(pos);}
 public void update(V178MiningBuilderStatus packet){
  if(!matches(packet.pos()))return;
  boolean changed=status.mode()!=packet.mode();
  status=packet;
  if(changed&&modeButton!=null)modeButton.setMessage(Component.literal(modeText()));
 }
 private String modeText(){return "Redstone: "+MODES[Math.max(0,Math.min(2,status.mode()))];}
 @Override protected void init(){
  int x=width/2-128,y=height/2-91;
  modeButton=Button.builder(Component.literal(modeText()),b->{
   ClientPacketDistributor.sendToServer(new V178MiningBuilderControl(
       status.pos(),(status.mode()+1)%3));
  }).bounds(x+12,y+142,232,20).build();
  addRenderableWidget(modeButton);
  addRenderableWidget(Button.builder(Component.literal("Close"),b->onClose())
    .bounds(x+73,y+170,110,20).build());
 }
 @Override public void tick(){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null){onClose();return;}
  if(mc.player.distanceToSqr(status.pos().getX()+.5,
      status.pos().getY()+.5,status.pos().getZ()+.5)>64){onClose();return;}
  if(mc.level.getGameTime()%10==0)
   ClientPacketDistributor.sendToServer(new V178MiningBuilderControl(status.pos(),-1));
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int x=width/2-128,y=height/2-91;
  V178UiTheme.panel(g,x,y,256,205);
  g.text(font,"MINING BUILDER  /  OPERATIONS",x+12,y+9,V178UiTheme.CYAN);
  g.text(font,"STATUS: "+status.state(),x+12,y+36,
    status.state().equals("MINING")?0xff83eda9:0xffffbe8b);
  int available=Math.max(0,Math.min(2000000,status.energy()));
  g.text(font,"ENERGY   "+available+" / 2000000 FE",x+12,y+52,0xffd2e9f4);
  g.fill(x+12,y+66,x+244,y+73,0xff132b3b);
  g.fill(x+12,y+66,x+12+(int)(232L*available/2000000L),y+73,0xff54d7eb);
  long total=Math.max(0,status.total()),progress=Math.max(0,Math.min(total,status.cursor()));
  int percent=total==0?0:(int)(progress*100/total);
  g.text(font,"PROGRESS "+progress+" / "+total+"  ("+percent+"%)",x+12,y+79,0xffd2e9f4);
  g.fill(x+12,y+91,x+244,y+98,0xff132b3b);
  g.fill(x+12,y+91,x+12+(total==0?0:(int)(232*progress/total)),y+98,0xff79dca9);
  g.text(font,"OUTPUT BUFFER  "+status.used()+" / 27 slots",x+12,y+105,0xffd2e9f4);
  g.text(font,total==0?"POSITION  --":
    "CURRENT X "+status.targetX()+"  Y "+status.targetY()+"  Z "+status.targetZ(),
    x+12,y+121,0xff9fe5f1);
 }
 @Override public boolean isPauseScreen(){return false;}
}
''')
assert "hasNeighborSignal" in (J/"mining/V178MiningBuilderBE.java").read_text()
assert "V178MiningBuilderStatus.send" in (J/"mining/V178MiningBuilderBlock.java").read_text()
print("B1666_MINING_BUILDER_GUI_REDSTONE_POSITION_STATUS_SERVER_AUTHORIZED_PASS")
