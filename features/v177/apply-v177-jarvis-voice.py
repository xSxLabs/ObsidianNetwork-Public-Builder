#!/usr/bin/env python3
"""v1.7.7 native client J.A.R.V.I.S. HUD, voice, wheel and settings."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V177_JARVIS_DRIFT",rel,old[:130],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,src):
 p=J/rel;p.parent.mkdir(exist_ok=True,parents=True)
 assert not p.exists(),("V177_DUPLICATE",rel)
 p.write_text(src,encoding="utf-8")

wheel=J/"client/NetworkActionWheelClient.java"
s=wheel.read_text(encoding="utf-8")
old=" private static int[] wheelActions(boolean vision,boolean attack){"
assert s.count(old)==1,("V177_JARVIS_WHEEL_METHOD_DRIFT",s.count(old))
s=s.replace(old,''' private static int[] wheelActions(boolean vision,boolean attack){
  int[] base=xsxBaseWheelActions(vision,attack);
  return V177JarvisClient.withJarvis(base);
 }
 private static int[] xsxBaseWheelActions(boolean vision,boolean attack){''',1)
matcher=re.search(r'private static void activate\(\s*int\s+([A-Za-z_]\w*)\s*\)\s*\{',s)
assert matcher is not None,"V177_WHEEL_ACTIVATE_NOT_FOUND"
choice=matcher.group(1)
s=s[:matcher.end()]+f'''
  // J.A.R.V.I.S. is built into every complete MK1..MK24 suit.
  if({choice}==9){{V177JarvisClient.toggle();return;}}
  if({choice}==10){{Minecraft.getInstance().setScreen(new V177JarvisSettingsScreen());return;}}
  V177JarvisClient.wheelAction({choice});
'''+s[matcher.end():]
label='i==6?"FOLLOW":i==7?"TURRET":i==8?"SLEEP":ACTIONS[i];'
assert s.count(label)==1,("V177_WHEEL_LABEL_DRIFT",s.count(label))
s=s.replace(label,
 'i==6?"FOLLOW":i==7?"TURRET":i==8?"SLEEP":i==9?"J.A.R.V.I.S. "+(V177JarvisClient.enabled()?"ON":"OFF"):i==10?"JARVIS SETTINGS":ACTIONS[i];',1)
ticker=re.search(r'public static void tick\(\s*ClientTickEvent\.Post\s+\w+\s*\)\s*\{',s)
assert ticker is not None,"V177_WHEEL_TICK_NOT_FOUND"
s=s[:ticker.end()]+"\n  V177JarvisClient.tick();"+s[ticker.end():]
wheel.write_text(s,encoding="utf-8")
change("client/PowerArmorBuild98Client.java",
 '''   // V177_INTEGRITY_ABOVE_PASTE (single combined value for four pieces)''',
 '''   V177JarvisClient.draw(event);
   // V177_INTEGRITY_ABOVE_PASTE (single combined value for four pieces)''')

add("client/V177JarvisSettings.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;
import java.util.UUID;
import java.util.Map;
import java.util.LinkedHashMap;

/** Per-player on-disk, client-only settings. No server spam or remote services. */
public final class V177JarvisSettings {
 private V177JarvisSettings(){}
 private static UUID owner;
 private static final Map<String,Boolean> switches=new LinkedHashMap<>();
 public static int radius=32;
 public static boolean german=false;
 public static boolean enabled=true;
 public static int volume=85;
 static {
  for(String key:new String[]{"voice","actions","startup","greeting","sleep",
       "energy","paste","integrity","hostiles","passives","players","bosses",
       "nearest","home","projectile","environment","scan",
       "service","offline","recall","follow","turret","sleep_command",
       "attack_on","attack_off","sleep_begin","sleep_end","exit",
       "flight_on","flight_off","morning","afternoon","evening",
       "energy_50","energy_25","energy_0","paste_57","paste_50",
       "paste_25","paste_1","integrity_50","integrity_25",
       "integrity_1","integrity_0"})
   switches.put(key,true);
 }
 public static boolean on(String key){return switches.getOrDefault(key,true);}
 public static void set(String key,boolean val){switches.put(key,val);save();}
 public static void toggle(String key){set(key,!on(key));}
 public static void setRadius(int value){
  radius=Math.max(8,Math.min(64,Math.round(value/8F)*8));save();
 }
 public static void language(boolean de){german=de;save();}
 public static void setVolume(int value){volume=Math.max(0,Math.min(100,value));save();}
 public static void enabled(boolean on){enabled=on;save();}
 private static Path file(){
  return Minecraft.getInstance().gameDirectory.toPath().resolve("config")
      .resolve("xsxlabs-jarvis-"+(owner==null?"default":owner)+".properties");
 }
 public static void load(UUID uuid){
  if(uuid.equals(owner))return;
  owner=uuid;radius=32;german=false;enabled=true;volume=85;
  for(String key:switches.keySet())switches.put(key,true);
  Properties p=new Properties();
  try(var stream=Files.newInputStream(file())){p.load(stream);}
  catch(java.io.IOException ignored){return;}
  enabled=Boolean.parseBoolean(p.getProperty("enabled","true"));
  german=Boolean.parseBoolean(p.getProperty("german","false"));
  try{volume=Math.max(0,Math.min(100,Integer.parseInt(p.getProperty("volume","85"))));}
  catch(NumberFormatException ignored){volume=85;}
  try{radius=Math.max(8,Math.min(64,((Integer.parseInt(p.getProperty("radius","32"))+4)/8)*8));}
  catch(NumberFormatException ignored){radius=32;}
  for(String key:switches.keySet())
    switches.put(key,Boolean.parseBoolean(p.getProperty(key,"true")));
 }
 public static void save(){
  if(owner==null)return;
  Properties p=new Properties();
  p.setProperty("enabled",String.valueOf(enabled));
  p.setProperty("german",String.valueOf(german));
  p.setProperty("radius",String.valueOf(radius));
  p.setProperty("volume",String.valueOf(volume));
  for(var entry:switches.entrySet())
    p.setProperty(entry.getKey(),String.valueOf(entry.getValue()));
  try{
   Files.createDirectories(file().getParent());
   try(var stream=Files.newOutputStream(file())){p.store(stream,"xSxLabs J.A.R.V.I.S. 1.7.7");}
  }catch(java.io.IOException ignored){}
 }
}
''')
add("client/V177JarvisSettingsScreen.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.components.Button;
import net.minecraft.network.chat.Component;

/** Each JARVIS announcement is selectable; six compact rows per page. */
public final class V177JarvisSettingsScreen extends Screen {
 private int page=0,subpage=0;
 private static final String[][][] FLAGS={
  { // VOICE
   {"voice|Voice assistant","startup|Diagnostics at armor entry","greeting|Greeting at armor entry","service|Assistant ON reply"},
   {"morning|Good morning greeting","afternoon|Good afternoon greeting",
    "evening|Good evening greeting","offline|Assistant OFF reply",
    "exit|Armor exit farewell"}
  },
  { // SCAN
   {"scan|Mob scan summary","hostiles|Detect hostile mobs","passives|Detect passive mobs",
    "players|Detect other players","bosses|Detect bosses"},
   {"nearest|Nearest mob and distance","projectile|Incoming projectile",
    "environment|Cave and visibility warning"}
  },
  { // ALERTS
   {"energy_50|Energy 50%","energy_25|Energy 25%",
    "energy_0|Energy empty","paste_57|NutriPaste 57%","paste_50|NutriPaste 50%"},
   {"paste_25|NutriPaste 25%","paste_1|NutriPaste 1%",
    "integrity_50|Integrity 50%","integrity_25|Integrity 25%",
    "integrity_1|Integrity 1%","integrity_0|Integrity zero"}
  },
  { // MODULES
   {"flight_on|Flight ON","flight_off|Flight OFF",
    "attack_on|Attack ON","attack_off|Attack OFF",
    "sleep_begin|Sleep begins"},
   {"sleep_end|Sleep finishes","sleep_command|Sleep mode command",
    "follow|Follow mode","turret|Turret mode","recall|Armor recall"},
   {"home|Welcome back at home","actions|General action sounds",
    "sleep|General sleep sounds"}
  }
 };
 public V177JarvisSettingsScreen(){super(Component.literal("J.A.R.V.I.S. CONFIGURATION"));}
 private void button(int x,int y,int w,String text,Runnable action){
  addRenderableWidget(Button.builder(Component.literal(text),b->{
   action.run();rebuildWidgets();
  }).bounds(x,y,w,20).build());
 }
 private void flag(int x,int y,String title,String key){
  button(x,y,238,title+": "+(V177JarvisSettings.on(key)?"ON":"OFF"),
    ()->V177JarvisSettings.toggle(key));
 }
 @Override protected void init(){
  int x=this.width/2-120,y=Math.max(22,this.height/2-125);
  button(x,y,58,"VOICE",()->{page=0;subpage=0;});
  button(x+60,y,58,"SCAN",()->{page=1;subpage=0;});
  button(x+120,y,58,"ALERTS",()->{page=2;subpage=0;});
  button(x+180,y,58,"MODULES",()->{page=3;subpage=0;});
  y+=27;
  if(page==0&&subpage==0){
   button(x,y,238,"Voice language: "+(V177JarvisSettings.german?"DEUTSCH":"ENGLISH"),
    ()->V177JarvisSettings.language(!V177JarvisSettings.german));
   button(x,y+23,238,"Voice volume: "+V177JarvisSettings.volume+"% (step 10)",
    ()->V177JarvisSettings.setVolume(V177JarvisSettings.volume>=100?0:V177JarvisSettings.volume+10));
   String[] flags=FLAGS[page][subpage];
   for(int i=0;i<flags.length;i++){
    String[] entry=flags[i].split("\\|",2);
    flag(x,y+(i+2)*23,entry[1],entry[0]);
   }
  }else if(page==1&&subpage==0){
   button(x,y,238,"Detection radius: "+V177JarvisSettings.radius+" blocks (step 8)",
    ()->V177JarvisSettings.setRadius(V177JarvisSettings.radius>=64?8:V177JarvisSettings.radius+8));
   String[] flags=FLAGS[page][subpage];
   for(int i=0;i<flags.length;i++){
    String[] entry=flags[i].split("\\|",2);
    flag(x,y+(i+1)*23,entry[1],entry[0]);
   }
  }else{
   String[] flags=FLAGS[page][subpage];
   for(int i=0;i<flags.length;i++){
    String[] entry=flags[i].split("\\|",2);
    flag(x,y+i*23,entry[1],entry[0]);
   }
  }
  // Navigation occupies its own row; DONE never overlaps any toggle.
  if(subpage>0)button(x,y+143,86,"< PREV",()->subpage--);
  if(subpage<FLAGS[page].length-1)button(x+152,y+143,86,"NEXT >",()->subpage++);
  button(x,y+168,238,"DONE",()->this.onClose());
 }
 @Override public void extractBackground(net.minecraft.client.gui.GuiGraphicsExtractor graphics,int mouseX,int mouseY,float partial){
  super.extractBackground(graphics,mouseX,mouseY,partial);
  graphics.text(font,"J.A.R.V.I.S.  /  ARMOR INTELLIGENCE SYSTEM",
      this.width/2-105,Math.max(10,this.height/2-148),0xff75d9ea);
 }
}
''')
add("client/V177JarvisClient.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.nutrition.NutriPaste;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.powerarmor.V177ArmorIntegrity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import java.util.ArrayDeque;
import java.util.Comparator;

/** Local, loaded-only and cooldown-gated J.A.R.V.I.S. voice and HUD.
 *  Audio uses the player's native OS text-to-speech. No fake voice files.
 */
public final class V177JarvisClient {
 private V177JarvisClient(){}
 private record Message(int priority,String english,String deutsch){}
 private static final ArrayDeque<Message> messages=new ArrayDeque<>();
 // v1.7.7 uses bundled offline male voice clips, never the Minecraft narrator.
 private static String subtitle="";
 private static int subtitleUntil;
 private static int lastTick=Integer.MIN_VALUE;
 private static int nextTalk=0;
 private static boolean wasInArmor=false,wasSleeping=false,wasFlying=false;
 private static boolean prevAttackMode=false;
 private static boolean nearHome=false;
 private static int prevEnergy=101,prevPaste=101,prevIntegrity=101;
 private static String scanKey="";
 private static int lastScanSpeech=Integer.MIN_VALUE/2;
 private static int lastProjectile=Integer.MIN_VALUE/2;
 private static int lastEnvironment=Integer.MIN_VALUE/2;
 private static boolean initial=true;
 public static boolean enabled(){return V177JarvisSettings.enabled;}
 public static boolean available(){
  var mc=Minecraft.getInstance();
  return mc.player!=null&&full(mc.player);
 }
 public static int[] withJarvis(int[] other){
  if(!available())return other;
  int[] out=java.util.Arrays.copyOf(other,other.length+2);
  out[other.length]=9;out[other.length+1]=10;
  return out;
 }
 public static void toggle(){
  V177JarvisSettings.enabled(!enabled());
  if(enabled())enqueue(2,"At your service, sir.","Zu Ihren Diensten, Sir.");
  else directly("Going offline. Until next time, sir.",
                "Ich gehe offline. Bis zum nächsten Mal, Sir.");
 }
 public static void wheelAction(int action){
  if(!enabled()||!V177JarvisSettings.on("actions"))return;
  switch(action){
   case 3->{
    // The sole voice action outside a worn suit: immediate recall acknowledgement.
    if(!available()) directly("Armor recall initiated. I'm on my way, sir.",
                              "Rüstungsrückruf eingeleitet. Ich bin auf dem Weg, Sir.");
    else enqueue(3,"Armor recall initiated. I'm on my way, sir.",
                   "Rüstungsrückruf eingeleitet. Ich bin auf dem Weg, Sir.");
   }
   case 6->enqueue(1,"Follow mode command received, sir.",
                      "Folgemodus-Befehl empfangen, Sir.");
   case 7->enqueue(1,"Turret mode command received, sir.",
                      "Geschützturmmodus-Befehl empfangen, Sir.");
   case 8->enqueue(1,"Sleep mode command received, sir.",
                      "Schlafmodus-Befehl empfangen, Sir.");
   default->{}
  }
 }
 private static boolean full(LocalPlayer p){
  int tier=PowerArmorRuntime.tier(p.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  if(tier<=0)return false;
  for(int i=1;i<4;i++)
   if(PowerArmorRuntime.tier(p.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)return false;
  return true;
 }
 private static void enqueue(int priority,String english,String deutsch){
  if(!enabled()||!V177JarvisSettings.on("voice"))return;
  if(messages.size()>=8)messages.removeLast();
  Message msg=new Message(priority,english,deutsch);
  if(priority>=4)messages.addFirst(msg);else messages.addLast(msg);
 }
 private static void directly(String en,String de){
  if(!V177JarvisSettings.on("voice"))return;
  speak(V177JarvisSettings.german?de:en);
 }
 private static void speak(String text){
  subtitle=text;
  var mc=Minecraft.getInstance();
  subtitleUntil=(mc.player==null?0:mc.player.tickCount)+100;
  V177JarvisAudio.enqueue(text,V177JarvisSettings.german,V177JarvisSettings.volume);
 }
 private static String number(int v){return String.valueOf(v);}
 private static int threshold(int current,int previous,int[] levels){
  for(int level:levels)if(previous>level&&current<=level)return level;
  return -1;
 }
 private static void checkLevels(LocalPlayer p){
  long total=0L,max=0L;
  for(var slot:PowerArmorRuntime.SLOTS){
   ItemStack stack=p.getItemBySlot(slot);
   total+=Math.max(0L,EnergyTool.energy(stack));
   max+=Math.max(0L,EnergyTool.capacity(stack));
  }
  int energy=max>0?(int)Math.round(100D*total/max):0;
  int paste=(int)Math.round(100D*NutriPaste.stored(p.getItemBySlot(PowerArmorRuntime.SLOTS[0]))
       /NutriPaste.HELMET_CAPACITY);
  int integrity=V177ArmorIntegrity.totalPercent(p);
  int e=threshold(energy,prevEnergy,new int[]{0,25,50});
  int n=threshold(paste,prevPaste,new int[]{1,25,50,57});
  int a=threshold(integrity,prevIntegrity,new int[]{0,1,25,50});
  if(e>=0&&V177JarvisSettings.on("energy"))
   enqueue(e==0?5:e==25?4:2,
      e==0?"Warning, sir. Armor energy reserves are completely depleted. Powered systems are offline.":
      "Sir, armor energy reserves have dropped to "+e+" percent.",
      e==0?"Warnung, Sir. Die Rüstungsenergie ist vollständig aufgebraucht.":
      "Sir, die Rüstungsenergie liegt bei "+e+" Prozent.");
  if(n>=0&&V177JarvisSettings.on("paste"))
   enqueue(n<=1?5:n<=25?4:2,
     n<=1?"Warning, sir. NutriPaste reserves are at one percent. Immediate refilling is recommended.":
         "Sir, NutriPaste reserves are at "+n+" percent.",
     "Sir, der NutriPaste-Vorrat liegt bei "+n+" Prozent.");
  if(a>=0&&V177JarvisSettings.on("integrity"))
   enqueue(a==0?5:a<=25?4:2,
     a==0?"Critical structural failure, sir. All armor protection systems are offline.":
          "Sir, armor structural integrity is at "+a+" percent.",
     a==0?"Kritischer Strukturausfall, Sir. Alle Rüstungsschutzsysteme sind offline.":
          "Sir, die Rüstungsintegrität liegt bei "+a+" Prozent.");
  prevEnergy=energy;prevPaste=paste;prevIntegrity=integrity;
 }
 private static String greeting(LocalPlayer p){
  long time=Math.floorMod(p.level().getOverworldClockTime(),24000L);
  return time<6000L?"Good morning":time<12000L?"Good afternoon":"Good evening";
 }
 private static String greetingDe(LocalPlayer p){
  long time=Math.floorMod(p.level().getOverworldClockTime(),24000L);
  return time<6000L?"Guten Morgen":time<12000L?"Guten Tag":"Guten Abend";
 }
 private static void start(LocalPlayer p){
  checkLevels(p);
  if(V177JarvisSettings.on("greeting"))
   enqueue(2,greeting(p)+", sir. Welcome back.",
            greetingDe(p)+", Sir. Willkommen zurück.");
  if(V177JarvisSettings.on("startup")){
   enqueue(2,"Armor diagnostics complete. Structural integrity at "+
     prevIntegrity+" percent. Energy reserves at "+prevEnergy+
     " percent. NutriPaste reserves at "+prevPaste+" percent. "+
     (prevIntegrity==0?"Armor systems offline.":"All systems operational."),
     "Rüstungsdiagnose abgeschlossen. Integrität "+prevIntegrity+
     " Prozent. Energie "+prevEnergy+" Prozent. NutriPaste "+prevPaste+
     " Prozent. "+(prevIntegrity==0?"Rüstungssysteme offline.":"Alle Systeme einsatzbereit."));
  }
 }
 private static String direction(LocalPlayer p,Entity e){
  var delta=e.position().subtract(p.position());
  var look=p.getLookAngle();
  double front=delta.x*look.x+delta.z*look.z;
  double side=look.z*delta.x-look.x*delta.z;
  if(Math.abs(front)>Math.abs(side))
   return front>0?"ahead of you":"behind you";
  return side>0?"to your right":"to your left";
 }
 private static String directionDe(LocalPlayer p,Entity e){
  return switch(direction(p,e)){
   case "ahead of you"->"vor Ihnen";
   case "behind you"->"hinter Ihnen";
   case "to your right"->"rechts von Ihnen";
   default->"links von Ihnen";
  };
 }
 private static String joinCategories(java.util.List<String> categories,String conjunction){
  if(categories.size()==1)return categories.get(0);
  return String.join(", ",categories.subList(0,categories.size()-1))+
         " "+conjunction+" "+categories.get(categories.size()-1);
 }
 private static void scan(LocalPlayer p){
  var mc=Minecraft.getInstance();
  int radius=V177JarvisSettings.radius;
  var range=p.getBoundingBox().inflate(radius);
  var all=mc.level.getEntitiesOfClass(Entity.class,range,
      e->e!=p&&e.isAlive()&&e.distanceToSqr(p)<=radius*radius);
  int hostile=0,passive=0,players=0,bosses=0;
  Monster closest=null;double closestD=Double.POSITIVE_INFINITY;
  boolean projectile=false;
  for(Entity entity:all){
   if(entity instanceof Player){if(V177JarvisSettings.on("players"))players++;continue;}
   if(entity instanceof EnderDragon||entity instanceof WitherBoss){
    if(V177JarvisSettings.on("bosses"))bosses++;
    continue;
   }
   if(entity instanceof Monster monster){
    if(V177JarvisSettings.on("hostiles")){
     hostile++;
     double d=monster.distanceToSqr(p);
     if(d<closestD){closest=monster;closestD=d;}
    }
   }else if(entity instanceof Animal){
    if(V177JarvisSettings.on("passives"))passive++;
   }
   if(entity instanceof Projectile proj && V177JarvisSettings.on("projectile")){
    var toPlayer=p.position().subtract(proj.position());
    if(toPlayer.lengthSqr()<24D*24D&&proj.getDeltaMovement().dot(toPlayer)>0.06D)
     projectile=true;
   }
  }
  int tick=p.tickCount;
  if(projectile&&tick-lastProjectile>100){
   lastProjectile=tick;
   enqueue(4,"Incoming projectile, sir.","Ein Geschoss nähert sich, Sir.");
  }
  String key=hostile+"/"+passive+"/"+players+"/"+bosses;
  boolean any=hostile+passive+players+bosses>0;
  if(any&&!key.equals(scanKey)&&tick-lastScanSpeech>=200){
   // Include only actual categories, never irrelevant zero counts.
   var enParts=new java.util.ArrayList<String>();
   var deParts=new java.util.ArrayList<String>();
   if(hostile>0){
    enParts.add(hostile+(hostile==1?" hostile entity":" hostile entities"));
    deParts.add(hostile+(hostile==1?" feindliche Kreatur":" feindliche Kreaturen"));
   }
   if(passive>0){
    enParts.add(passive+(passive==1?" passive creature":" passive creatures"));
    deParts.add(passive+(passive==1?" friedliche Kreatur":" friedliche Kreaturen"));
   }
   if(players>0){
    enParts.add(players+(players==1?" player":" players"));
    deParts.add(players+" Spieler");
   }
   if(bosses>0){
    enParts.add(bosses+(bosses==1?" boss":" bosses"));
    deParts.add(bosses+(bosses==1?" Boss":" Bosse"));
   }
   String en="Sir, I am detecting "+joinCategories(enParts,"and")+
         " within "+radius+" blocks.";
   String de="Sir, ich erkenne "+joinCategories(deParts,"und")+
         " im Umkreis von "+radius+" Blöcken.";
   if(closest!=null&&V177JarvisSettings.on("nearest")){
    int dist=(int)Math.round(Math.sqrt(closestD));
    String kind=closest.getType().getDescription().getString();
    en+=" The closest threat is a "+kind+", "+dist+" blocks "+direction(p,closest)+".";
    de+=" Die nächste Bedrohung ist "+kind+", "+dist+" Blöcke "+directionDe(p,closest)+".";
   }
   enqueue(hostile+bosses>0?3:1,en,de);
   lastScanSpeech=tick;
  }
  scanKey=key;
 }
 private static void checkHome(LocalPlayer p){
  if(!V177JarvisSettings.on("home"))return;
  // 26.1 replaced getSharedSpawnPos with synchronized respawn data.
  // /sethome is mod-specific and cannot be inferred from world spawn.
  var data=p.level().getRespawnData();
  if(data==null||!data.dimension().equals(p.level().dimension()))return;
  BlockPos home=data.pos();
  double distance=p.distanceToSqr(home.getX()+.5,home.getY()+.5,home.getZ()+.5);
  if(!nearHome&&distance<=64D){
   nearHome=true;
   enqueue(2,"Welcome home, sir.","Willkommen zu Hause, Sir.");
  }else if(nearHome&&distance>=144D)nearHome=false;
 }
 private static void checkEnvironment(LocalPlayer p){
  if(!V177JarvisSettings.on("environment"))return;
  if(p.tickCount-lastEnvironment<600)return;
  if(p.level().getMaxLocalRawBrightness(p.blockPosition())<=3
       &&p.getY()<30){
   lastEnvironment=p.tickCount;
   enqueue(1,"Sir, we are entering a deep cave. Visibility is limited.",
             "Sir, wir betreten eine tiefe Höhle. Die Sicht ist eingeschränkt.");
  }
 }
 public static void tick(){
  var mc=Minecraft.getInstance();
  if(mc.player==null){wasInArmor=false;return;}
  LocalPlayer p=mc.player;
  if(lastTick==p.tickCount)return;
  lastTick=p.tickCount;
  V177JarvisSettings.load(p.getUUID());
  boolean worn=full(p);
  if(!worn){
   if(wasInArmor&&enabled()&&V177JarvisSettings.on("greeting"))
    directly("See you later, sir.","Bis später, Sir.");
   wasInArmor=false;wasSleeping=false;wasFlying=false;prevAttackMode=false;
   messages.clear();initial=true;return;
  }
  if(!wasInArmor){
   wasInArmor=true;initial=true;prevEnergy=101;prevPaste=101;prevIntegrity=101;
   prevAttackMode=V176AttackModeClient.active();
   if(enabled())start(p);
  }
  if(!enabled())return;
  if(p.tickCount%5==0)checkLevels(p);
  // Use the real synced armor upgrade state instead of guessing from the click.
  boolean attackMode=V176AttackModeClient.active();
  if(attackMode!=prevAttackMode&&V177JarvisSettings.on("actions")){
   if(attackMode)enqueue(3,"Attack mode activated.","Angriffsmodus aktiviert.");
   else enqueue(3,"Attack mode deactivated.","Angriffsmodus deaktiviert.");
  }
  prevAttackMode=attackMode;
  boolean sleep=p.getPose()==Pose.SLEEPING;
  if(sleep&&!wasSleeping&&V177JarvisSettings.on("sleep"))
   enqueue(2,"Sleeping in progress, sir.","Schlafvorgang läuft, Sir.");
  if(!sleep&&wasSleeping&&V177JarvisSettings.on("sleep"))
   enqueue(2,"Sleeping finished. Good morning, sir.",
             "Schlafvorgang abgeschlossen. Guten Morgen, Sir.");
  wasSleeping=sleep;
  boolean flight=p.getAbilities().flying;
  if(!wasFlying&&flight&&V177JarvisSettings.on("actions"))
   enqueue(2,"Flight systems engaged, sir.","Flugsysteme aktiviert, Sir.");
  else if(wasFlying&&!flight&&V177JarvisSettings.on("actions"))
   enqueue(1,"Flight systems disengaged.","Flugsysteme deaktiviert.");
  wasFlying=flight;
  if(p.tickCount%20==0){scan(p);checkHome(p);}
  if(p.tickCount%100==0)checkEnvironment(p);
  if(!messages.isEmpty()&&p.tickCount>=nextTalk){
   Message chosen=messages.removeFirst();
   String line=V177JarvisSettings.german?chosen.deutsch():chosen.english();
   speak(line);
   nextTalk=p.tickCount+Math.max(50,line.split("\\s+").length*8);
  }
 }
 public static void draw(RenderGuiEvent.Post event){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return;
  var g=event.getGuiGraphics();
  g.pose().pushMatrix();
  g.pose().translate(8f,8f);
  g.pose().scale(.7f,.7f);
  g.text(mc.font,"J.A.R.V.I.S.",0,0,0xff78e1f5);
  g.text(mc.font,"ARMOR INTELLIGENCE SYSTEM",0,11,0xffa8c4dc);
  g.text(mc.font,enabled()?"ONLINE":"OFFLINE",0,22,enabled()?0xff87eac1:0xffe98f7a);
  // Audio-only J.A.R.V.I.S.: no spoken sentence text in the HUD.
  // Preserve title, ARMOR INTELLIGENCE SYSTEM and ONLINE/OFFLINE.
  g.pose().popMatrix();
 }
}
''')
add("client/V177JarvisAudio.java",r'''package dev.obsidiannetwork.client;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.SourceDataLine;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;

/** Bundled neural speech; no network, third-party app, or narrator at runtime. */
public final class V177JarvisAudio {
 private V177JarvisAudio(){}
 private record ClipSpec(String text,String resource){}
 private record Job(List<String> clips,int volume){}
 private static final AudioFormat FORMAT=new AudioFormat(22050f,16,1,true,false);
 private static final ArrayBlockingQueue<Job> queue=new ArrayBlockingQueue<>(8);
 private static final Map<String,List<ClipSpec>> CATALOG=loadCatalog();
 private static final Thread WORKER=startWorker();
 private static Map<String,List<ClipSpec>> loadCatalog(){
  Map<String,List<ClipSpec>> map=new HashMap<>();
  try(InputStream input=V177JarvisAudio.class.getResourceAsStream(
       "/assets/obsidiannetwork/jarvis_audio/catalog.tsv")){
   if(input==null){System.err.println("XSXLABS_JARVIS_NO_VOICE_ASSETS");return map;}
   try(BufferedReader reader=new BufferedReader(new InputStreamReader(input,StandardCharsets.UTF_8))){
    String line;
    while((line=reader.readLine())!=null){
     String[] parts=line.split("\\t",3);
     if(parts.length!=3||parts[1].isEmpty())continue;
     map.computeIfAbsent(parts[0],k->new ArrayList<>())
       .add(new ClipSpec(parts[1],parts[0]+"/"+parts[2]+".wav"));
    }
   }
   for(List<ClipSpec> list:map.values())
    list.sort(Comparator.comparingInt((ClipSpec c)->c.text().length()).reversed());
  }catch(Exception ex){System.err.println("XSXLABS_JARVIS_CATALOG_ERROR "+ex);}
  return map;
 }
 private static List<String> plan(String text,boolean german){
  List<ClipSpec> list=CATALOG.get(german?"de":"en");
  if(list==null||list.isEmpty()||text==null||text.isEmpty())return List.of();
  List<String> clips=new ArrayList<>();
  int index=0;
  while(index<text.length()){
   char ch=text.charAt(index);
   if(Character.isWhitespace(ch)||ch==','||ch=='.'||ch==';'||ch==':'||ch=='!'||ch=='?'){
    index++;continue;
   }
   if(ch>='0'&&ch<='9'){
    int start=index;
    while(index<text.length()&&text.charAt(index)>='0'&&text.charAt(index)<='9')index++;
    try{
     int n=Integer.parseInt(text.substring(start,index));
     if(n<0||n>100)return List.of();
     clips.add((german?"de":"en")+"/number_"+n+".wav");
     continue;
    }catch(NumberFormatException err){return List.of();}
   }
   ClipSpec matching=null;
   for(ClipSpec spec:list){
    String word=spec.text();
    if(index+word.length()>text.length()||
       !text.regionMatches(true,index,word,0,word.length()))continue;
    int end=index+word.length();
    if(Character.isLetterOrDigit(word.charAt(word.length()-1))&&end<text.length()
      &&Character.isLetterOrDigit(text.charAt(end)))continue;
    matching=spec;break;
   }
   if(matching==null)return List.of();
   clips.add(matching.resource());index+=matching.text().length();
  }
  return List.copyOf(clips);
 }
 public static boolean enqueue(String text,boolean german,int volume){
  List<String> clips=plan(text,german);
  if(clips.isEmpty()){
   System.err.println("XSXLABS_JARVIS_MISSING_SPOKEN_LINE: "+text);
   return false;
  }
  Job job=new Job(clips,Math.max(0,Math.min(100,volume)));
  if(!queue.offer(job)){queue.poll();queue.offer(job);}
  return true;
 }
 private static Thread startWorker(){
  Thread t=new Thread(()->{
   while(!Thread.currentThread().isInterrupted()){
    try{play(queue.take());}
    catch(InterruptedException ex){Thread.currentThread().interrupt();}
    catch(Exception ex){System.err.println("XSXLABS_JARVIS_AUDIO_PLAYBACK "+ex);}
   }
  },"xSxLabs-JARVIS-Voice");
  t.setDaemon(true);t.start();return t;
 }
 private static void play(Job job) throws Exception{
  if(job.volume()==0)return;
  SourceDataLine line=AudioSystem.getSourceDataLine(FORMAT);
  try{
   line.open(FORMAT,32768);line.start();
   byte[] buf=new byte[8192];
   for(String key:job.clips()){
    String path="/assets/obsidiannetwork/jarvis_audio/"+key;
    try(InputStream raw=V177JarvisAudio.class.getResourceAsStream(path)){
     if(raw==null)throw new IOException("missing audio "+key);
     try(AudioInputStream wav=AudioSystem.getAudioInputStream(new BufferedInputStream(raw))){
      if(!wav.getFormat().matches(FORMAT))
       throw new IOException("voice format mismatch "+key+" "+wav.getFormat());
      int count;
      while((count=wav.read(buf,0,buf.length))>=0){
       if(count==0)continue;
       int size=count-(count%2);
       for(int i=0;i<size;i+=2){
        int sample=(short)((buf[i]&0xff)|(buf[i+1]<<8));
        int scaled=(int)(sample*(job.volume()/100f));
        buf[i]=(byte)scaled;buf[i+1]=(byte)(scaled>>>8);
       }
       line.write(buf,0,size);
      }
     }
    }
   }
   line.drain();
  }finally{line.stop();line.close();}
 }
}
''')
print("V177_JARVIS_CLIENT_VOICE_WHEEL_SETTINGS_INSTALLED")
