#!/usr/bin/env python3
"""Build 131: latest worn suit preference, grouped controls, instant station break."""
import os,json
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def edit(path,a,b):
 p=root/path
 s=p.read_text(encoding="utf-8")
 assert s.count(a)==1,(path,"anchor drift",s.count(a),a[:110])
 p.write_text(s.replace(a,b,1),encoding="utf-8")

pref=root/"powerarmor/PowerArmorRecallPreference.java"
assert not pref.exists()
pref.write_text(r'''package dev.obsidiannetwork.powerarmor;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
/** BUILD131_LAST_WORN_PERSISTED: only a suit UUID, not item stacks. */
public final class PowerArmorRecallPreference extends SavedData {
 public record Entry(String owner,String suit){
  public static final Codec<Entry> CODEC=RecordCodecBuilder.create(i->i.group(
   Codec.STRING.fieldOf("owner").forGetter(Entry::owner),
   Codec.STRING.fieldOf("suit").forGetter(Entry::suit)
  ).apply(i,Entry::new));
 }
 public static final SavedDataType<PowerArmorRecallPreference> TYPE=new SavedDataType<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_last_worn"),
  PowerArmorRecallPreference::new,
  Entry.CODEC.listOf().xmap(PowerArmorRecallPreference::new,PowerArmorRecallPreference::all));
 private final Map<String,Entry> entries=new LinkedHashMap<>();
 public PowerArmorRecallPreference(){}
 private PowerArmorRecallPreference(List<Entry> loaded){
  for(Entry e:loaded)entries.put(e.owner(),e);
 }
 public static PowerArmorRecallPreference get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 public List<Entry> all(){return List.copyOf(entries.values());}
 public UUID preferred(UUID owner){
  Entry value=entries.get(owner.toString());
  if(value==null)return null;
  try{return UUID.fromString(value.suit());}
  catch(IllegalArgumentException ignored){return null;}
 }
 public void remember(UUID owner,UUID suit){
  Entry next=new Entry(owner.toString(),suit.toString());
  if(!next.equals(entries.put(next.owner(),next)))setDirty();
 }
}
''',encoding="utf-8")

edit("powerarmor/PowerArmorRecall.java",
 ''' /** Only server may choose the source, destination and transfer. */
 public static int request(ServerPlayer player){''',
 ''' /** BUILD131_REMEMBER_AFTER_EXIT: only after verified transactional exit. */
 public static void rememberLastWorn(ServerPlayer player,ArmorStand stand){
  if(!(stand.level() instanceof ServerLevel world)
     ||world!=player.level()||!owned(stand,player.getUUID()))return;
  PowerArmorRecallIndex.get(world.getServer()).index(stand,world,player.getUUID());
  PowerArmorRecallPreference.get(world.getServer()).remember(player.getUUID(),stand.getUUID());
 }
 /** Only server may choose the source, destination and transfer. */
 public static int request(ServerPlayer player){''')

edit("powerarmor/PowerArmorRecall.java",
 '''  var matches=PowerArmorRecallIndex.get(player.level().getServer()).owned(player.getUUID());
  if(matches.size()!=1){
   tell(player,matches.isEmpty()?
    "no indexed suit; load older v1.7 suit's chunk once to register it.":
    "several owned suits indexed; refusing ambiguous recall.");
   return 0;
  }
  var loc=matches.get(0);''',
 '''  // BUILD131_PREFER_LAST_WORN: not the nearest, oldest or last loaded.
  var matches=PowerArmorRecallIndex.get(player.level().getServer()).owned(player.getUUID());
  if(matches.isEmpty()){
   tell(player,"no indexed suit; load older v1.7 suit's chunk once to register it.");
   return 0;
  }
  PowerArmorRecallIndex.Location loc;
  if(matches.size()==1){
   loc=matches.get(0);
  }else{
   UUID last=PowerArmorRecallPreference.get(player.level().getServer()).preferred(player.getUUID());
   loc=null;
   if(last!=null)for(var candidate:matches)
    if(candidate.suit().equals(last.toString())){loc=candidate;break;}
   if(loc==null){
    tell(player,"multiple suits found but no last-worn suit saved. Exit your preferred armor once.");
    return 0;
   }
  }''')

# The exit transaction has already checked the equipment was transferred
# only once, that the new stand survived and original gear is restored.
edit("powerarmor/PowerArmorSuitWorld.java",
 '''   if(backup!=null)saved.finish(player);
   player.sendSystemMessage(Component.literal(
    "Power Armor disengaged. Right-click the standing suit to enter."));''',
 '''   if(backup!=null)saved.finish(player);
   // BUILD131_VERIFIED_EXIT_FAVORITE: a new stand gets a NEW suit UUID.
   PowerArmorRecall.rememberLastWorn(player,stand);
   player.sendSystemMessage(Component.literal(
    "Power Armor disengaged. Right-click the standing suit to enter."));''')

category=root/"powerarmor/ObsidianKeyCategory.java"
assert not category.exists()
category.write_text(r'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
/** BUILD131_MOD_KEY_CATEGORY: all mod bindings grouped in vanilla controls. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class ObsidianKeyCategory {
 private ObsidianKeyCategory(){}
 public static final KeyMapping.Category CATEGORY=new KeyMapping.Category(
   Identifier.fromNamespaceAndPath("obsidiannetwork","controls"));
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){
  e.registerCategory(CATEGORY);
 }
}
''',encoding="utf-8")
grouped=[]
for file in sorted(root.rglob("*.java")):
 if file==category:continue
 content=file.read_text(encoding="utf-8")
 if '"key.obsidiannetwork.' not in content or 'KeyMapping.Category.MISC' not in content:continue
 file.write_text(content.replace('KeyMapping.Category.MISC',
   'dev.obsidiannetwork.powerarmor.ObsidianKeyCategory.CATEGORY'),encoding="utf-8")
 grouped.append(file.relative_to(root).as_posix())
assert "powerarmor/PowerArmorRecallKeyClient.java" in grouped,grouped
assert "powerarmor/PowerArmorExitKeyClient.java" in grouped,grouped
for lang in ("de_de","en_us"):
 p=assets/"lang"/(lang+".json")
 d=json.loads(p.read_text(encoding="utf-8"))
 d["key.category.obsidiannetwork.controls"]="xSxLabs Network Storage"
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Zero hardness, unchanged high blast resistance and occupied-station break guard.
edit("ObsidianNetwork.java",".strength(4.0F,3600000.0F)",".strength(0.0F,3600000.0F)")
print("BUILD131_LAST_WORN_RECALL PASS; GROUPED="+",".join(grouped)+"; STATION_HAND_INSTANT PASS")
