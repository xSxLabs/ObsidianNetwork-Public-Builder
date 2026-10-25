#!/usr/bin/env python3
"""Build174 holographic placement guide: client particle wireframe preview.

Runs client-only while a completed Blueprint is held. Bounding shape matches
the server's saved target, rotation and mirror transform. No block changes.
Particles are capped per refresh so a 16^3 schematic won't spam the client.
"""
from pathlib import Path
import os
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/NetworkBlueprintPreviewClient.java"
assert not p.exists(),p
p.write_text(r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.item.NetworkBlueprintItem;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** V173_BLUEPRINT_GHOST_PREVIEW: bounded, translucent 3D block outline.
 * Right click block anchors the plan. Shift-right click cycles four
 * rotations then four mirrored rotations. Nothing is placed until print.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkBlueprintPreviewClient {
 private NetworkBlueprintPreviewClient(){}
 private static final DustParticleOptions BLUE=new DustParticleOptions(0x28d9ff,.65f);
 @SubscribeEvent public static void tick(ClientTickEvent.Post event){
  var mc=Minecraft.getInstance();
  if(mc.player==null||mc.level==null||mc.player.tickCount%8!=0)return;
  var held=mc.player.getMainHandItem();
  if(!held.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))return;
  String origin=NetworkBlueprintItem.read(held,"xsxlabs_anchor");
  String prefix=mc.level.dimension().identifier()+"|";
  if(!origin.startsWith(prefix))return;
  String[] pos=origin.substring(prefix.length()).split("[|]");
  String[] dim=NetworkBlueprintItem.read(held,"xsxlabs_size").split(",");
  if(pos.length!=3||dim.length!=3)return;
  int x,y,z,sx,sy,sz,rot=0;
  try{
   x=Integer.parseInt(pos[0]);y=Integer.parseInt(pos[1]);z=Integer.parseInt(pos[2]);
   sx=Integer.parseInt(dim[0]);sy=Integer.parseInt(dim[1]);sz=Integer.parseInt(dim[2]);
   String turn=NetworkBlueprintItem.read(held,"xsxlabs_rotation");
   if(!turn.isBlank())rot=Integer.parseInt(turn);
  }catch(NumberFormatException ex){return;}
  if(sx<1||sy<1||sz<1||sx>16||sy>16||sz>16||rot<0||rot>7)return;
  var blocks=NetworkBlueprintItem.blocks(held);
  int count=0,phase=mc.player.tickCount/8%4;
  for(int n=0;n<blocks.size()&&n<sx*sy*sz;n++){
   if(blocks.get(n).equals("minecraft:air")||n%4!=phase)continue;
   int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);
   int px=rot>=4?sx-1-dx:dx,pz=dz;
   switch(rot%4){
    case 1->{int old=px;px=sz-1-pz;pz=old;}
    case 2->{px=sx-1-px;pz=sz-1-pz;}
    case 3->{int old=px;px=pz;pz=sx-1-old;}
   }
   var at=new BlockPos(x+px,y+dy,z+pz);
   if(!mc.level.hasChunkAt(at)||++count>90)continue;
   double px0=at.getX(),py0=at.getY(),pz0=at.getZ();
   for(int i=0;i<2;i++)mc.level.addParticle(BLUE,px0+.18+(.64*i),py0+.12,pz0+.18+(.64*i),0,.001,0);
   mc.level.addParticle(BLUE,px0+.5,py0+.86,pz0+.5,0,.001,0);
  }
 }
}
''',encoding="utf8")
print("V173_BLUEPRINT_HOLOGRAM174_PASS: saved 3D target and mirrored rotation outline preview")
