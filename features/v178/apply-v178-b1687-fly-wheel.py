#!/usr/bin/env python3
"""B1687 JARVIS Action Wheel: switch actual installed Power Armor FlyModule ON/OFF.
Server-authoritative, persistent armor component flag, explicit actionbar,
and suit flight runtime permissions still decide whether flight is possible.
Runs AFTER v177 jarvis voice/hud actions and original PowerArmorRuntime.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf8")
 assert s.count(old)==1,("B1687_FLY_WHEEL_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf8")
def emit(rel,src):
 p=J/rel;assert not p.exists(),("B1687_FLY_DUPLICATE",rel)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(src,encoding="utf8")
# Wrap the existing unmodified flight-card inspection. All legacy modules
# and their check paths use the exact same pre-existing logic; only the
# flight card can be overridden with an explicit persisted disabled flag.
runtime=J/"powerarmor/PowerArmorRuntime.java"
s=runtime.read_text(encoding="utf8")
matches=list(re.finditer(r'(?P<prefix>public\s+static\s+boolean\s+)hasCard\s*\((?P<args>[^)]*)\)\s*\{',s))
assert len(matches)==1,("B1687_EXPECT_ONE_HAS_CARD_METHOD",len(matches))
m=matches[0];args=m.group("args")
pieces=args.split(",")
assert len(pieces)==2,("B1687_HAS_CARD_SIGNATURE",args)
def param(x):
 x=x.strip().split()
 assert len(x)>=2,("B1687_HAS_CARD_ARGUMENT",x)
 return x[-1]
player,module=map(param,pieces)
replacement=f'''public static boolean hasCard({args}){{
  if("flight".equals({module})&&V178FlyModuleSwitch.disabled({player}))return false;
  return hasCardWithoutFlySwitch({player},{module});
 }}
 public static boolean hasCardWithoutFlySwitch({args}){{'''
s=s[:m.start()]+replacement+s[m.end():]
runtime.write_text(s,encoding="utf8")

# Existing PowerArmorCommands root command already contains the Attack toggle.
commands=J/"powerarmor/PowerArmorCommands.java"
s=commands.read_text(encoding="utf8")
needle='   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException()))));'
assert s.count(needle)==1,("B1687_COMMAND_ANCHOR_DRIFT",s.count(needle))
s=s.replace(needle,
'''   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException())))
   .then(Commands.literal("flymodule").executes(c->V178FlyModuleSwitch.toggle(c.getSource().getPlayerOrException()))));''',1)
commands.write_text(s,encoding="utf8")

emit("powerarmor/V178FlyModuleSwitch.java",r'''package dev.obsidiannetwork.powerarmor;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
/** No client privilege escalation. The existing armor flight runtime still
 * checks installed card, FE and suit; this class supplies only an OFF gate.
 */
public final class V178FlyModuleSwitch{
 private V178FlyModuleSwitch(){}
 public static final String DISABLED="xsxlabs_flight_off";
 private static List<String> tokens(String s){
  return new ArrayList<>(s==null||s.isEmpty()?List.of():Arrays.asList(s.split(",")));
 }
 public static boolean disabled(Player p){
  if(p==null)return false;
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  if(chest.isEmpty())return false;
  String raw=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return tokens(raw).contains(DISABLED);
 }
 private static void notice(ServerPlayer p,String message){
  p.sendOverlayMessage(Component.literal(message));
 }
 public static int toggle(ServerPlayer p){
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCardWithoutFlySwitch(p,"flight")){
   notice(p,"FlyModule unavailable: install the flight upgrade in a complete suit.");
   return 0;
  }
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  var list=tokens(chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get()));
  boolean turnOn=list.contains(DISABLED);
  list.removeIf(DISABLED::equals);
  if(!turnOn)list.add(DISABLED);
  chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",list));
  if(!turnOn&&!p.isCreative()&&!p.isSpectator()){
   p.getAbilities().mayfly=false;
   p.getAbilities().flying=false;
   p.onUpdateAbilities();
  }
  // Turning on does NOT directly grant mayfly. Original runtime restores it
  // only after checking that the suit/card/FE allows flying.
  notice(p,turnOn?"Fly ON - Flight module activated":"Fly OFF - Flight module deactivated");
  return 1;
 }
}
''')

emit("client/V178FlyModuleClient.java",r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.powerarmor.V178FlyModuleSwitch;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import java.util.Arrays;
public final class V178FlyModuleClient {
 private V178FlyModuleClient(){}
 public static boolean available(){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return false;
  int tier=PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<=0)return false;
  for(int i=1;i<PowerArmorRuntime.SLOTS.length;i++)
   if(PowerArmorRuntime.tier(mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)
    return false;
  for(var slot:PowerArmorRuntime.SLOTS){
   ItemStack stack=mc.player.getItemBySlot(slot);
   String raw=stack.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(raw!=null&&Arrays.asList(raw.split(",")).contains("flight"))return true;
  }
  return false;
 }
 public static boolean active(){
  var mc=Minecraft.getInstance();
  return available()&&mc.player!=null&&!V178FlyModuleSwitch.disabled(mc.player);
 }
 public static int[] withFly(int[] wheel){
  if(!available())return wheel;
  int[] extended=java.util.Arrays.copyOf(wheel,wheel.length+1);
  extended[wheel.length]=11;return extended;
 }
 public static void toggleFromWheel(){
  var mc=Minecraft.getInstance();
  if(available()&&mc.player!=null&&mc.player.connection!=null)
    mc.player.connection.sendCommand("powerarmor flymodule");
 }
}
''')
# Original JARVIS actions remain, append module sector on installed-card suits.
wheel="client/NetworkActionWheelClient.java"
patch(wheel,
'''   return V177JarvisClient.withJarvis(base);''',
'''   return V178FlyModuleClient.withFly(V177JarvisClient.withJarvis(base));''')
wheelFile=J/wheel
s=wheelFile.read_text(encoding="utf8")
matcher=re.search(r'private\s+static\s+void\s+activate\(\s*int\s+([A-Za-z_]\w*)\s*\)\s*\{',s)
assert matcher,("B1687_WHEEL_ACTIVATE",)
choice=matcher.group(1)
s=s[:matcher.end()]+f'''
  if({choice}==11){{V178FlyModuleClient.toggleFromWheel();return;}}
'''+s[matcher.end():]
needle='i==10?"JARVIS SETTINGS":ACTIONS[i];'
assert s.count(needle)==1,("B1687_WHEEL_LABEL_ANCHOR",s.count(needle))
s=s.replace(needle,
 'i==10?"JARVIS SETTINGS":i==11?(V178FlyModuleClient.active()?"FLY OFF":"FLY ON"):ACTIONS[i];',1)
wheelFile.write_text(s,encoding="utf8")
assert "FLY OFF" in s and "FLY ON" in s
assert "hasCardWithoutFlySwitch" in runtime.read_text(encoding="utf8")
print("B1687_ACTION_WHEEL_FLY_ON_OFF_SERVER_AUTHORIZED_PERSISTENT_FE_GATED_PASS")
