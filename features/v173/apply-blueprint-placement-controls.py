#!/usr/bin/env python3
"""Build210: Create-like Blueprint X/Z/Y nudging, rotation, mirroring and visible client guidance."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def add(rel,content):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_text(content,encoding="utf-8")
def rep(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

add("item/BlueprintPlacementPayload.java",r'''package dev.obsidiannetwork.item;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** V173_BLUEPRINT_NUDGE_PACKET: server owns all saved transform changes. */
public record BlueprintPlacementPayload(int action) implements CustomPacketPayload{
 public static final Type<BlueprintPlacementPayload> TYPE=new Type<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","blueprint_nudge"));
 public static final StreamCodec<RegistryFriendlyByteBuf,BlueprintPlacementPayload> CODEC=
  StreamCodec.of((buf,p)->buf.writeVarInt(p.action()),
                 buf->new BlueprintPlacementPayload(buf.readVarInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler{
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToServer(TYPE,CODEC,(payload,context)->{
    if(context.player() instanceof ServerPlayer player)apply(player,payload.action());
   });
  }
 }
 private static void apply(ServerPlayer player,int command){
  if(command<0||command>7||player.isSpectator())return;
  ItemStack stack=player.getMainHandItem();
  if(!stack.is(ObsidianNetwork.NETWORK_BLUEPRINT.get())||
      NetworkBlueprintItem.blocks(stack).isEmpty())return;
  String dim=player.level().dimension().identifier()+"|";
  String target=NetworkBlueprintItem.read(stack,"xsxlabs_anchor");
  int x,y,z;
  if(!target.startsWith(dim)){
   BlockPos p=player.blockPosition().relative(player.getDirection(),3);
   x=p.getX();y=p.getY();z=p.getZ();
  }else{
   String[] parts=target.substring(dim.length()).split("[|]");
   if(parts.length!=3)return;
   try{
    x=Integer.parseInt(parts[0]);y=Integer.parseInt(parts[1]);
    z=Integer.parseInt(parts[2]);
   }catch(NumberFormatException ex){return;}
  }
  switch(command){
   case 0->x--;case 1->x++;
   case 2->z--;case 3->z++;
   case 4->y++;case 5->y--;
  }
  if(command==6||command==7){
   int r=0;
   try{r=Integer.parseInt(NetworkBlueprintItem.read(stack,"xsxlabs_rotation"));}
   catch(NumberFormatException ex){}
   r=(r+8)%8;
   if(command==6)r=r>=4?4+(r+1)%4:(r+1)%4;
   else r=(r+4)%8;
   NetworkBlueprintItem.write(stack,"xsxlabs_rotation",""+r);
  }
  // Keep entire plan inside reasonable build height and vanilla world border.
  if(y<player.level().getMinY()||y>player.level().getMaxY())return;
  if(Math.abs(x)>29999970||Math.abs(z)>29999970)return;
  NetworkBlueprintItem.write(stack,"xsxlabs_anchor",dim+x+"|"+y+"|"+z);
  player.sendOverlayMessage(Component.literal("Blueprint @ "+x+" "+y+" "+z+
   " / Rotation "+NetworkBlueprintItem.read(stack,"xsxlabs_rotation")+" (arrow/page/R/M)"));
 }
}
''')
add("client/BlueprintPlacementKeys.java",r'''package dev.obsidiannetwork.client;
import com.mojang.blaze3d.platform.InputConstants;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.item.BlueprintPlacementPayload;
import dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/** V173_BLUEPRINT_REAL_CONTROLS: arrows X/Z, page up/down Y, R rotate, M mirror. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class BlueprintPlacementKeys {
 private BlueprintPlacementKeys(){}
 private static final int[] KEY_CODES={
  GLFW.GLFW_KEY_LEFT,GLFW.GLFW_KEY_RIGHT,
  GLFW.GLFW_KEY_UP,GLFW.GLFW_KEY_DOWN,
  GLFW.GLFW_KEY_PAGE_UP,GLFW.GLFW_KEY_PAGE_DOWN,
  GLFW.GLFW_KEY_R,GLFW.GLFW_KEY_M};
 private static final String[] LABELS={
  "x_minus","x_plus","z_minus","z_plus",
  "y_plus","y_minus","rotate","mirror"};
 private static final KeyMapping[] KEYS=new KeyMapping[8];
 static{
  for(int i=0;i<8;i++)KEYS[i]=new KeyMapping(
   "key.obsidiannetwork.blueprint_"+LABELS[i],
   InputConstants.Type.KEYSYM,KEY_CODES[i],PowerArmorExitKeyClient.CATEGORY);
 }
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){
  for(KeyMapping key:KEYS)e.register(key);
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  for(int i=0;i<KEYS.length;i++)
   while(KEYS[i].consumeClick()){
    if(mc.player==null||mc.screen!=null||
       !mc.player.getMainHandItem().is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))continue;
    ClientPacketDistributor.sendToServer(new BlueprintPlacementPayload(i));
   }
 }
 @SubscribeEvent public static void hud(RenderGuiEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.screen!=null||
     !mc.player.getMainHandItem().is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))return;
  var g=e.getGuiGraphics();int y=mc.getWindow().getGuiScaledHeight()/2+26;
  g.fill(5,y-3,257,y+25,0xAA061C2C);
  g.text(mc.font,"BLUEPRINT PREVIEW  |  Arrows: X/Z  Page: Y",9,y,0xff58eaff);
  g.text(mc.font,"R: rotate  M: mirror  Right-click: confirm",9,y+12,0xffe8f6f8);
 }
}
''')
# Increase the minimum visible particles per block and avoid 1/4-phase
# invisibility on sparse blueprints (glass/shaders are tested separately).
rep("client/NetworkBlueprintPreviewClient.java",
 '''   if(blocks.get(n).equals("minecraft:air")||n%4!=phase)continue;''',
 '''   if(blocks.get(n).equals("minecraft:air"))continue;''')
rep("client/NetworkBlueprintPreviewClient.java",
 '''   for(int i=0;i<2;i++)mc.level.addParticle(BLUE,px0+.18+(.64*i),py0+.12,pz0+.18+(.64*i),0,.001,0);
   mc.level.addParticle(BLUE,px0+.5,py0+.86,pz0+.5,0,.001,0);''',
 '''   for(int i=0;i<4;i++){
    mc.level.addParticle(BLUE,px0+.12+((i&1)*.76),py0+.12,pz0+.12+(((i>>1)&1)*.76),0,.001,0);
    mc.level.addParticle(BLUE,px0+.12+((i&1)*.76),py0+.88,pz0+.12+(((i>>1)&1)*.76),0,.001,0);
   }''')
print("V173_BLUEPRINT_CREATE_STYLE_MOVE_ROTATE_BUILD210_PASS")
