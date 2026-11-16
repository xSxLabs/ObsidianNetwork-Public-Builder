#!/usr/bin/env python3
"""v1.7.8 mining builder: loaded-only top-down area selection, server-owned card.
K while holding Mining Shape Card opens map; drag chunk rectangle, set Y range,
press SAVE. Single bounded server-authoritative packet; no generated chunks.
"""
import os, json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def emit(rel,source):
 p=J/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_MINING_MAP_DUPLICATE",rel)
 p.write_text(source,encoding="utf-8")
emit("mining/V178MiningAreaSelection.java",r'''package dev.obsidiannetwork.mining;

import dev.obsidiannetwork.item.NetworkBlueprintItem;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.minecraft.network.chat.Component;

/** Server validates bounds, hand and player distance. Never accesses chunks. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178MiningAreaSelection(int minX,int minY,int minZ,
                                      int maxX,int maxY,int maxZ,boolean offhand)
 implements CustomPacketPayload {
 public static final Type<V178MiningAreaSelection> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","v178_mining_area_selection"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178MiningAreaSelection> CODEC=
   StreamCodec.of((buf,p)->{
     buf.writeVarInt(p.minX);buf.writeVarInt(p.minY);buf.writeVarInt(p.minZ);
     buf.writeVarInt(p.maxX);buf.writeVarInt(p.maxY);buf.writeVarInt(p.maxZ);
     buf.writeBoolean(p.offhand);
   },buf->new V178MiningAreaSelection(buf.readVarInt(),buf.readVarInt(),
      buf.readVarInt(),buf.readVarInt(),buf.readVarInt(),buf.readVarInt(),buf.readBoolean()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void payloads(RegisterPayloadHandlersEvent event){
   event.registrar("1").playToServer(TYPE,CODEC,(packet,context)->{
     if(!(context.player() instanceof ServerPlayer p))return;
     ItemStack card=p.getItemInHand(packet.offhand?InteractionHand.OFF_HAND:InteractionHand.MAIN_HAND);
     if(!(card.getItem() instanceof V178MiningShapeCard))return;
     String dimension=p.level().dimension().identifier().toString();
     V178MiningShapeCard.Bounds b=new V178MiningShapeCard.Bounds(
       dimension,packet.minX(),packet.minY(),packet.minZ(),
       packet.maxX(),packet.maxY(),packet.maxZ());
     if(!V178MiningShapeCard.valid(b))return;
     // Tight player-range limit, including both corners. No chunk reads.
     int px=p.blockPosition().getX(),pz=p.blockPosition().getZ();
     if(Math.abs((long)b.minX()-px)>4096L||Math.abs((long)b.maxX()-px)>4096L
       ||Math.abs((long)b.minZ()-pz)>4096L||Math.abs((long)b.maxZ()-pz)>4096L)return;
     if(b.minY() < -64||b.maxY()>319)return;
     NetworkBlueprintItem.write(card,"xsxlabs_mining_bounds",
       dimension+"|"+b.minX()+"|"+b.minY()+"|"+b.minZ()+"|"+
       b.maxX()+"|"+b.maxY()+"|"+b.maxZ());
     NetworkBlueprintItem.write(card,"xsxlabs_mining_first","");
     p.sendOverlayMessage(Component.literal("Mining Card: saved "+b.width()+"x"+
       b.height()+"x"+b.depth()+" ("+b.volume()+" blocks)"));
   });
 }
}
''')
emit("client/V178MiningAreaScreen.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.mining.V178MiningShapeCard;
import dev.obsidiannetwork.mining.V178MiningAreaSelection;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/** Lightweight loaded-only 25x25 mining area map. No chunk loading or scan
 * in render; cursor and selections live entirely client-side until SAVE.
 */
public final class V178MiningAreaScreen extends Screen {
 private static final int DIAMETER=25;
 private final boolean offhand;
 private int cx=Integer.MIN_VALUE,cz;
 private int minY,maxY;
 private int firstX,firstZ,lastX,lastZ;
 private boolean dragging,selected;
 private int zoom=12;
 public V178MiningAreaScreen(boolean offhand){
   super(Component.literal("xSxLabs | Mining Area Map"));
   this.offhand=offhand;
 }
 public int centerX(){return cx;}
 public int centerZ(){return cz;}
 private int tile(){return Math.min(zoom,Math.max(4,(Math.min(width,height)-104)/DIAMETER));}
 private int left(){return (width-DIAMETER*tile())/2;}
 private int top(){return (height-DIAMETER*tile())/2;}
 private void center(){
   var p=Minecraft.getInstance().player;
   if(p!=null){cx=p.blockPosition().getX()>>4;cz=p.blockPosition().getZ()>>4;}
 }
 private void lower(int step){minY=Math.max(-64,Math.min(maxY,minY+step));}
 private void upper(int step){maxY=Math.min(319,Math.max(minY,maxY+step));}
 @Override protected void init(){
   if(cx==Integer.MIN_VALUE){
     center();
     var p=Minecraft.getInstance().player;
     if(p!=null){
       int y=p.blockPosition().getY();
       minY=Math.max(-64,y-16);maxY=Math.min(319,y+16);
     }
   }
   addRenderableWidget(Button.builder(Component.literal("Center"),b->center())
     .bounds(4,4,53,19).build());
   addRenderableWidget(Button.builder(Component.literal("Low -8"),b->lower(-8))
     .bounds(62,4,53,19).build());
   addRenderableWidget(Button.builder(Component.literal("Low +8"),b->lower(8))
     .bounds(119,4,53,19).build());
   addRenderableWidget(Button.builder(Component.literal("High -8"),b->upper(-8))
     .bounds(176,4,58,19).build());
   addRenderableWidget(Button.builder(Component.literal("High +8"),b->upper(8))
     .bounds(238,4,58,19).build());
   addRenderableWidget(Button.builder(Component.literal("SAVE"),b->saveSelection())
     .bounds(Math.max(302,width-62),4,58,19).build());
 }
 @Override public void tick(){
   var mc=Minecraft.getInstance();
   if(mc.level!=null&&cx!=Integer.MIN_VALUE)
     V178TerrainMap.tick(mc.level,cx,cz);
 }
 private boolean inside(double x,double y){
   return x>=left()&&x<left()+DIAMETER*tile()
       &&y>=top()&&y<top()+DIAMETER*tile();
 }
 private int chunkX(double x){return cx-12+Math.max(0,Math.min(24,((int)x-left())/tile()));}
 private int chunkZ(double y){return cz-12+Math.max(0,Math.min(24,((int)y-top())/tile()));}
 private V178MiningShapeCard.Bounds area(){
   if(!selected||Minecraft.getInstance().level==null)return null;
   int lowX=Math.min(firstX,lastX),highX=Math.max(firstX,lastX);
   int lowZ=Math.min(firstZ,lastZ),highZ=Math.max(firstZ,lastZ);
   return new V178MiningShapeCard.Bounds(
     Minecraft.getInstance().level.dimension().identifier().toString(),
     lowX<<4,minY,lowZ<<4,(highX<<4)+15,maxY,(highZ<<4)+15);
 }
 private void saveSelection(){
   var b=area();
   var mc=Minecraft.getInstance();
   if(b==null||mc.player==null||!V178MiningShapeCard.valid(b))return;
   ClientPacketDistributor.sendToServer(new V178MiningAreaSelection(
      b.minX(),b.minY(),b.minZ(),b.maxX(),b.maxY(),b.maxZ(),offhand));
   mc.setScreen(null);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
   super.extractBackground(g,mx,my,delta);
   int t=tile(),x0=left(),y0=top(),w=DIAMETER*t;
   g.fill(x0-4,y0-5,x0+w+4,y0+w+40,0xea102132);
   var mc=Minecraft.getInstance();
   for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){
     int wx=cx+x-12,wz=cz+z-12;
     int px=x0+x*t,py=y0+z*t;
     V178TerrainMap.draw(mc.level,g,wx,wz,px,py,t);
   }
   if(selected){
     int l=Math.max(cx-12,Math.min(firstX,lastX));
     int r=Math.min(cx+12,Math.max(firstX,lastX));
     int a=Math.max(cz-12,Math.min(firstZ,lastZ));
     int b=Math.min(cz+12,Math.max(firstZ,lastZ));
     if(l<=r&&a<=b){
       int lx=x0+(l-cx+12)*t,rx=x0+(r-cx+13)*t;
       int ty=y0+(a-cz+12)*t,by=y0+(b-cz+13)*t;
       g.fill(lx,ty,rx,by,0x555ddd86);
       g.fill(lx,ty,rx,ty+2,0xffa9ffaf);
       g.fill(lx,by-2,rx,by,0xffa9ffaf);
       g.fill(lx,ty,lx+2,by,0xffa9ffaf);
       g.fill(rx-2,ty,rx,by,0xffa9ffaf);
     }
   }
   if(mc.player!=null){
     int dx=(mc.player.blockPosition().getX()>>4)-cx+12;
     int dz=(mc.player.blockPosition().getZ()>>4)-cz+12;
     if(dx>=0&&dx<DIAMETER&&dz>=0&&dz<DIAMETER){
       int px=x0+dx*t+t/2,py=y0+dz*t+t/2;
       g.fill(px-2,py-2,px+3,py+3,0xffffffff);
     }
   }
   g.text(font,"MINING AREA | "+cx+","+cz+" | Y "+minY+".."+maxY,
     x0,y0-18,0xffa6edff);
   var b=area();
   boolean valid=V178MiningShapeCard.valid(b);
   g.text(font,valid?"Selection "+b.width()+"x"+b.height()+"x"+b.depth()+
         " = "+b.volume()+" blocks (ready to save)":
         selected?"Invalid area: max 512 each axis and 8M blocks":
                  "Left-drag chunks to select a mining rectangle",
     x0,y0+w+6,valid?0xff95efac:0xfff7c882);
   g.text(font,"Arrow keys: pan  Wheel: zoom  Y controls: vertical bounds",
     x0,y0+w+20,0xffc1d4e2);
 }
 @Override public boolean mouseClicked(MouseButtonEvent e,boolean doubleClick){
   if(super.mouseClicked(e,doubleClick))return true;
   if(e.button()!=0||!inside(e.x(),e.y()))return false;
   firstX=lastX=chunkX(e.x());firstZ=lastZ=chunkZ(e.y());
   dragging=true;selected=true;return true;
 }
 @Override public boolean mouseDragged(MouseButtonEvent e,double dx,double dy){
   if(!dragging)return super.mouseDragged(e,dx,dy);
   lastX=chunkX(e.x());lastZ=chunkZ(e.y());return true;
 }
 @Override public boolean mouseReleased(MouseButtonEvent e){
   if(!dragging)return super.mouseReleased(e);
   lastX=chunkX(e.x());lastZ=chunkZ(e.y());
   dragging=false;return true;
 }
 @Override public boolean mouseScrolled(double mx,double my,double h,double v){
   zoom=Math.max(6,Math.min(18,zoom+(v>0?1:v<0?-1:0)));return true;
 }
 @Override public boolean keyPressed(KeyEvent e){
   int k=e.key();
   if(k==GLFW.GLFW_KEY_ESCAPE){Minecraft.getInstance().setScreen(null);return true;}
   if(k==GLFW.GLFW_KEY_LEFT)cx-=4;
   else if(k==GLFW.GLFW_KEY_RIGHT)cx+=4;
   else if(k==GLFW.GLFW_KEY_UP)cz-=4;
   else if(k==GLFW.GLFW_KEY_DOWN)cz+=4;
   else return super.keyPressed(e);
   return true;
 }
 @Override public boolean isPauseScreen(){return false;}
}
''')
emit("client/V178MiningAreaKey.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.mining.V178MiningShapeCard;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.client.KeyMapping;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.lwjgl.glfw.GLFW;

@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178MiningAreaKey {
 private V178MiningAreaKey(){}
 private static final KeyMapping OPEN=new KeyMapping(
   "key.obsidiannetwork.mining_area_map",InputConstants.Type.KEYSYM,
   GLFW.GLFW_KEY_K,KeyMapping.Category.MISC);
 @SubscribeEvent public static void keys(RegisterKeyMappingsEvent e){e.register(OPEN);}
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  while(OPEN.consumeClick()){
   if(mc.player==null||mc.level==null||mc.screen!=null)continue;
   if(mc.player.getMainHandItem().getItem() instanceof V178MiningShapeCard)
    mc.setScreen(new V178MiningAreaScreen(false));
   else if(mc.player.getOffhandItem().getItem() instanceof V178MiningShapeCard)
    mc.setScreen(new V178MiningAreaScreen(true));
  }
 }
}
''')
for lang,text in (("en_us","Mining Area Map"),("de_de","Mining-Bereichskarte")):
 p=R/f"assets/obsidiannetwork/lang/{lang}.json"
 data=json.loads(p.read_text(encoding="utf-8"))
 key="key.obsidiannetwork.mining_area_map"
 assert key not in data,("V178_MINING_MAP_DUPLICATE_LANG",lang)
 data[key]=text
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("V178_MINING_BUILDER_GUI_MAP_LOADED_ONLY_CLIENT_SERVER_VALIDATED_PASS")
