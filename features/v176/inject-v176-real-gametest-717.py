#!/usr/bin/env python3
"""B717 CI-only NeoForge GameTest: real FE bullets, Looting, Follow/Turret.

Extend the existing real MK1/MK2 equipment roundtrip, rather than creating
a mock system. This source file is temporary and excluded from release JAR.
Everything is tested on server-level ItemStacks and real projectile entities.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
def inject(old,new):
 global s
 assert s.count(old)==1,("V176_B717_GAMETEST_ANCHOR_DRIFT",s.count(old),old[:110])
 s=s.replace(old,new,1)

start='''                  check(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),"missing tier "+tier+" before first exit");'''
test=r'''
                  // B717: real server-side shot + exact FE + module gated
                  // + real enchantment registry; no mock projectile simulation.
                  if(tier==0){
                    var chest=player.getItemBySlot(slots[1]);
                    var card=new net.minecraft.world.item.ItemStack(ObsidianNetwork.POWER_CARD_MICRO_MG.get());
                    var lookup=level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT);
                    var loot=lookup.getOrThrow(net.minecraft.world.item.enchantment.Enchantments.LOOTING);
                    card.enchant(loot,2);
                    check(dev.obsidiannetwork.powerarmor.V176LootingSupport.itemLevel(
                       card,level.registryAccess())==2,"B717 Looting II anvil card unreadable");
                    String installed=dev.obsidiannetwork.powerarmor.V176LootingSupport.install(
                       protectionFive,"micro_mg",card,level.registryAccess());
                    check(dev.obsidiannetwork.powerarmor.V176LootingSupport.level(installed)==2,
                      "B717 Looting II not persisted on installed module");
                    var recovered=new net.minecraft.world.item.ItemStack(ObsidianNetwork.POWER_CARD_MICRO_MG.get());
                    dev.obsidiannetwork.powerarmor.V176LootingSupport.restore(
                       recovered,installed,level.registryAccess());
                    check(recovered.getEnchantmentLevel(loot)==2,
                      "B717 Looting II not recovered when uninstalling module");
                    chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),installed);
                    dev.obsidiannetwork.core.EnergyTool.setEnergy(chest,9000L);
                    long before=dev.obsidiannetwork.core.EnergyTool.energy(chest);
                    check(before>=6000L,"B717 chest FE capacity too low for two 3000 FE shots: "+before);
                    check(dev.obsidiannetwork.powerarmor.V176AttackModeServer.toggle(player)==1,
                      "B717 real Attack Mode activation rejected");
                    check(dev.obsidiannetwork.powerarmor.V176AttackModeServer.on(player),
                      "B717 installed weapon not recognized");
                    var bullets=level.getEntitiesOfClass(
                      dev.obsidiannetwork.powerarmor.V176MicroMgProjectile.class,
                      new net.minecraft.world.phys.AABB(base).inflate(40D));
                    int bulletCount=bullets.size();
                    check(dev.obsidiannetwork.powerarmor.V176MicroMgFire.fire(player)==1,
                      "B717 first physical FE projectile rejected");
                    check(dev.obsidiannetwork.core.EnergyTool.energy(chest)==before-3000L,
                      "B717 FE must be charged exactly once per spawned projectile");
                    int bulletCountAfter=level.getEntitiesOfClass(
                      dev.obsidiannetwork.powerarmor.V176MicroMgProjectile.class,
                      new net.minecraft.world.phys.AABB(base).inflate(40D)).size();
                    check(bulletCountAfter==bulletCount+1,
                      "B717 no physical new projectile entity after FE consumption");
                    check(dev.obsidiannetwork.powerarmor.V176MicroMgFire.fire(player)==0,
                      "B717 cooldown allowed double fire in same server tick");
                    check(dev.obsidiannetwork.core.EnergyTool.energy(chest)==before-3000L,
                      "B717 rejected shot erroneously consumed FE");
                    check(dev.obsidiannetwork.powerarmor.V176AttackModeServer.toggle(player)==1,
                      "B717 Attack Mode deactivation rejected");
                    check(!dev.obsidiannetwork.powerarmor.V176AttackModeServer.on(player),
                      "B717 disabled attack kept a weapon state");
                    chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
                      protectionFive);
                    dev.obsidiannetwork.core.EnergyTool.setEnergy(chest,0L);
                    System.out.println("V176_B717_REAL_BULLET_FE_LOOTING PASS "+
                       "spawned=true charged_once=true cooldown=true looting2_roundtrip=true");
                  }
'''
inject(start,start+"\n"+test.rstrip("\n"))

end='''                  stands.get(0).discard();'''
test2=r'''
                  // B717: the persistent real suit has no phantom third mode.
                  // Both buttons exclusively toggle same real owned stand.
                  if(tier==0){
                    var worldSuit=stands.get(0);
                    var worldChest=worldSuit.getItemBySlot(slots[1]);
                    worldChest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),
                      protectionFive+",micro_mg");
                    dev.obsidiannetwork.core.EnergyTool.setEnergy(worldChest,6000L);
                    check(dev.obsidiannetwork.powerarmor.V176CompanionMode.toggle(player,false)==1,
                      "B717 Follow toggle failed on real world suit");
                    check(worldSuit.entityTags().contains("xsxlabs_v176_follow"),
                      "B717 real suit did not enter Follow");
                    check(!worldSuit.entityTags().contains("xsxlabs_v176_turret"),
                      "B717 Follow wrongly enabled Turret attack");
                    check(dev.obsidiannetwork.powerarmor.V176CompanionMode.toggle(player,true)==1,
                      "B717 Turret toggle failed on real world suit");
                    check(worldSuit.entityTags().contains("xsxlabs_v176_turret"),
                      "B717 Turret tag not persisted");
                    check(!worldSuit.entityTags().contains("xsxlabs_v176_follow"),
                      "B717 exclusive mode not enforced");
                    check(dev.obsidiannetwork.powerarmor.V176CompanionMode.toggle(player,true)==1,
                      "B717 Turret OFF failed");
                    check(!worldSuit.entityTags().contains("xsxlabs_v176_turret"),
                      "B717 Turret kept active after OFF");
                    check(!worldSuit.entityTags().contains("xsxlabs_v176_follow"),
                      "B717 disabling Turret wrongly reenabled Follow");
                    System.out.println("V176_B717_REAL_COMPANION_EXCLUSIVE PASS "+
                      "follow_only=true turret_follows=true toggle_off=true");
                  }
'''
inject(end,test2.rstrip("\n")+"\n"+end)
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
assert s.count("V176_B717_REAL_BULLET_FE_LOOTING PASS")==1
assert s.count("V176_B717_REAL_COMPANION_EXCLUSIVE PASS")==1
assert s.count("protection5_roundtrip=true")==1
p.write_text(s,encoding="utf-8")
print("V176_B717_REAL_MK1_FE_PROJECTILE_LOOTING_AND_FOLLOW_TURRET_GAMETEST_INJECTED")
