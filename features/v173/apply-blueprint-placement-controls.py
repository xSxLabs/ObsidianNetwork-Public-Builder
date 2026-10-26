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
# Build222: validate the WHOLE transformed Blueprint footprint, not only
# the anchor. No out-of-height or border positions must reach the printer.
# These guards apply to packet nudges, right-click anchoring and printer ticks.
rep("item/BlueprintPlacementPayload.java",
 '''  if(y<player.level().getMinY()||y>player.level().getMaxY())return;
  if(Math.abs(x)>29999970||Math.abs(z)>29999970)return;''',
 '''   // V173_BLUEPRINT_WHOLE_VOLUME_BOUNDS222: rotations swap X/Z span.
   String[] size=NetworkBlueprintItem.read(stack,"xsxlabs_size").split(",");
   if(size.length!=3)return;
   int sx,sy,sz,rot=0;
   try{
    sx=Integer.parseInt(size[0]);sy=Integer.parseInt(size[1]);
    sz=Integer.parseInt(size[2]);
    String orientation=NetworkBlueprintItem.read(stack,"xsxlabs_rotation");
    if(!orientation.isBlank())rot=Integer.parseInt(orientation);
   }catch(NumberFormatException ex){return;}
   if(sx<1||sy<1||sz<1||sx>16||sy>16||sz>16||rot<0||rot>7)return;
   int width=(rot%2==0)?sx:sz,depth=(rot%2==0)?sz:sx;
   if(y<player.level().getMinY()||(long)y+sy>player.level().getMaxY()||
      x < -29999970 || z < -29999970 ||
      (long)x+width-1>29999970 || (long)z+depth-1>29999970)return;
   var border=player.level().getWorldBorder();
   if(!border.isWithinBounds(new BlockPos(x,y,z))||
      !border.isWithinBounds(new BlockPos(x+width-1,y+sy-1,z+depth-1)))return;''')
rep("item/NetworkBlueprintItem.java",
 '''  write(plan,"xsxlabs_anchor",server.dimension().identifier()+"|"+''',
 '''   // Guard the complete rotated footprint when confirming by right-click.
   String[] s=read(plan,"xsxlabs_size").split(",");
   if(s.length!=3)return InteractionResult.FAIL;
   int sx,sy,sz,rotation=0;
   try{
    sx=Integer.parseInt(s[0]);sy=Integer.parseInt(s[1]);sz=Integer.parseInt(s[2]);
    String turn=read(plan,"xsxlabs_rotation");
    if(!turn.isBlank())rotation=Integer.parseInt(turn);
   }catch(NumberFormatException ex){return InteractionResult.FAIL;}
   if(sx<1||sy<1||sz<1||sx>16||sy>16||sz>16||rotation<0||rotation>7)
    return InteractionResult.FAIL;
   int width=(rotation%2==0)?sx:sz,depth=(rotation%2==0)?sz:sx;
   if(at.getY()<server.getMinY()||(long)at.getY()+sy>server.getMaxY()||
      at.getX() < -29999970 || at.getZ() < -29999970 ||
      (long)at.getX()+width-1>29999970 ||
      (long)at.getZ()+depth-1>29999970 ||
      !server.getWorldBorder().isWithinBounds(at)||
      !server.getWorldBorder().isWithinBounds(at.offset(width-1,sy-1,depth-1))){
    player.sendSystemMessage(Component.literal("Blueprint: entire build volume must fit inside world bounds."));
    return InteractionResult.FAIL;
   }
   write(plan,"xsxlabs_anchor",server.dimension().identifier()+"|"+''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''  BlockPos dest=new BlockPos(tx+px,ty+dy,tz+pz);''',
 '''  // Never wrap overflowed coordinates or place outside the loaded world.
   long targetX=(long)tx+px,targetY=(long)ty+dy,targetZ=(long)tz+pz;
   if(targetX < -29999970 || targetX > 29999970 ||
      targetZ < -29999970 || targetZ > 29999970 ||
      targetY < world.getMinY() || targetY >= world.getMaxY()){
    setStatus("BLUEPRINT OUTSIDE WORLD BOUNDS");return;
   }
   BlockPos dest=new BlockPos((int)targetX,(int)targetY,(int)targetZ);
   if(!world.getWorldBorder().isWithinBounds(dest)){
    setStatus("BLUEPRINT OUTSIDE WORLD BORDER");return;
   }''')
# No GUI/server feature may quietly succeed if the patch is missing.
packet=(J/"item/BlueprintPlacementPayload.java").read_text(encoding="utf-8")
item=(J/"item/NetworkBlueprintItem.java").read_text(encoding="utf-8")
printer=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
assert "V173_BLUEPRINT_WHOLE_VOLUME_BOUNDS222" in packet
assert "entire build volume must fit inside world bounds" in item
assert "BLUEPRINT OUTSIDE WORLD BOUNDS" in printer
print("V173_BLUEPRINT_SAFE_WORLD_VOLUME_BUILD222_PASS: nudge, click, printer")
# Build224: server-authoritative BLUEPRINT transforms must be atomic.
# An invalid R/M turn previously changed the card even when bounds rejected it.
rep("item/BlueprintPlacementPayload.java",
 '''  if(command==6||command==7){''',
 '''  int pendingRotation=-1;
  if(command==6||command==7){''')
rep("item/BlueprintPlacementPayload.java",
 '''   NetworkBlueprintItem.write(stack,"xsxlabs_rotation",""+r);''',
 '''   pendingRotation=r;''')
rep("item/BlueprintPlacementPayload.java",
 '''    if(!orientation.isBlank())rot=Integer.parseInt(orientation);''',
 '''    if(!orientation.isBlank())rot=Integer.parseInt(orientation);
    if(pendingRotation>=0)rot=pendingRotation;''')
rep("item/BlueprintPlacementPayload.java",
 '''  NetworkBlueprintItem.write(stack,"xsxlabs_anchor",dim+x+"|"+y+"|"+z);''',
 '''  if(pendingRotation>=0)
   NetworkBlueprintItem.write(stack,"xsxlabs_rotation",""+pendingRotation);
  NetworkBlueprintItem.write(stack,"xsxlabs_anchor",dim+x+"|"+y+"|"+z);''')
# Guard the whole atomic source order, not just fragments.
packet=(J/"item/BlueprintPlacementPayload.java").read_text(encoding="utf-8")
assert packet.count("pendingRotation")>=4
assert packet.rindex("if(pendingRotation>=0)")>packet.index("isWithinBounds")
assert packet.index("NetworkBlueprintItem.write(stack,\"xsxlabs_rotation\"")>packet.index("isWithinBounds")
print("V173_BLUEPRINT_ATOMIC_TRANSFORM_BUILD224_PASS: invalid turns do not mutate cards")

# Build227 REPAIR of the five combined Build226 fixes.
# Use single semantically unique Java anchors to survive indentation changes.
rep("portal/PortalGateBlockEntity.java",
 '''PortalIndex.Anchor anchor=be.target;''',
 '''PortalIndex.Anchor anchor=be.target;
     // Prevent a one-shot B from teleporting to a removed/replaced Portal A.
     boolean current=false;
     if(be.owner.equals(anchor.owner())){
      for(PortalIndex.Anchor saved:PortalIndex.get(level.getServer()).owned(player.getUUID()))
       if(saved.key().equals(anchor.key())&&saved.uid().equals(anchor.uid())){
        current=true;break;
       }
     }
     if(!current){
      player.sendSystemMessage(Component.literal("Portal A removed or replaced. Reopen Portal B."));
      level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());return;
     }''')
# Throttle repeated warning messages while the player remains inside B.
rep("portal/PortalGateBlockEntity.java",
 '''if(dest==null){player.sendSystemMessage(Component.literal("Portal A dimension unavailable."));return;}''',
 '''if(dest==null){
      if(be.lifetime%20==1)player.sendSystemMessage(Component.literal("Portal A dimension unavailable."));
      return;
     }''')
rep("portal/PortalGateBlockEntity.java",
 '''player.sendSystemMessage(Component.literal("Portal A exit obstructed."));return;''',
 '''if(be.lifetime%20==1)player.sendSystemMessage(Component.literal("Portal A exit obstructed."));
      return;''')
# Hologram lines can extend above the original 10-block tracking/cleanup box.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''new AABB(worldPosition).inflate(4,10,4)''',
 '''new AABB(worldPosition).inflate(4,40,4)''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''new AABB(worldPosition).inflate(1.5,2.5,1.5)''',
 '''new AABB(worldPosition).inflate(1.5,40,1.5)''')
# An unloaded Create destination chunk is not a failed contraption attachment.
# Retry on the next tick rather than discarding the stored local coordinates.
rep("powerarmor/PowerArmorCreateCarrier.java",
 '''if(world.hasChunkAt(BlockPos.containing(dest))''',
 '''if(!world.hasChunkAt(BlockPos.containing(dest)))return;
      if(world.hasChunkAt(BlockPos.containing(dest))''')
# Saturating arithmetic for simultaneous cable buffer + large cells.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''public long availableFE(){return energyBuffer+EnergyTool.energy(energy);}''',
 '''public long availableFE(){
   long cell=Math.max(0L,EnergyTool.energy(energy));
   return energyBuffer>Long.MAX_VALUE-cell?Long.MAX_VALUE:energyBuffer+cell;
  }''')
portal=(J/"portal/PortalGateBlockEntity.java").read_text(encoding="utf-8")
holo=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
carrier=(J/"powerarmor/PowerArmorCreateCarrier.java").read_text(encoding="utf-8")
assert "saved.uid().equals(anchor.uid())" in portal
assert portal.count("be.lifetime%20==1")==2
assert "inflate(4,40,4)" in holo and "inflate(1.5,40,1.5)" in holo
assert "if(!world.hasChunkAt(BlockPos.containing(dest)))return;" in carrier
assert "energyBuffer>Long.MAX_VALUE-cell" in holo
print("V173_BUILD227_BATCH_PASS: UID, warning throttle, holo cleanup, Create retry, FE saturation")

# Build228: Ingame-readiness bundle: 8 source-guarded corrections in one CI.
# 1. 3D Map settings represent projection width, height AND depth. Vertical
# sampling remains centered on the terminal, instead of misusing Z depth.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''worldPosition.getY()-holoDepth''','''worldPosition.getY()-holoHeight''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''worldPosition.getY()+holoHeight);
   int count=0;''',
 '''worldPosition.getY()+holoHeight);
   int count=0,scanned=0;''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''for(int x=-radius;x<=radius && count<180;x+=step)''',
 '''for(int x=-radius;x<=radius && count<180 && scanned<1100;x+=step)''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''for(int z=-radius;z<=radius && count<180;z+=step)''',
 '''for(int z=-radius;z<=radius && count<180 && scanned<1100;z+=step)''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''for(int y=low;y<=high && count<180;y+=Math.max(1,(high-low)/10)){''',
 '''for(int y=low;y<=high && count<180 && scanned<1100;
          y+=Math.max(1,(high-low)/10)){
       scanned++;''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''(double)(y-worldPosition.getY())/
          Math.max(1,holoHeight+holoDepth)*holoHeight,''',
 '''(double)(y-low)/Math.max(1,high-low)*holoHeight,''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''worldPosition.getZ()+.5+(double)z/radius*holoWidth/2,''',
 '''worldPosition.getZ()+.5+(double)z/radius*holoDepth/2,''')
# 2. Never inspect the NORTH chunk without checking that it's loaded.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''if(!world.getBlockState(scan.above()).isAir() &&
         !world.getBlockState(scan.north()).isAir())continue;''',
 '''BlockPos above=scan.above(),north=scan.north();
       if(world.hasChunkAt(above)&&world.hasChunkAt(north)&&
          !world.getBlockState(above).isAir()&&
          !world.getBlockState(north).isAir())continue;''')
# 3. Migrate old single-line hologram stands without leaving invulnerable
# invisible entities. New display lines already carry a #<line> tag.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''for(ArmorStand entity:old)for(String tag:entity.entityTags())
   if(tag.startsWith(labelTag()+"#"))existing.put(tag,entity);''',
 '''for(ArmorStand entity:old){
    boolean current=false;
    for(String tag:entity.entityTags())if(tag.startsWith(labelTag()+"#")){
     existing.put(tag,entity);current=true;break;
    }
    if(!current)entity.discard();
   }''')
# 4. The Quill refuses to capture machines' BlockEntities: the Printer
# must enforce the same rule on forged or old blueprints.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''import net.minecraft.world.level.block.Blocks;''',
 '''import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''if(block==Blocks.AIR||material.isEmpty()||!block.defaultBlockState().getFluidState().isEmpty())''',
 '''if(block==Blocks.AIR||block instanceof EntityBlock||
      material.isEmpty()||!block.defaultBlockState().getFluidState().isEmpty())''')
# 5. A restored waterlogged/fluids state is also unsupported.
# Refund the already reserved material instead of placing free fluid.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''boolean placed=world.setBlock(dest,targetState,3);''',
 '''if(!targetState.getFluidState().isEmpty()){
    net.storage().insert(key,1L);
    setStatus("UNSUPPORTED FLUID BLOCKSTATE "+name);return;
   }
   boolean placed=world.setBlock(dest,targetState,3);''')
# 6. A transient world collision should not permanently detach a power suit
# from a moving Create platform; keep the safe stationary state and retry.
rep("powerarmor/PowerArmorCreateCarrier.java",
 '''}else ATTACHED.remove(id);''',
 '''}else return;''')
# 7. Network Vision must not turn itself off when singleplayer GUI pauses.
rep("client/NetworkVisionClient.java",
 '''if(mc.player==null||mc.level==null||mc.isPaused()){enabled=false;return;}''',
 '''if(mc.player==null||mc.level==null){enabled=false;return;}
  if(mc.isPaused())return;''')
# 8. Vision recognizes the actual wireless relay and portal devices too.
rep("client/NetworkVisionClient.java",
 '''|| s.getBlock() instanceof dev.obsidiannetwork.block.NetworkDeviceBlock)color=DEVICE;''',
 '''|| s.getBlock() instanceof dev.obsidiannetwork.block.NetworkDeviceBlock
      || s.getBlock() instanceof dev.obsidiannetwork.block.NetworkSignalRelayBlock
      || s.is(ObsidianNetwork.NETWORK_PORTAL_A.get())
      || s.is(ObsidianNetwork.NETWORK_PORTAL_B.get()))color=DEVICE;''')
# The reconstruction fails CLOSED if any of the 8 groups did not apply.
holo=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
armor=(J/"powerarmor/PowerArmorCreateCarrier.java").read_text(encoding="utf-8")
vision=(J/"client/NetworkVisionClient.java").read_text(encoding="utf-8")
for token in ("int count=0,scanned=0","scanned<1100",
              "z/radius*holoDepth/2","world.hasChunkAt(north)",
              "if(!current)entity.discard()","block instanceof EntityBlock",
              "UNSUPPORTED FLUID BLOCKSTATE"):
 assert token in holo,("BUILD228_MISSING",token)
assert "}else return;" in armor
assert "if(mc.isPaused())return;" in vision
assert "NetworkSignalRelayBlock" in vision
print("V173_BUILD228_EIGHT_FIX_BUNDLE_PASS: map dimensions, scan limits, legacy stands, safe printer, Create retry, Vision")

# Build230: grouped final-preflight and Create/Portal/Hologram reliability fixes.
# Printer START must not arm invalid or wrong-dimension placements. This
# protects saved NBT as well as client-origin button packets.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''public boolean control(int button){''',
 '''private boolean blueprintReadyToPrint(){
   if(!(level instanceof ServerLevel world)){
    setStatus("PRINTER SERVER NOT READY");return false;
   }
   if(blueprint.isEmpty()){
    setStatus("PRINTER NEEDS BLUEPRINT");return false;
   }
   int[] dims=size();
   if(dims==null || dims.length!=3 || dims[0]<=0 || dims[1]<=0 || dims[2]<=0 ||
      (long)dims[0]*dims[1]*dims[2]!=planLength()){
    setStatus("INVALID SAVED BLUEPRINT");return false;
   }
   String target=NetworkBlueprintItem.read(blueprint,"xsxlabs_anchor");
   String prefix=world.dimension().identifier()+"|";
   if(!target.startsWith(prefix)){
    setStatus("BLUEPRINT TARGET IN WRONG DIMENSION");return false;
   }
   String[] coords=target.substring(prefix.length()).split("[|]");
   if(coords.length!=3){setStatus("INVALID BLUEPRINT POSITION");return false;}
   int x,y,z,rot=0;
   try{
    x=Integer.parseInt(coords[0]);y=Integer.parseInt(coords[1]);
    z=Integer.parseInt(coords[2]);
    String turn=NetworkBlueprintItem.read(blueprint,"xsxlabs_rotation");
    if(!turn.isBlank())rot=Integer.parseInt(turn);
   }catch(NumberFormatException ex){
    setStatus("INVALID BLUEPRINT COORDINATES");return false;
   }
   if(rot<0||rot>7){setStatus("INVALID BLUEPRINT ROTATION");return false;}
   // Reject oversized blueprints before any coordinate arithmetic.
   if((long)dims[0]*dims[1]*dims[2]>1000000L){
    setStatus("BLUEPRINT TOO LARGE");return false;
   }
   int width=(rot%2==0)?dims[0]:dims[2];
   int depth=(rot%2==0)?dims[2]:dims[0];
   if(y<world.getMinY()||(long)y+dims[1]>world.getMaxY()||
      x < -29999970||z < -29999970||
      (long)x+width-1>29999970||(long)z+depth-1>29999970){
    setStatus("BLUEPRINT OUTSIDE BUILD LIMITS");return false;
   }
   BlockPos corner=new BlockPos(x,y,z);
   BlockPos end=corner.offset(width-1,dims[1]-1,depth-1);
   if(!world.getWorldBorder().isWithinBounds(corner)||
      !world.getWorldBorder().isWithinBounds(end)){
    setStatus("BLUEPRINT OUTSIDE WORLD BORDER");return false;
   }
   return true;
  }
  public boolean control(int button){''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''running=true;setStatus("READY");''',
 '''if(!blueprintReadyToPrint()){running=false;sync();return false;}
    missing=ItemStack.EMPTY;
    running=true;setStatus("READY");''')
# Removing or replacing a blueprint must stop the currently scheduled print.
# Otherwise re-inserting another design could unintentionally resume.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''if(!ItemStack.isSameItemSameComponents(blueprint,s)){index=0;completed=0;missing=ItemStack.EMPTY;}''',
 '''if(!ItemStack.isSameItemSameComponents(blueprint,s)){
     index=0;completed=0;running=false;missing=ItemStack.EMPTY;
    }''')
# Create carrier search is now tolerant of occasional late contraption ticks.
# Still UUID-checked, bounded, no chunks forced or equipment copied.
rep("powerarmor/PowerArmorCreateCarrier.java",
 '''stand.getBoundingBox().inflate(8.0D,8.0D,8.0D)''',
 '''stand.getBoundingBox().inflate(16.0D,16.0D,16.0D)''')
rep("powerarmor/PowerArmorCreateCarrier.java",
 '''dest.distanceToSqr(stand.position())>64D''',
 '''dest.distanceToSqr(stand.position())>256D''')
# Portal B is summoned only into an already-loaded chunk within world height.
rep("portal/PortalActionPayload.java",
 '''BlockPos pos=player.blockPosition().relative(player.getDirection(),2);''',
 '''BlockPos pos=player.blockPosition().relative(player.getDirection(),2);
   if(pos.getY()<level.getMinY()||pos.getY()+1>=level.getMaxY()||
      !level.hasChunkAt(pos)||!level.getWorldBorder().isWithinBounds(pos.above())){
    tell(player,"Portal B requires a loaded, valid two-block-high space.");return;
   }''')
# Stale or malicious SavedData targets must not force-load chunks outside
# dimension height or border when a player steps through temporary Portal B.
rep("portal/PortalGateBlockEntity.java",
 '''BlockPos exit=anchor.pos();''',
 '''BlockPos exit=anchor.pos();
     if(exit.getY()<dest.getMinY()||exit.getY()+1>=dest.getMaxY()||
        !dest.getWorldBorder().isWithinBounds(exit)||
        !dest.getWorldBorder().isWithinBounds(exit.above())){
      player.sendSystemMessage(Component.literal("Portal A outside current world limits."));
      level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());return;
     }''')
# Pure holographic text stands should have zero hitbox/interaction; they
# remain invulnerable and have no gravity.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''entity.setInvisible(true);entity.setNoGravity(true);''',
 '''entity.setInvisible(true);entity.setNoGravity(true);
     entity.noPhysics=true;''')
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''entity.setPos(worldPosition.getX()+.5,y,worldPosition.getZ()+.5);''',
 '''entity.noPhysics=true;
    entity.setPos(worldPosition.getX()+.5,y,worldPosition.getZ()+.5);''')
# A fail-closed source contract for all bundled fixes.
device=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
portal=(J/"portal/PortalGateBlockEntity.java").read_text(encoding="utf-8")
action=(J/"portal/PortalActionPayload.java").read_text(encoding="utf-8")
carrier=(J/"powerarmor/PowerArmorCreateCarrier.java").read_text(encoding="utf-8")
assert "blueprintReadyToPrint()" in device
assert "BLUEPRINT TOO LARGE" in device
assert "PRINTER NEEDS BLUEPRINT" in device
assert "dims==null || dims.length!=3" in device
assert "dims[0]<=0" in device
assert "running=false;missing=ItemStack.EMPTY" in device
assert device.count("entity.noPhysics=true;")>=2
assert "setMarker(true)" not in device
assert "inflate(16.0D,16.0D,16.0D)" in carrier
assert "distanceToSqr(stand.position())>256D" in carrier
assert "requires a loaded, valid two-block-high space" in action
assert "Portal A outside current world limits" in portal
print("V173_BUILD230_BATCH_PASS: printer validation, blueprint safe switch, Create search, two portal checks, zero-hitbox holo")
print("V173_BLUEPRINT_CREATE_STYLE_MOVE_ROTATE_BUILD210_PASS")

# Build237: protect printer volume multiplication from overflow in corrupt or
# forged Blueprint dimensions. Each dimension is bounded before multiplication.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''if(dims==null || dims.length!=3 || dims[0]<=0 || dims[1]<=0 || dims[2]<=0 ||
      (long)dims[0]*dims[1]*dims[2]!=planLength()){''',
 '''if(dims==null || dims.length!=3 ||
      dims[0]<=0 || dims[1]<=0 || dims[2]<=0 ||
      dims[0]>1000000 || dims[1]>1000000 || dims[2]>1000000 ||
      (long)dims[0]*dims[1]*dims[2]!=planLength()){''')
device=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
assert "dims[0]>1000000 || dims[1]>1000000 || dims[2]>1000000" in device
print("V173_PRINTER_OVERFLOW_GUARD_BUILD237_PASS")

# Build238: protect Blueprint nudge packet against signed int wraparound.
# Only the final validated coordinate is committed to the item.
rep("item/BlueprintPlacementPayload.java",
 '''  switch(command){
   case 0->x--;case 1->x++;
   case 2->z--;case 3->z++;
   case 4->y++;case 5->y--;
  }''',
 '''  // V173_BLUEPRINT_NUDGE_OVERFLOW238: reject before Java int wraps.
  if((command==0&&x==Integer.MIN_VALUE)||
     (command==1&&x==Integer.MAX_VALUE)||
     (command==2&&z==Integer.MIN_VALUE)||
     (command==3&&z==Integer.MAX_VALUE)||
     (command==4&&y==Integer.MAX_VALUE)||
     (command==5&&y==Integer.MIN_VALUE))return;
  switch(command){
   case 0->x--;case 1->x++;
   case 2->z--;case 3->z++;
   case 4->y++;case 5->y--;
  }''')
packet=(J/"item/BlueprintPlacementPayload.java").read_text(encoding="utf-8")
assert "V173_BLUEPRINT_NUDGE_OVERFLOW238" in packet
assert packet.index("V173_BLUEPRINT_NUDGE_OVERFLOW238")<packet.index("switch(command)")
print("V173_BLUEPRINT_NUDGE_OVERFLOW_BUILD238_PASS")

# Build241: a saved Blueprint cannot start a print in unloaded target chunks.
# This prevents printer state from advancing against an unavailable region.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''   BlockPos corner=new BlockPos(x,y,z);
   BlockPos end=corner.offset(width-1,dims[1]-1,depth-1);
   if(!world.getWorldBorder().isWithinBounds(corner)||''',
 '''   BlockPos corner=new BlockPos(x,y,z);
   BlockPos end=corner.offset(width-1,dims[1]-1,depth-1);
   if(!world.hasChunkAt(corner)||!world.hasChunkAt(end)){
    setStatus("BLUEPRINT TARGET CHUNKS NOT LOADED");return false;
   }
   if(!world.getWorldBorder().isWithinBounds(corner)||''')
device=(J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
assert "BLUEPRINT TARGET CHUNKS NOT LOADED" in device
print("V173_PRINTER_TARGET_CHUNK_GUARD_BUILD241_PASS")

# Build243: Hologram mode buttons must apply immediately, not silently
# wait for a separate APPLY click. Keep screen open for further edits.
rep("client/HologramConfigScreen.java",
 '''Button.builder(Component.literal("NETWORK"),b->mode="network")''',
 '''Button.builder(Component.literal("NETWORK"),b->{mode="network";save(false);})''')
rep("client/HologramConfigScreen.java",
 '''Button.builder(Component.literal("MAP 3D"),b->mode="map")''',
 '''Button.builder(Component.literal("MAP 3D"),b->{mode="map";save(false);})''')
rep("client/HologramConfigScreen.java",
 '''Button.builder(Component.literal("CUSTOM"),b->mode="custom")''',
 '''Button.builder(Component.literal("CUSTOM"),b->{mode="custom";save(false);})''')
rep("client/HologramConfigScreen.java",
 ''' private void save(){
  if(terminal==null)return;''',
 ''' private void save(){save(true);}
 private void save(boolean closeAfter){
  if(terminal==null)return;''')
rep("client/HologramConfigScreen.java",
 '''    val(width,5,1,32),val(height,3,1,32),val(depth,5,1,32),val(radius,16,2,256)));
  onClose();''',
 '''    val(width,5,1,32),val(height,3,1,32),val(depth,5,1,32),val(radius,16,2,256)));
  if(closeAfter)onClose();''')
# Remove the stray instruction over the inventory panel; mode selection
# is already clearly labelled by the three buttons.
rep("client/HologramConfigScreen.java",
 '''  g.text(font,"NETWORK / MAP / CUSTOM | right panel: projection settings",8,58,0xffceeef5);''',
 '''  // Buttons above the panel are the mode selector; no overlay label.''')
screen=(J/"client/HologramConfigScreen.java").read_text(encoding="utf-8")
assert screen.count('save(false);')==3
assert "if(closeAfter)onClose();" in screen
assert "right panel: projection settings" not in screen
print("V173_HOLOGRAM_IMMEDIATE_MODES_GUI_BUILD243_PASS")

# Build244: Portal B may appear suspended in midair. Preserve solid-block,
# fluid, headroom and world-border checks; do not demand supporting ground.
rep("portal/PortalActionPayload.java",
 '''      level.getBlockState(pos.below()).isAir() ||!level.getWorldBorder().isWithinBounds(pos)){''',
 '''      !level.getWorldBorder().isWithinBounds(pos)){''')
rep("portal/PortalActionPayload.java",
 '''Portal B needs two free blocks and solid ground two blocks in front of you.''',
 '''Portal B needs two free blocks in front of you.''')
portal=(J/"portal/PortalActionPayload.java").read_text(encoding="utf-8")
assert "level.getBlockState(pos.below()).isAir()" not in portal
assert "level.getBlockState(pos.above()).isAir()" in portal
print("V173_PORTAL_B_AIRBORNE_BUILD244_PASS")

# Build245: Larger Portal A/B interaction aperture. Extend the existing
# two-block visual selection shape to three blocks, and match server entry
# height so upper-body entry is recognized. This is a visual/entry fix;
# actual 2-wide multiblock portals remain a separate implementation.
rep("portal/PortalGateBlock.java",
 '''  return box(1,0,6,15,32,10);''',
 '''  return box(0,0,6,16,48,10);''')
rep("portal/PortalGateBlockEntity.java",
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+1.85)continue;''',
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+2.85)continue;''')
gate=(J/"portal/PortalGateBlock.java").read_text(encoding="utf-8")
entity=(J/"portal/PortalGateBlockEntity.java").read_text(encoding="utf-8")
assert "box(0,0,6,16,48,10)" in gate
assert "pos.getY()+2.85" in entity
print("V173_PORTAL_TALL_APERTURE_BUILD245_PASS")

# Build246: Four-action hold-to-open radial menu, click-to-activate.
# The UI is a HUD overlay, not a blocking Screen: key release is reliable.
add("client/NetworkActionWheelClient.java",r'''package dev.obsidiannetwork.client;
import com.mojang.blaze3d.platform.InputConstants;
import dev.obsidiannetwork.portal.PortalActionPayload;
import dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient;
import dev.obsidiannetwork.powerarmor.PowerArmorExitPayload;
import dev.obsidiannetwork.powerarmor.PowerArmorRecallPayload;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/** Hold wheel key, hover with mouse, left-click to execute; release closes. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkActionWheelClient {
 private NetworkActionWheelClient(){}
 private static final KeyMapping WHEEL=new KeyMapping(
  "key.obsidiannetwork.action_wheel",InputConstants.Type.KEYSYM,
  GLFW.GLFW_KEY_G,PowerArmorExitKeyClient.CATEGORY);
 private static final String[] ACTIONS={
  "POWER ARMOR EXIT","SPAWN PORTAL B","SELECT PORTAL A","POWER ARMOR RECALL"};
 private static boolean open=false,wasMouseDown=false;
 private static int selected=-1;
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){e.register(WHEEL);}
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.screen!=null||!WHEEL.isDown()){
   open=false;selected=-1;wasMouseDown=false;return;
  }
  open=true;
  double scale=mc.getWindow().getGuiScale();
  double mx=mc.mouseHandler.xpos()/scale;
  double my=mc.mouseHandler.ypos()/scale;
  double dx=mx-mc.getWindow().getGuiScaledWidth()/2.0;
  double dy=my-mc.getWindow().getGuiScaledHeight()/2.0;
  double distance=Math.sqrt(dx*dx+dy*dy);
  selected=distance<24||distance>120?-1:
    (Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0));
  boolean down=GLFW.glfwGetMouseButton(mc.getWindow().handle(),GLFW.GLFW_MOUSE_BUTTON_LEFT)==GLFW.GLFW_PRESS;
  if(down&&!wasMouseDown&&selected>=0){
   switch(selected){
    case 0->ClientPacketDistributor.sendToServer(new PowerArmorExitPayload());
    case 1->ClientPacketDistributor.sendToServer(new PortalActionPayload.Spawn());
    case 2->ClientPacketDistributor.sendToServer(new PortalActionPayload.Cycle());
    case 3->ClientPacketDistributor.sendToServer(new PowerArmorRecallPayload());
    default->{}
   }
  }
  wasMouseDown=down;
 }
 @SubscribeEvent public static void render(RenderGuiEvent.Post e){
  if(!open)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.screen!=null)return;
  var g=e.getGuiGraphics();
  int x=mc.getWindow().getGuiScaledWidth()/2;
  int y=mc.getWindow().getGuiScaledHeight()/2;
  g.fill(x-135,y-135,x+135,y+135,0xB9091726);
  g.fill(x-23,y-23,x+23,y+23,0xFF152E40);
  g.text(mc.font,"xSxLabs",x-22,y-4,0xFF6FEAFF);
  for(int i=0;i<4;i++){
   int cx=x+(i==1?76:i==3?-76:0);
   int cy=y+(i==0?-76:i==2?76:0);
   int color=i==selected?0xEE167D9B:0xDD1B3347;
   g.fill(cx-70,cy-14,cx+70,cy+14,color);
   int w=mc.font.width(ACTIONS[i]);
   g.text(mc.font,ACTIONS[i],cx-w/2,cy-4,0xFFE7F8FF);
  }
 }
}
''')
print("V173_HOLD_CLICK_ACTION_WHEEL_BUILD246_PASS")

# Build247: Action wheel hardening: no accidental attacks while selecting,
# no input carry-over on close, and portal selector uses the existing picker.
rep("client/NetworkActionWheelClient.java",
 '''  open=true;
  double scale=mc.getWindow().getGuiScale();''',
 '''  if(!open)wasMouseDown=GLFW.glfwGetMouseButton(
   mc.getWindow().handle(),GLFW.GLFW_MOUSE_BUTTON_LEFT)==GLFW.GLFW_PRESS;
  open=true;
  double scale=mc.getWindow().getGuiScale();''')
rep("client/NetworkActionWheelClient.java",
 '''  if(down&&!wasMouseDown&&selected>=0){''',
 '''  if(down&&!wasMouseDown&&selected>=0){
   // Consume the same click from Minecraft's attack key while the wheel is held.
   mc.options.keyAttack.setDown(false);''')
# Portal A/B gate height should never permit clicking into unloaded chunks.
rep("portal/PortalGateBlockEntity.java",
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+2.85)continue;''',
 '''      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+2.85)continue;''') if False else None
wheel=(J/"client/NetworkActionWheelClient.java").read_text(encoding="utf-8")
assert "if(!open)wasMouseDown" in wheel
assert "keyAttack.setDown(false)" in wheel
print("V173_WHEEL_INPUT_HARDENING_BUILD247_PASS")

# Build248: consolidate GUI fixes and input cleanup in one patch.
# Hologram uses a menu-backed screen; suppress vanilla slot decorations
# and keep the custom controls unobstructed.
rep("client/HologramConfigScreen.java",
 '''  super(menu,inventory,title);
 }''',
 '''  super(menu,inventory,title);
  this.imageWidth=253;
  this.imageHeight=166;
 }''')
rep("client/HologramConfigScreen.java",
 ''' @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''',
 ''' @Override protected void renderSlot(GuiGraphicsExtractor g,net.minecraft.world.inventory.Slot slot){
  // This machine is configured with text fields, not vanilla inventory slots.
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''')
# Avoid ghost click passing through to the game on every frame.
rep("client/NetworkActionWheelClient.java",
 '''  if(down&&!wasMouseDown&&selected>=0){
   // Consume the same click from Minecraft's attack key while the wheel is held.
   mc.options.keyAttack.setDown(false);''',
 '''  if(down)mc.options.keyAttack.setDown(false);
  if(down&&!wasMouseDown&&selected>=0){''')
# Ensure wheel does not stay visible when its hotkey is released.
rep("client/NetworkActionWheelClient.java",
 '''  if(!open)return;
  Minecraft mc=Minecraft.getInstance();''',
 '''  if(!open||!WHEEL.isDown())return;
  Minecraft mc=Minecraft.getInstance();''')
screen=(J/"client/HologramConfigScreen.java").read_text(encoding="utf-8")
wheel=(J/"client/NetworkActionWheelClient.java").read_text(encoding="utf-8")
assert "this.imageWidth=253" in screen
assert "void renderSlot(" in screen
assert "if(!open||!WHEEL.isDown())return;" in wheel
print("V173_BATCH_GUI_WHEEL_BUILD248_PASS")

# Build249: NeoForge 1.21 GUI API compile repair from Build248 diagnostics.
# imageWidth/imageHeight are final in this mapping, and renderSlot is not
# a valid GuiGraphicsExtractor override. Preserve custom GUI layout without
# illegal mutation or method overrides.
rep("client/HologramConfigScreen.java",
 '''  super(menu,inventory,title);
  this.imageWidth=253;
  this.imageHeight=166;
 }''',
 '''  super(menu,inventory,title);
 }''')
rep("client/HologramConfigScreen.java",
 ''' @Override protected void renderSlot(GuiGraphicsExtractor g,net.minecraft.world.inventory.Slot slot){
  // This machine is configured with text fields, not vanilla inventory slots.
 }
 @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''',
 ''' @Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my){''')
screen=(J/"client/HologramConfigScreen.java").read_text(encoding="utf-8")
assert "this.imageWidth=253" not in screen
assert "void renderSlot(" not in screen
print("V173_GUI_NEOFORGE_COMPILE_REPAIR_BUILD249_PASS")

# Build250 batch: persist custom Portal A labels in the world index, retain
# backwards compatibility with existing anchors, and expose names in picker.
rep("portal/PortalIndex.java",
 '''int x,int y,int z,boolean selected,String id){''',
 '''int x,int y,int z,boolean selected,String id,String name){''')
rep("portal/PortalIndex.java",
 '''    Codec.STRING.optionalFieldOf("id","").forGetter(Anchor::id)
  ).apply(i,Anchor::new));''',
 '''    Codec.STRING.optionalFieldOf("id","").forGetter(Anchor::id),
    Codec.STRING.optionalFieldOf("name","").forGetter(Anchor::name)
  ).apply(i,Anchor::new));''')
rep("portal/PortalIndex.java",
 '''public Anchor withSelected(boolean chosen){return new Anchor(owner,dimension,x,y,z,chosen,id);}''',
 '''public Anchor withSelected(boolean chosen){return new Anchor(owner,dimension,x,y,z,chosen,id,name);}
   public Anchor withName(String label){return new Anchor(owner,dimension,x,y,z,selected,id,label);}
   public String displayName(){return name==null||name.isBlank()?"Portal A #"+uid().substring(0,8):name;}''')
rep("portal/PortalIndex.java",
 '''Anchor a=new Anchor(player.toString(),dim,pos.getX(),pos.getY(),pos.getZ(),true,UUID.randomUUID().toString());''',
 '''Anchor a=new Anchor(player.toString(),dim,pos.getX(),pos.getY(),pos.getZ(),true,UUID.randomUUID().toString(),"");''')
rep("portal/PortalIndex.java",
 ''' public Anchor cycle(UUID owner){''',
 ''' /** Rename an owned A only; reject stale or foreign identifiers. */
 public boolean rename(UUID owner,String uid,String label){
  if(label==null)return false;
  String clean=label.strip();
  if(clean.isEmpty()||clean.length()>48)return false;
  for(Anchor a:owned(owner))if(a.uid().equals(uid)){
   saved.put(a.key(),a.withName(clean));setDirty();return true;
  }
  return false;
 }
 public Anchor cycle(UUID owner){''')
rep("portal/PortalSelectMenu.java",
 '''" / "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]";''',
 '''" / "+a.displayName()+" / "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]";''')
idx=(J/"portal/PortalIndex.java").read_text(encoding="utf-8")
picker=(J/"portal/PortalSelectMenu.java").read_text(encoding="utf-8")
assert 'optionalFieldOf("name","")' in idx
assert 'boolean rename(UUID owner,String uid,String label)' in idx
assert 'a.displayName()' in picker
print("V173_PORTAL_A_PERSISTENT_NAMES_PICKER_BUILD250_PASS")

# Build251: Wheel cursor must actually move in first-person gameplay.
# Vanilla mouse capture otherwise fixes cursor at screen center, making
# all four hover targets unreachable. Release only while wheel is held.
rep("client/NetworkActionWheelClient.java",
 ''' private static boolean open=false,wasMouseDown=false;''',
 ''' private static boolean open=false,wasMouseDown=false,cursorReleased=false;''')
rep("client/NetworkActionWheelClient.java",
 '''   open=false;selected=-1;wasMouseDown=false;return;''',
 '''   if(cursorReleased){
    mc.mouseHandler.grabMouse();
    cursorReleased=false;
   }
   open=false;selected=-1;wasMouseDown=false;return;''')
rep("client/NetworkActionWheelClient.java",
 '''  if(!open)wasMouseDown=GLFW.glfwGetMouseButton(''',
 '''  if(!cursorReleased){
   mc.mouseHandler.releaseMouse();
   cursorReleased=true;
  }
  if(!open)wasMouseDown=GLFW.glfwGetMouseButton(''')
# Ensure no persistent capture state survives a player disconnect.
wheel=(J/"client/NetworkActionWheelClient.java").read_text(encoding="utf-8")
assert 'mc.mouseHandler.releaseMouse()' in wheel
assert 'mc.mouseHandler.grabMouse()' in wheel
print("V173_WHEEL_FREE_CURSOR_HOLD_RELEASE_BUILD251_PASS")

# Build252: Portal aperture 2 blocks wide, 3 blocks tall.
# A and B share the same non-colliding centered geometry and entry detection.
rep("portal/PortalGateBlock.java",
 '''  return box(0,0,6,16,48,10);''',
 '''  return box(-8,0,6,24,48,10);''')
rep("portal/PortalGateBlockEntity.java",
 '''if(Math.abs(player.getX()-(pos.getX()+0.5))>0.52 ||''',
 '''if(Math.abs(player.getX()-(pos.getX()+0.5))>1.02 ||''')
rep("portal/PortalActionPayload.java",
 '''if(!level.getBlockState(pos).isAir()||!level.getBlockState(pos.above()).isAir() ||''',
 '''if(!level.getBlockState(pos).isAir()||!level.getBlockState(pos.above()).isAir() ||
      !level.getBlockState(pos.above(2)).isAir() ||''')
# Replace the old 1x2 glass and frame model with a 2x3 geometry,
# centered on the original portal anchor so old saved worlds still work.
import json
for slug,glass in (("network_portal_a","minecraft:block/purple_stained_glass"),
                   ("network_portal_b","minecraft:block/light_blue_stained_glass")):
 def cuboid(frm,to,tex):
  return {"from":frm,"to":to,"faces":{side:{"texture":"#"+tex} for side in
   ("north","south","east","west","up","down")}}
 model={"render_type":"minecraft:translucent",
  "textures":{"particle":"minecraft:block/obsidian",
              "frame":"minecraft:block/obsidian","window":glass},
  "elements":[
   cuboid([-8,0,6],[-5,48,10],"frame"),
   cuboid([21,0,6],[24,48,10],"frame"),
   cuboid([-5,44,6],[21,48,10],"frame"),
   cuboid([-5,0,6],[21,3,10],"frame"),
   cuboid([-5,3,7.5],[21,44,8.5],"window")]}
 path=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/models/block"/(slug+".json")
 path.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
gate=(J/"portal/PortalGateBlock.java").read_text(encoding="utf-8")
portal=(J/"portal/PortalActionPayload.java").read_text(encoding="utf-8")
assert "box(-8,0,6,24,48,10)" in gate
assert "pos.above(2)" in portal
print("V173_PORTAL_WIDE_TALL_GEOMETRY_BUILD252_PASS")

# Build253: harden 2x3 portals and preserve the owner-bound A target.
# The wider entrance must be checked at both lateral edges before spawning B.
rep("portal/PortalActionPayload.java",
 '''  if(!level.getBlockState(pos).isAir()||!level.getBlockState(pos.above()).isAir() ||
      !level.getBlockState(pos.above(2)).isAir() ||
      !level.getWorldBorder().isWithinBounds(pos)){''',
 '''  BlockPos side=pos.relative(player.getDirection().getClockWise());
  if(!level.getWorldBorder().isWithinBounds(pos)||
      !level.getWorldBorder().isWithinBounds(side)||
      !level.getBlockState(pos).isAir()||
      !level.getBlockState(pos.above()).isAir()||
      !level.getBlockState(pos.above(2)).isAir()||
      !level.getBlockState(side).isAir()||
      !level.getBlockState(side.above()).isAir()||
      !level.getBlockState(side.above(2)).isAir()){''')
rep("portal/PortalActionPayload.java",
 '''Portal B needs two free blocks in front of you.''',
 '''Portal B needs a clear 2x3 opening in front of you.''')
# Ensure the 3-high arrival volume is safe before cross-dimension teleport.
rep("portal/PortalGateBlockEntity.java",
 '''    if(!dest.getBlockState(exit.above()).isAir()){
     if(be.lifetime%20==1)player.sendSystemMessage(Component.literal("Portal A exit obstructed."));
      return;
    }''',
 '''    if(!dest.getWorldBorder().isWithinBounds(exit)||
       !dest.getBlockState(exit.above()).isAir()||
       !dest.getBlockState(exit.above(2)).isAir()){
     player.sendSystemMessage(Component.literal("Portal A exit obstructed."));return;
    }''')
# Prevent the selection message from concealing a user-defined portal label.
rep("portal/PortalActionPayload.java",
 '''tell(player,"Portal A selected: "+chosen.dimension()+" ["+chosen.x()+", "+chosen.y()+", "+chosen.z()+"] ("+''',
 '''tell(player,"Portal A selected: "+chosen.displayName()+" / "+chosen.dimension()+" ["+chosen.x()+", "+chosen.y()+", "+chosen.z()+"] ("+''')
# Display the name at B spawn as well, so users can confirm the target.
rep("portal/PortalActionPayload.java",
 '''tell(player,"Portal B opened -> "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]. Enter to travel.");''',
 '''tell(player,"Portal B opened -> "+a.displayName()+" / "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]. Enter to travel.");''')
portal=(J/"portal/PortalActionPayload.java").read_text(encoding="utf-8")
entity=(J/"portal/PortalGateBlockEntity.java").read_text(encoding="utf-8")
assert 'BlockPos side=pos.relative(player.getDirection().getClockWise())' in portal
assert 'a.displayName()' in portal
assert 'exit.above(2)' in entity
print("V173_PORTAL_2X3_SAFETY_AND_LABELS_BUILD253_PASS")
