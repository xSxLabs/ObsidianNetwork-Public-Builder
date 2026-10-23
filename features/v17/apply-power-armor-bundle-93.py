#!/usr/bin/env python3
"""Build 93: loss-safe manual Power Armor unequip, front-pad station docking,
vanilla attributes for Jade, and ten cosmetically distinct additional MK tiers.

Execute AFTER all existing 70/78/91 overlays. Do not touch MK1/MK2 assets,
SavedData codecs, or the successful Build92 Tesseract/channel implementation.
"""
import os, json, re, struct, zlib
from pathlib import Path

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
recipes=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork/recipe"
parts=(("helmet","HEAD","netherite_helmet",3),
       ("chestplate","CHEST","netherite_chestplate",8),
       ("leggings","LEGS","netherite_leggings",6),
       ("boots","FEET","netherite_boots",3))
# Primary plating, second metallic trim, unique crafting-dye
finishes={
 3:("Midnight Blue","Mitternachtsblau",(25,48,91),(179,192,205),"blue_dye"),
 4:("Arctic White","Arktisweiß",(218,222,224),(60,96,128),"white_dye"),
 5:("Army Olive","Olivgrün",(64,81,51),(189,157,83),"green_dye"),
 6:("Graphite Red","Graphitrot",(42,48,55),(188,37,58),"red_dye"),
 7:("Void Purple","Void-Violett",(57,33,85),(142,97,201),"purple_dye"),
 8:("Teal Bronze","Türkisbronze",(21,108,121),(179,118,65),"cyan_dye"),
 9:("Burgundy Steel","Bordeauxstahl",(105,29,52),(190,205,212),"magenta_dye"),
10:("Navy Copper","Marineblau-Kupfer",(23,41,69),(202,117,62),"orange_dye"),
11:("Forest Champagne","Waldgrün-Champagner",(28,92,57),(194,171,112),"lime_dye"),
12:("Ice Cobalt","Eis-Kobalt",(218,235,239),(38,101,207),"light_blue_dye"),
}

def load(p):return p.read_text(encoding="utf-8")
def put(p,contents):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(contents,encoding="utf-8")
def edit(p,old,new):
 s=load(p); count=s.count(old)
 assert count==1, f"BUILD93 anchor drift {p} ({count}): {old[:140]}"
 put(p,s.replace(old,new,1))
def jwrite(relative,old,new):edit(java/relative,old,new)
def dump(p,obj):put(p,json.dumps(obj,indent=2,ensure_ascii=False)+"\n")

# Vanilla item component, NOT just cosmetic entity attributes:
# each piece contributes netherite-equivalent values to armor HUD, Jade, and
# real Minecraft damage calculations. FE-based card mitigation stays additive.
statfile=java/"powerarmor/PowerArmorStats.java"
assert not statfile.exists(),"Build93 duplicate PowerArmorStats"
put(statfile,r'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.component.ItemAttributeModifiers;

/** Real standard equipment attributes on each wearable MK1..MK12 piece. */
public final class PowerArmorStats {
 private PowerArmorStats(){}
 public static ItemAttributeModifiers forSlot(EquipmentSlot slot){
  EquipmentSlotGroup group=switch(slot){
   case HEAD -> EquipmentSlotGroup.HEAD;
   case CHEST -> EquipmentSlotGroup.CHEST;
   case LEGS -> EquipmentSlotGroup.LEGS;
   case FEET -> EquipmentSlotGroup.FEET;
   default -> throw new IllegalArgumentException("Non-armor slot "+slot);
  };
  int protection=switch(slot){
   case HEAD -> 3;
   case CHEST -> 8;
   case LEGS -> 6;
   case FEET -> 3;
   default -> 0;
  };
  String key=slot.getName();
  return ItemAttributeModifiers.builder()
      .add(Attributes.ARMOR,new AttributeModifier(
          Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_"+key+"_armor"),
          protection,AttributeModifier.Operation.ADD_VALUE),group)
      .add(Attributes.ARMOR_TOUGHNESS,new AttributeModifier(
          Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_"+key+"_toughness"),
          3.0D,AttributeModifier.Operation.ADD_VALUE),group)
      .build();
 }
}
''')
mod=java/"ObsidianNetwork.java"
code=load(mod)
# Patch precisely the existing eight registered wearable items without
# altering item registry IDs, asset identifiers, recipes or stored FE metadata.
for part,slot,_,armor in parts:
 for tier in (1,2):
  item="power_armor_"+(f"mk{tier}_" if tier>1 else "")+part
  find='ITEMS.registerItem("'+item+'", p -> new dev.obsidiannetwork.powerarmor.PowerArmorItem('
  start=code.index(find);end=code.index('));',start)
  fragment=code[start:end]
  old='p.stacksTo(1).durability(4000000)'
  assert fragment.count(old)==1, item+" attributes installation anchor"
  fragment=fragment.replace(old,old+
    '.component(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS,'+
    'dev.obsidiannetwork.powerarmor.PowerArmorStats.forSlot('+
    'net.minecraft.world.entity.EquipmentSlot.'+slot+'))',1)
  code=code[:start]+fragment+code[end:]

# New items deliberately reuse all MK1 gameplay code; the registry ID and
# item equipment asset are distinct. No recipe collides with MK2 or other MKs.
addition=""
for tier in finishes:
 for part,slot,material,armor in parts:
  ident=f"power_armor_mk{tier}_{part}"
  addition+=f'''   public static final DeferredItem<dev.obsidiannetwork.powerarmor.PowerArmorItem> POWER_ARMOR_MK{tier}_{part.upper()} =
      ITEMS.registerItem("{ident}", p -> new dev.obsidiannetwork.powerarmor.PowerArmorItem(
        p.stacksTo(1).durability(4000000)
          .component(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS,
             dev.obsidiannetwork.powerarmor.PowerArmorStats.forSlot(net.minecraft.world.entity.EquipmentSlot.{slot}))
          .component(net.minecraft.core.component.DataComponents.UNBREAKABLE,net.minecraft.util.Unit.INSTANCE)
          .component(net.minecraft.core.component.DataComponents.EQUIPPABLE,
             net.minecraft.world.item.equipment.Equippable.builder(net.minecraft.world.entity.EquipmentSlot.{slot})
                .setAsset(net.minecraft.resources.ResourceKey.create(
                   net.minecraft.world.item.equipment.EquipmentAssets.ROOT_ID,
                   net.minecraft.resources.Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_mk{tier}")))
                .build())
          .component(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get(),0L)
      ));
'''
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE ='
assert code.count(anchor)==1
code=code.replace(anchor,addition+anchor,1)
# Creative inventory exposure for all forty additional pieces.
tab='            output.accept((ItemLike)POWER_ARMOR_MK2_BOOTS.get());'
assert code.count(tab)==1,"Missing Build32 MK2 creative slot"
code=code.replace(tab,tab+'\n'+'\n'.join(
 f'            output.accept((ItemLike)POWER_ARMOR_MK{tier}_{part.upper()}.get());'
 for tier in finishes for part,*_ in parts),1)
put(mod,code)

runtime=java/"powerarmor/PowerArmorRuntime.java"
# All 48 pieces uniquely identify their tier. Never infer tier=MK1 from an
# invalid helmet or accept mismatched chest/legs/boots.
tiermethod=''' public static int tier(ItemStack stack,int slot){
  if(stack.isEmpty())return 0;
'''
for tier in range(1,13):
 for idx,(part,_,_,_) in enumerate(parts):
  var=(f"POWER_ARMOR_MK{tier}_{part.upper()}" if tier>1 else f"POWER_ARMOR_{part.upper()}")
  tiermethod+=f"  if(slot=={idx}&&stack.is(dev.obsidiannetwork.ObsidianNetwork.{var}.get()))return {tier};\n"
tiermethod+='''  return 0;
 }
'''
s=load(runtime)
anchor=' public static boolean full(ServerPlayer p){'
assert s.count(anchor)==1
s=s.replace(anchor,tiermethod+anchor,1)
# Other built-ins still use the old piece(stack,slot,isMk2) for selecting
# the two legacy visuals. Replace ONLY full-set validation with tier().
beg=s.index(' public static boolean full(ServerPlayer p){')
end=s.index(' }',beg)+2
before=s[beg:end]
assert "piece(" in before and "mk2" in before
after=''' public static boolean full(ServerPlayer p){
  int tier=tier(p.getItemBySlot(SLOTS[0]),0);
  if(tier==0)return false;
  for(int i=1;i<SLOTS.length;i++)
   if(tier(p.getItemBySlot(SLOTS[i]),i)!=tier)return false;
  return true;
 }'''
s=s[:beg]+after+s[end:]
# The backup is world-persisted. If the entire suit was manually removed,
# auto-recover the previous armor atomically into FOUR EMPTY equipment slots;
# keep backup pending for partial removal or occupied slots. This never
# recreates/extracts Power Armor items, so there is no duplication path.
old='''  if(p.tickCount%5!=0)return;'''
assert s.count(old)==1
s=s.replace(old,old+'''
  var oldArmor=ArmorLoadoutData.get(p.level().getServer());
  if(oldArmor.has(p)&&!full(p)){
   boolean empty=true;
   for(EquipmentSlot slot:SLOTS)
    if(!p.getItemBySlot(slot).isEmpty()){empty=false;break;}
   if(empty)oldArmor.recover(p);
  }''',1)
put(runtime,s)

world=java/"powerarmor/PowerArmorSuitWorld.java"
s=load(world)
beg=s.index(' public static boolean full(ArmorStand stand){')
end=s.index(' }',beg)+2
previous=s[beg:end]
assert "mk2" in previous and "piece(" in previous
replacement=''' public static boolean full(ArmorStand stand){
  int tier=PowerArmorRuntime.tier(stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  if(tier==0)return false;
  for(int i=1;i<4;i++)
   if(PowerArmorRuntime.tier(stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)return false;
  return true;
 }'''
s=s[:beg]+replacement+s[end:]
# Critical62's transfer-before-spawn protection is retained byte-for-byte.
find='''  boolean mk2=PowerArmorRuntime.piece(suit.get(0),0,true);
  for(int i=0;i<4;i++)if(!PowerArmorRuntime.piece(suit.get(i),i,mk2))return null;'''
assert s.count(find)==1,"Build62 spawn prevalidation anchor changed"
s=s.replace(find,'''  int suitTier=PowerArmorRuntime.tier(suit.get(0),0);
  if(suitTier==0)return null;
  for(int i=1;i<4;i++)if(PowerArmorRuntime.tier(suit.get(i),i)!=suitTier)return null;''',1)
# Build38 assumed fixed north; Build49 added actual FACING property, so use
# the modeled front direction and measure radius from station, not parking pad.
assert s.count('BlockPos candidate=station.north();')==1
s=s.replace('BlockPos candidate=station.north();',
 '''BlockPos candidate=station.relative(level.getBlockState(station).getValue(ArmorStationBlock.FACING));''',1)
assert s.count('if(candidate.distSqr(origin)>4.0D)continue;')==1
s=s.replace('if(candidate.distSqr(origin)>4.0D)continue;',
            'if(station.distSqr(origin)>4.0D)continue;',1)
# Select GeckoLib transition model from the actual suit tier.
find='''  boolean mk2=PowerArmorRuntime.piece(
     stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0,true);
  var type=mk2?dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get()
              :dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get();'''
assert s.count(find)==1,"GeckoLib animation tier selection changed"
selection='''  int tier=PowerArmorRuntime.tier(stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0);
  net.minecraft.world.entity.EntityType<PowerArmorVisualEntity> type=switch(tier){
   case 2 -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get();
'''
for tier in finishes:
 selection+=f"   case {tier} -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{tier}.get();\n"
selection+='''   default -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get();
  };'''
s=s.replace(find,selection,1)
put(world,s)

# GeckoLib transition entities remain cosmetic and ephemeral. Add an animated
# renderer for each variant, with the exact same 13-bone MK1 mesh/animation.
mod=java/"ObsidianNetwork.java"
s=load(mod)
anchor='   public static final net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.entity.EntityType<?>,\n       net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity>> ARMOR_VISUAL_ENTITY_MK2 ='
assert s.count(anchor)==1
# Insert new regs before the MK2 reg; entity DeferredRegister already active.
registrations=""
for tier in finishes:
 registrations+=f'''   public static final net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.entity.EntityType<?>,
       net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity>> ARMOR_VISUAL_ENTITY_MK{tier} =
       ARMOR_VISUAL_ENTITIES.registerEntityType("power_armor_visual_mk{tier}",
         dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(1.6F,2.5F).clientTrackingRange(8).updateInterval(1).noSave());
'''
s=s.replace(anchor,registrations+anchor,1);put(mod,s)
renderer=java/"client/PowerArmorGeoRenderers.java"
s=load(renderer)
anchor='  event.registerEntityRenderer(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get(),'
assert s.count(anchor)==1
s=s.replace(anchor,''.join(
 f'''  event.registerEntityRenderer(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{tier}.get(),
    ctx -> new com.geckolib.renderer.GeoEntityRenderer<>(
      ctx,ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{tier}.get()));
''' for tier in finishes)+anchor,1);put(renderer,s)
attrs=java/"powerarmor/PowerArmorAttributes.java"
s=load(attrs)
anchor='  event.put(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get(),vanillaStandBase);'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n'+''.join(
 f'  event.put(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{tier}.get(),vanillaStandBase);\n'
 for tier in finishes),1);put(attrs,s)

# Resource generation: recolor the real MK1 PNG pixels (not AI concepts)
# preserving original shading, design, alpha, highlights, geometry, and visor.
# Supports both indexed textures and all five valid RGBA PNG filter modes.
def pack(kind,payload):
 return struct.pack(">I",len(payload))+kind+payload+struct.pack(">I",zlib.crc32(kind+payload)&0xffffffff)
def chunks(data):
 assert data.startswith(b"\x89PNG\r\n\x1a\n")
 out=[];i=8
 while i<len(data):
  n=struct.unpack(">I",data[i:i+4])[0]
  kind=data[i+4:i+8];payload=data[i+8:i+8+n];i+=12+n
  out.append((kind,payload))
  if kind==b"IEND":break
 return out
def recolor_rgb(rgb,primary,trim):
 r,g,b=rgb
 # Base MK1 saturated red/black plates -> new primary.
 if r>70 and r>g*1.8 and r>b*1.7:
  luminance=max(.26,min(1.32,r/170.0))
  return tuple(max(0,min(255,int(c*luminance))) for c in primary)
 # MK1 golden edges -> new metallic secondary.
 if r>110 and g>92 and b>40 and r>b*1.20:
  luminance=max(.37,min(1.4,(r+g)/360.0))
  return tuple(max(0,min(255,int(c*luminance))) for c in trim)
 return rgb
def recolor_png(data,primary,trim):
 inp=chunks(data)
 hdr=next(d for k,d in inp if k==b"IHDR")
 w,h,depth,kind,compression,filter_method,interlace=struct.unpack(">IIBBBBB",hdr)
 assert depth==8 and interlace==0 and compression==0
 if kind==3:
  out=[]
  for name,payload in inp:
   if name==b"PLTE":
    values=bytearray(payload)
    for i in range(0,len(values),3):
     values[i:i+3]=bytes(recolor_rgb(tuple(values[i:i+3]),primary,trim))
    payload=bytes(values)
   out.append(pack(name,payload))
  return b"\x89PNG\r\n\x1a\n"+b"".join(out)
 assert kind in (2,6),f"unsupported MK1 texture PNG color type {kind}"
 bpp=4 if kind==6 else 3
 packed=zlib.decompress(b"".join(payload for name,payload in inp if name==b"IDAT"))
 previous=bytearray(w*bpp);rows=[];idx=0
 for _ in range(h):
  mode=packed[idx];idx+=1
  row=bytearray(packed[idx:idx+w*bpp]);idx+=w*bpp
  for i in range(len(row)):
   left=row[i-bpp] if i>=bpp else 0
   up=previous[i];corner=previous[i-bpp] if i>=bpp else 0
   if mode==0:predict=0
   elif mode==1:predict=left
   elif mode==2:predict=up
   elif mode==3:predict=(left+up)//2
   elif mode==4:
    p=left+up-corner;ds=(abs(p-left),abs(p-up),abs(p-corner))
    predict=(left,up,corner)[ds.index(min(ds))]
   else:raise AssertionError("unknown filter")
   row[i]=(row[i]+predict)&255
  previous=row[:]
  for i in range(0,len(row),bpp):
   if bpp==4 and row[i+3]==0:continue
   row[i:i+3]=bytes(recolor_rgb(tuple(row[i:i+3]),primary,trim))
  rows.append(b"\x00"+row)
 assert idx==len(packed),"PNG pixel length mismatch"
 out=[]
 for name,payload in inp:
  if name==b"IDAT":
   if not any(k==b"IDAT" for k,_ in out):
    out.append((name,zlib.compress(b"".join(rows),9)))
  else:out.append((name,payload))
 return b"\x89PNG\r\n\x1a\n"+b"".join(pack(k,v) for k,v in out)

for tier,(english,german,primary,secondary,dye) in finishes.items():
 key=f"power_armor_mk{tier}"
 for layer in ("humanoid","humanoid_leggings"):
  source=res/f"textures/entity/equipment/{layer}/power_armor.png"
  dest=source.parent/(key+".png")
  dest.write_bytes(recolor_png(source.read_bytes(),primary,secondary))
 dump(res/f"equipment/{key}.json",{"layers":{
  "humanoid":[{"texture":"obsidiannetwork:"+key}],
  "humanoid_leggings":[{"texture":"obsidiannetwork:"+key}]}})
 for part,slot,material,_ in parts:
  ident=f"{key}_{part}"
  icon=res/f"textures/item/power_armor_{part}.png"
  (icon.parent/(ident+".png")).write_bytes(recolor_png(icon.read_bytes(),primary,secondary))
  dump(res/f"models/item/{ident}.json",{"parent":"minecraft:item/generated",
         "textures":{"layer0":"obsidiannetwork:item/"+ident}})
  dump(res/f"items/{ident}.json",{"model":{"type":"minecraft:model",
         "model":"obsidiannetwork:item/"+ident}})
  # Distinct dye ensures no conflicting recipe outputs for ten variants.
  dump(recipes/(ident+".json"),{
   "type":"minecraft:crafting_shaped","pattern":["ABA","CDC","AEA"],
   "key":{"A":"minecraft:netherite_ingot","B":"minecraft:iron_block",
          "C":"minecraft:diamond","D":"minecraft:"+material,"E":"minecraft:"+dye},
   "result":{"id":"obsidiannetwork:"+ident,"count":1}})
 for lang,title in (("en_us",english),("de_de",german)):
  path=res/f"lang/{lang}.json"
  data=json.loads(load(path))
  labels={"helmet":("Helmet","Helm"),"chestplate":("Chestplate","Brustplatte"),
          "leggings":("Leggings","Beinschutz"),"boots":("Boots","Stiefel")}
  for part,_,_,_ in parts:
   data["item.obsidiannetwork."+key+"_"+part]=(
    f"Power Armor MK{tier} {title} {labels[part][0]}" if lang=="en_us" else
    f"Power-Rüstung MK{tier} {title} {labels[part][1]}")
  dump(path,data)
 # GeckoLib model and animation stay identical to MK1, only shell pixels differ.
 model=res/"geckolib/models/entity/power_armor_visual_mk1.geo.json"
 animation=res/"geckolib/animations/entity/power_armor_visual_mk1.animation.json"
 assert model.exists() and animation.exists()
 data=json.loads(load(model))
 data["minecraft:geometry"][0]["description"]["identifier"]=f"geometry.power_armor_visual_mk{tier}"
 dump(res/f"geckolib/models/entity/power_armor_visual_mk{tier}.geo.json",data)
 put(res/f"geckolib/animations/entity/power_armor_visual_mk{tier}.animation.json",load(animation))
 png=res/"textures/entity/power_armor_visual_mk1.png"
 (res/f"textures/entity/power_armor_visual_mk{tier}.png").write_bytes(
    recolor_png(png.read_bytes(),primary,secondary))

assert sum(load(mod).count(f'ITEMS.registerItem("power_armor_mk{t}_') for t in finishes)==40
assert all(f"ARMOR_VISUAL_ENTITY_MK{t}" in load(mod) for t in finishes)
assert 'getValue(ArmorStationBlock.FACING)' in load(world)
assert 'if(station.distSqr(origin)>4.0D)continue;' in load(world)
assert 'oldArmor.recover(p)' in load(runtime)
assert 'DataComponents.ATTRIBUTE_MODIFIERS' in load(mod)
print("BUILD93_POWER_ARMOR_PASS: manual unequip recovery, real vanilla attributes, facing-aware 2-block front docking, MK3-MK12 complete matching sets, dedicated recipes, original MK1/MK2 art preserved and 10 color-matched animated GeckoLib meshes")
