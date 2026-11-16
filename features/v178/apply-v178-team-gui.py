#!/usr/bin/env python3
"""Original xSxLabs claim-team screen and low-cost server snapshot.

Apply after ftb-map-gui and after teams. Server always checks team ownership.
The map's Team button opens a separate native screen; no per-frame network IO.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def rep(path,old,new):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,("V178_TEAM_GUI_DRIFT",path.name,old[:90],s.count(old))
 path.write_text(s.replace(old,new,1),encoding="utf-8")
def emit(rel,java):
 p=J/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_TEAM_GUI_DUPLICATE",rel)
 p.write_text(java,encoding="utf-8")

emit("claims/V178TeamSnapshot.java",r'''package dev.obsidiannetwork.claims;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** On-demand, max 16 members, ~600 bytes: no constant network polling. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178TeamSnapshot(String leader,String members) implements CustomPacketPayload {
 public static final Type<V178TeamSnapshot> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claim_team_snapshot"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178TeamSnapshot> CODEC=
   StreamCodec.of((buf,p)->{
     buf.writeUtf(p.leader(),40);buf.writeUtf(p.members(),768);
   },buf->new V178TeamSnapshot(buf.readUtf(40),buf.readUtf(768)));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToClient(TYPE,CODEC);
 }
}
''')

claim=J/"claims/V178Claims.java"
rep(claim,
'''  for(UUID member:members)tell(p,"Member: "+member);
  return 1;
 }''',
'''  for(UUID member:members)tell(p,"Member: "+member);
  // Small bounded view sent only for /xsxchunks team list requests.
  StringBuilder summary=new StringBuilder(16*37);
  for(UUID member:members){
   if(!summary.isEmpty())summary.append(';');
   summary.append(member);
  }
  PacketDistributor.sendToPlayer(p,new V178TeamSnapshot(
     leader.toString(),summary.toString()));
  return 1;
 }''')

emit("client/V178ClaimTeamScreen.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.claims.V178TeamSnapshot;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;
import java.util.regex.Pattern;

/** A native GUI facade over the server-authoritative team commands.
 *  No client-side trust assumptions, only an on-demand ~600-byte snapshot.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178ClaimTeamScreen extends Screen {
 private static final Pattern VALID_PLAYER=Pattern.compile("[A-Za-z0-9_]{3,16}");
 private static final Pattern VALID_UUID=Pattern.compile("[0-9a-fA-F-]{36}");
 private static volatile V178TeamSnapshot snapshot;
 private final Screen parent;
 private EditBox playerInput;
 private String status="Choose an action. Team details are server-owned.";
 public V178ClaimTeamScreen(Screen parent){
   super(Component.literal("xSxLabs | Claim Team"));
   this.parent=parent;
 }
 @SubscribeEvent public static void payload(RegisterClientPayloadHandlersEvent event){
   event.register(V178TeamSnapshot.TYPE,(packet,context)->snapshot=packet);
 }
 private void send(String suffix){
   Minecraft mc=Minecraft.getInstance();
   if(mc.player==null||mc.player.connection==null)return;
   mc.player.connection.sendCommand("xsxchunks team "+suffix);
   status="Submitted to server: "+suffix;
   // Preserve order and use the existing bounded, explicit list packet.
   if(!suffix.equals("list"))mc.player.connection.sendCommand("xsxchunks team list");
 }
 private void namedAction(String action){
   if(playerInput==null)return;
   String value=playerInput.getValue().trim();
   if(!VALID_PLAYER.matcher(value).matches()&&
      !(action.equals("kick")&&VALID_UUID.matcher(value).matches())){
     status="Enter a valid player name (or member UUID to kick).";
     return;
   }
   send(action+" "+value);
 }
 @Override protected void init(){
   int x=width/2-120,y=Math.max(38,(height-265)/2);
   snapshot=null;
   playerInput=new EditBox(font,x,y+27,240,20,Component.literal("Player or UUID"));
   playerInput.setMaxLength(36);
   playerInput.setHint(Component.literal("Player name / offline member UUID"));
   addRenderableWidget(playerInput);
   addRenderableWidget(Button.builder(Component.literal("Invite"),
     b->namedAction("invite")).bounds(x,y+53,56,20).build());
   addRenderableWidget(Button.builder(Component.literal("Kick"),
     b->namedAction("kick")).bounds(x+60,y+53,56,20).build());
   addRenderableWidget(Button.builder(Component.literal("Accept"),
     b->send("accept")).bounds(x+120,y+53,56,20).build());
   addRenderableWidget(Button.builder(Component.literal("Leave"),
     b->send("leave")).bounds(x+180,y+53,56,20).build());
   addRenderableWidget(Button.builder(Component.literal("Refresh list"),
     b->send("list")).bounds(x,y+80,112,20).build());
   addRenderableWidget(Button.builder(Component.literal("Back to map"),
     b->onClose()).bounds(x+118,y+80,122,20).build());
   send("list");
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
   super.extractBackground(g,mx,my,delta);
   int x=width/2-120,y=Math.max(38,(height-265)/2);
   g.fill(x-6,y-22,x+247,y+258,0xe70c2230);
   g.text(font,"CHUNK TEAM MANAGEMENT",x,y-15,0xff91e8f8);
   g.text(font,"Player / UUID",x,y+12,0xffe3f4fc);
   g.text(font,status,x,y+108,0xffc5e9dd);
   V178TeamSnapshot data=snapshot;
   if(data==null){
     g.text(font,"Requesting team membership...",x,y+129,0xffefcf8e);
     return;
   }
   g.text(font,"Owner: "+data.leader(),x,y+127,0xff93e8a8);
   if(data.members().isEmpty()){
     g.text(font,"No members in this team.",x,y+142,0xffd6e2ef);
   }else{
     String[] members=data.members().split(";");
     for(int i=0;i<Math.min(16,members.length);i++)
       g.text(font,(i+1)+". "+members[i],x,y+142+i*8,0xffd6e2ef);
   }
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(parent);}
 @Override public boolean isPauseScreen(){return false;}
}
''')

screen=J/"client/V178ClaimsMapScreen.java"
rep(screen,
'''  addRenderableWidget(Button.builder(Component.literal("i"),b->help=!help)
     .bounds(229,5,22,20).build());''',
'''  addRenderableWidget(Button.builder(Component.literal("i"),b->help=!help)
     .bounds(229,5,22,20).build());
  addRenderableWidget(Button.builder(Component.literal("Teams"),
     b->Minecraft.getInstance().setScreen(new V178ClaimTeamScreen(this)))
     .bounds(Math.max(255,width-67),5,63,20).build());''')
for marker in ("claims/V178TeamSnapshot.java","client/V178ClaimTeamScreen.java"):
 assert (J/marker).exists(),marker
print("V178_CLAIM_TEAM_GUI_ON_DEMAND_SERVER_SNAPSHOT_INSTALLED")
