#!/usr/bin/env python3
"""B1189: persistent per-player /xsxlabs chat on|off|status.

Mute ONLY messages originating from our mod's Java call stack, including
PowerArmor exit/entry/follow/turret/Attack and wireless terminal feedback.
Normal vanilla/other-mod chat packets remain untouched. Original B1188
Multitool models/textures and all gameplay code are unchanged.
"""
import json,os
from pathlib import Path
J=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork'
R=Path(os.environ['V1_RESOURCE_ROOT'])
command=J/'powerarmor/V176ChatControl.java'
mixin=J/'mixin/V176ChatMutePacketMixin.java'
assert not command.exists() and not mixin.exists(),('B1189_DUPLICATE_CHAT_FILTER')
command.parent.mkdir(parents=True,exist_ok=True)
mixin.parent.mkdir(parents=True,exist_ok=True)
command.write_text(r'''package dev.obsidiannetwork.powerarmor;

import com.mojang.brigadier.CommandDispatcher;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.network.protocol.game.ClientboundSystemChatPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** Per-player, world-persistent suppression for our mod's own chat and
 * actionbar packets. Never suppress player chat or other mods' output.
 * This never changes armor, weapons, wireless networking or item rendering.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176ChatControl {
 private V176ChatControl(){}
 private static final Map<Path,Set<UUID>> MUTES=new HashMap<>();
 private static final ThreadLocal<Boolean> CONFIRMATION=ThreadLocal.withInitial(()->false);
 private static final StackWalker WALKER=StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE);

 private static Path store(ServerPlayer p) {
  return p.level().getServer().getWorldPath(LevelResource.ROOT)
    .resolve("xsxlabs-muted-chat-players.txt");
 }
 private static Set<UUID> load(Path path) {
  return MUTES.computeIfAbsent(path, key->{
   Set<UUID> result=new HashSet<>();
   if(Files.exists(key)) {
    try {
     for(String line:Files.readAllLines(key,StandardCharsets.UTF_8))
      if(!line.isBlank())result.add(UUID.fromString(line.trim()));
    }catch(IOException|IllegalArgumentException ex){
     org.slf4j.LoggerFactory.getLogger("xSxLabsChat")
       .error("Cannot read persisted chat mute settings {}",key,ex);
    }
   }
   return result;
  });
 }
 public static synchronized boolean muted(ServerPlayer p) {
  return load(store(p)).contains(p.getUUID());
 }
 private static synchronized boolean change(ServerPlayer p, boolean mute) {
  Path path=store(p);
  Set<UUID> changed=new HashSet<>(load(path));
  if(mute)changed.add(p.getUUID());
  else changed.remove(p.getUUID());
  try {
   Files.createDirectories(path.getParent());
   Path tmp=path.resolveSibling(path.getFileName().toString()+".tmp");
   StringBuilder text=new StringBuilder();
   changed.stream().sorted().forEach(id->text.append(id).append('\n'));
   Files.writeString(tmp,text.toString(),StandardCharsets.UTF_8);
   try {
    Files.move(tmp,path,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
   }catch(java.nio.file.AtomicMoveNotSupportedException ignored){
    Files.move(tmp,path,StandardCopyOption.REPLACE_EXISTING);
   }
   MUTES.put(path,changed);
   return true;
  }catch(IOException ex){
   org.slf4j.LoggerFactory.getLogger("xSxLabsChat")
      .error("Cannot persist chat mute settings {}",path,ex);
   return false;
  }
 }
 /** Explicit status confirmation MUST get through even in muted mode. */
 private static void reply(ServerPlayer p,String text) {
  CONFIRMATION.set(true);
  try {p.sendSystemMessage(Component.literal(text));}
  finally {CONFIRMATION.remove();}
 }
 private static int set(ServerPlayer p,boolean on) {
  if(!change(p,!on)){
   reply(p,"[xSxLabs] Chat setting could not be saved; check server log.");
   return 0;
  }
  reply(p,"[xSxLabs] Mod messages: "+(on?"ON":"OFF"));
  return 1;
 }
 private static int status(ServerPlayer p) {
  reply(p,"[xSxLabs] Mod messages: "+(muted(p)?"OFF":"ON"));
  return 1;
 }
 @SubscribeEvent public static void register(RegisterCommandsEvent e) {
  e.getDispatcher().register(Commands.literal("xsxlabs")
    .then(Commands.literal("chat")
      .then(Commands.literal("off").executes(c->set(c.getSource().getPlayerOrException(),false)))
      .then(Commands.literal("on").executes(c->set(c.getSource().getPlayerOrException(),true)))
      .then(Commands.literal("status").executes(c->status(c.getSource().getPlayerOrException())))));
 }
 /** Called only for chat/actionbar network packets. Never block gameplay. */
 public static boolean suppress(ServerPlayer p,Packet<?> packet) {
  if(Boolean.TRUE.equals(CONFIRMATION.get())
      || !(packet instanceof ClientboundSystemChatPacket
           || packet instanceof ClientboundSetActionBarTextPacket)
      || !muted(p))return false;
  // Check the emitting Java call stack, not message wording or packet text.
  // The calling chain must include OUR mod (not this filter itself).
  return WALKER.walk(stream->stream.limit(60).anyMatch(f->{
   String cls=f.getClassName();
   return cls.startsWith("dev.obsidiannetwork.")
       && !cls.equals("dev.obsidiannetwork.powerarmor.V176ChatControl")
       && !cls.equals("dev.obsidiannetwork.mixin.V176ChatMutePacketMixin");
  }));
 }
}
''',encoding='utf-8')
mixin.write_text(r'''package dev.obsidiannetwork.mixin;

import dev.obsidiannetwork.powerarmor.V176ChatControl;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The outgoing mod-origin chat/actionbar is filtered at exactly one common
 * packet boundary; gameplay/data packets and other mods are never canceled.
 */
@Mixin(ServerCommonPacketListenerImpl.class)
public abstract class V176ChatMutePacketMixin {
 @Inject(method="send(Lnet/minecraft/network/protocol/Packet;)V",
         at=@At("HEAD"),cancellable=true,require=1)
 private void xsxlabs$muteOwnModFeedback(Packet<?> packet,CallbackInfo ci) {
  // send(Packet) is DECLARED by ServerCommonPacketListenerImpl, not by
  // its ServerGamePacketListenerImpl subclass; target the real bytecode.
  if((Object)this instanceof ServerGamePacketListenerImpl game
      && game.player!=null && V176ChatControl.suppress(game.player,packet))
   ci.cancel();
 }
}
''',encoding='utf-8')
cfg=R/'obsidiannetwork.mixins.json'
data=json.loads(cfg.read_text(encoding='utf-8'))
assert 'client' in data and isinstance(data['client'],list)
data.setdefault('mixins',[])
assert 'V176ChatMutePacketMixin' not in data['mixins']
data['mixins'].append('V176ChatMutePacketMixin')
cfg.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
# Fail closed: the chat patch must not change gameplay or the confirmed tool.
assert 'V176ChatMutePacketMixin' in cfg.read_text()
assert 'new ClientboundSystemChatPacket' not in command.read_text()
assert all(p.is_file() for p in [
 R/'assets/obsidiannetwork/models/item/multitool.json',
 R/'assets/obsidiannetwork/textures/item/void_reaver_hd.png'])
tool=json.loads((R/'assets/obsidiannetwork/models/item/multitool.json').read_text())
assert len(tool.get('elements',[]))==2318,('B1189_MULTITOOL_FREEZE_B1188_BROKEN',len(tool.get('elements',[])))
print('B1189_PERSISTENT_PER_PLAYER_MOD_CHAT_ACTIONBAR_COMMANDS_AND_B1188_MULTITOOL_FREEZE_PASS')
