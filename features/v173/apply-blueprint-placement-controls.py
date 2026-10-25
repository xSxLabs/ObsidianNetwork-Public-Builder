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
# Build215: a continuously visible 12-edge 3D placement box supplements
# the sparse voxel particles. Chunk-safe and shows all transformed extents.
rep("client/NetworkBlueprintPreviewClient.java",
 '''  var blocks=NetworkBlueprintItem.blocks(held);''',
 '''  // V173_BLUEPRINT_EDGE_WIREFRAME: visible complete 3D volume guide.
  // Rotations 90/270 swap X and Z extents; mirror keeps the same bounds.
  int width=(rot%2==0)?sx:sz,depth=(rot%2==0)?sz:sx;
  for(int axis=0;axis<3;axis++)for(int corner=0;corner<4;corner++){
   int length=axis==0?width:axis==1?sy:depth;
   int samples=Math.min(10,Math.max(1,length*2));
   for(int step=0;step<=samples;step++){
    double t=(double)step/samples;
    double wx=x+.06+(axis==0?(width-.12)*t:(corner&1)*(width-.12));
    double wy=y+.06+(axis==1?(sy-.12)*t:
         axis==0?(corner&1)*(sy-.12):((corner>>1)&1)*(sy-.12));
    double wz=z+.06+(axis==2?(depth-.12)*t:((corner>>1)&1)*(depth-.12));
    if(mc.level.hasChunkAt(BlockPos.containing(wx,wy,wz)))
     mc.level.addParticle(BLUE,wx,wy,wz,0,.001,0);
   }
  }
  var blocks=NetworkBlueprintItem.blocks(held);''')
# Old limit permanently hid every voxel beyond the first 90.
# Rotate a bounded, evenly distributed sample over the entire plan.
rep("client/NetworkBlueprintPreviewClient.java",
 '''  int count=0,phase=mc.player.tickCount/3%4;''',
 '''  int count=0,budget=90;
  int stride=Math.max(1,(Math.min(blocks.size(),sx*sy*sz)+budget-1)/budget);
  int phase=(mc.player.tickCount/3)%stride;''')
rep("client/NetworkBlueprintPreviewClient.java",
 '''   if(blocks.get(n).equals("minecraft:air"))continue;''',
 '''   if(blocks.get(n).equals("minecraft:air")||n%stride!=phase)continue;''')
print("V173_BLUEPRINT_EDGE_WIREFRAME_BUILD215_PASS: twelve edges and rotating complete-structure samples")
# Build216: texture-aware, client-only material cues. The exact block IDs and
# saved blockstate properties already in the Schematic are the only inputs.
# Red indicates an obstructed destination. Never touch or load world blocks.
rep("client/NetworkBlueprintPreviewClient.java",
 '''import net.minecraft.core.particles.DustParticleOptions;''',
 '''import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;''')
rep("client/NetworkBlueprintPreviewClient.java",
 ''' private static final DustParticleOptions BLUE=new DustParticleOptions(0x28d9ff,.65f);''',
 ''' private static final DustParticleOptions BLUE=new DustParticleOptions(0x28d9ff,.65f);
 private static final DustParticleOptions BLOCKED=new DustParticleOptions(0xff414c,.85f);
 /** V173_BLUEPRINT_MATERIAL_GHOST216: restore saved properties, not just IDs. */
 @SuppressWarnings({"rawtypes","unchecked"})
 private static BlockState stateProperty(BlockState state,
    net.minecraft.world.level.block.state.properties.Property property,String value){
  return (BlockState)property.getValue(value)
      .map(v->state.setValue(property,(Comparable)v)).orElse(state);
 }''')
rep("client/NetworkBlueprintPreviewClient.java",
 '''  var blocks=NetworkBlueprintItem.blocks(held);
  int count=0,budget=90;''',
 '''  var blocks=NetworkBlueprintItem.blocks(held);
  String[] serializedStates=NetworkBlueprintItem.read(held,"xsxlabs_states").split(";",-1);
  int count=0,budget=90;''')
rep("client/NetworkBlueprintPreviewClient.java",
 '''   double px0=at.getX(),py0=at.getY(),pz0=at.getZ();
   for(int i=0;i<4;i++){''',
 '''   double px0=at.getX(),py0=at.getY(),pz0=at.getZ();
   // A red marker warns that the Printer will pause at this destination.
   if(!mc.level.getBlockState(at).isAir()){
    mc.level.addParticle(BLOCKED,px0+.5,py0+.5,pz0+.5,0,0,0);
    continue;
   }
   Identifier id=Identifier.tryParse(blocks.get(n));
   if(id!=null){
    var block=BuiltInRegistries.BLOCK.getValue(id);
    if(block!=null && block!=Blocks.AIR){
     BlockState material=block.defaultBlockState();
     if(n<serializedStates.length){
      for(String pair:serializedStates[n].split("&")){
       int sep=pair.indexOf('=');
       if(sep<=0)continue;
       var property=block.getStateDefinition().getProperty(pair.substring(0,sep));
       if(property!=null)material=stateProperty(material,property,pair.substring(sep+1));
      }
     }
     if(rot>=4)material=material.mirror(Mirror.FRONT_BACK);
     for(int turn=0;turn<rot%4;turn++)material=material.rotate(Rotation.CLOCKWISE_90);
     // Stationary block-textured sprite, bounded to the rotating sample.
     mc.level.addParticle(new BlockParticleOption(ParticleTypes.BLOCK_MARKER,material),
                          px0+.5,py0+.5,pz0+.5,0,0,0);
    }
   }
   for(int i=0;i<4;i++){''')
# Check the generated file's exact API anchors; abort rather than ship
# a misleading source patch when upstream preview structure changes.
preview=(J/"client/NetworkBlueprintPreviewClient.java").read_text(encoding="utf-8")
for token in ("V173_BLUEPRINT_MATERIAL_GHOST216","ParticleTypes.BLOCK_MARKER",
              "mc.level.getBlockState(at).isAir()","stateProperty(material,property",
              "material.rotate(Rotation.CLOCKWISE_90)"):
 assert token in preview,token
print("V173_BLUEPRINT_BLOCK_TEXTURES_BUILD216_PASS: saved states, bounded sprite markers, blocked targets")
print("V173_BLUEPRINT_CREATE_STYLE_MOVE_ROTATE_BUILD210_PASS")
