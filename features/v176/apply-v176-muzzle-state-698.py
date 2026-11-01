#!/usr/bin/env python3
"""v1.7.6 B698: eliminate stale armed state and alternate real turret muzzles.

Ordering: after B696 and B697. Maintains existing Follow/Turret event-only HUD.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B698_SOURCE_DRIFT",rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

edit("powerarmor/V176CompanionMode.java",
 ' private static final Map<ArmorStand,Long> LAST_SHOT=new WeakHashMap<>();',
 ''' private static final Map<ArmorStand,Long> LAST_SHOT=new WeakHashMap<>();
 /** Never keep turret visuals active after the stand becomes worn equipment. */
 public static void clearTurretToken(ItemStack chest){
  if(chest.isEmpty())return;
  String raw=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(raw==null||!raw.contains("micro_mg_turret_on"))return;
  var tokens=new java.util.ArrayList<String>(Arrays.asList(raw.split(",")));
  if(tokens.removeIf("micro_mg_turret_on"::equals))
   chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",tokens));
 }''')

edit("powerarmor/V176CompanionMode.java",
 '''  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);
   return;
  }''',
 '''  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);
   ItemStack prior=suit.getItemBySlot(EquipmentSlot.CHEST);
   clearTurretToken(prior);
   suit.setItemSlot(EquipmentSlot.CHEST,prior.copy());
   return;
  }''')

edit("powerarmor/V176AttackModeServer.java",
 '''  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg")){''',
 '''  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  if(PowerArmorRuntime.full(p))V176CompanionMode.clearTurretToken(chest);
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg")){''')

edit("powerarmor/PowerArmorSuitWorld.java",
 '   V176AttackModeServer.clearFromChest(worn.get(1));',
 '   V176AttackModeServer.clearFromChest(worn.get(1));\n   V176CompanionMode.clearTurretToken(worn.get(1));')

# Aim at the monster from left and right forearm muzzles, never both from the
# center of the armor body. Actual origin is used for final server ray trace.
edit("powerarmor/V176CompanionMode.java",
 '''   Vec3 dir=end.subtract(start).normalize();
   var shot=new V176MicroMgProjectile(''',
 '''   Vec3 centerDirection=end.subtract(start).normalize();
   Vec3 right=new Vec3(-centerDirection.z,0,centerDirection.x);
   if(right.lengthSqr()<1.0E-6D)right=new Vec3(1.0D,0,0);
   right=right.normalize();
   double barrelSide=((now/5L)&1L)==0L?0.27D:-0.27D;
   Vec3 muzzle=start.add(right.scale(barrelSide)).add(0,-0.20D,0);
   if(world.clip(new ClipContext(muzzle,end,ClipContext.Block.COLLIDER,
       ClipContext.Fluid.NONE,suit)).getType()!=HitResult.Type.MISS)continue;
   Vec3 dir=end.subtract(muzzle).normalize();
   var shot=new V176MicroMgProjectile(''')
edit("powerarmor/V176CompanionMode.java",
 '''   shot.setPos(start.x,start.y,start.z);
   shot.shoot(dir.x,dir.y,dir.z,3.0F,0.7F);''',
 '''   shot.setPos(muzzle.x,muzzle.y,muzzle.z);
   shot.shoot(dir.x,dir.y,dir.z,3.0F,0.7F);''')
edit("powerarmor/V176CompanionMode.java",
 '''   world.sendParticles(ParticleTypes.END_ROD,start.x,start.y,start.z,
     2,0.05,0.05,0.05,0.02);''',
 '''   world.sendParticles(ParticleTypes.END_ROD,muzzle.x,muzzle.y,muzzle.z,
     2,0.05,0.05,0.05,0.02);''')

s=(J/"powerarmor/V176CompanionMode.java").read_text(encoding="utf-8")
assert s.count('display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));')==1
assert s.count('shot.addTag("xsxlabs_v176_automatic_bullet");')==1
print("V176_B698_ALTERNATING_MUZZLES_AND_MODE_TRANSFER_GUARDS_PASS")
