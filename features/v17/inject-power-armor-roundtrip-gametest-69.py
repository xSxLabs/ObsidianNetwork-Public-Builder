#!/usr/bin/env python3
"""Build 69: CI-only live Power Armor transfer regression (MK1/MK2).

This injects a dedicated NeoForge server GameTest into the temporary build103
class after all v1.7 runtime overlays. No shipped game code is modified and
the temporary test class is removed before packaging the user JAR.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/build103/Build103GameTests.java"
s = p.read_text(encoding="utf-8")
marker = "POWER_ARMOR_REAL_ROUNDTRIP_V69"
register = 'event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork", "fifty_real_storage_drives"),'
klass = "private static final class FullEquipmentCellTest extends GameTestInstance {"
assert marker not in s and s.count(register) == 1 and s.count(klass) == 1, "Build 69 test fixture changed"

registration = '''event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork", "power_armor_real_roundtrip"),
                  new PowerArmorRoundtripTest(new TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>>(environment, STRUCTURE, 190, 0, true, Rotation.NONE)));
              '''
s = s.replace(register, registration + register, 1)

test_class = r'''
            /** No mock-client connection: direct server entity, item, and tick paths only. */
            private static final class PowerArmorRoundtripTest extends GameTestInstance {
              PowerArmorRoundtripTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data){super(data);}
              @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){
                throw new UnsupportedOperationException("CI-only Power Armor transfer test");
              }
              @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){
                return Component.literal("Real MK1/MK2 Power Armor conservation roundtrip");
              }
              private static void check(boolean ok,String message){
                if(!ok)throw new IllegalStateException("POWER_ARMOR_REAL_ROUNDTRIP_V69: "+message);
              }
              private static java.util.List<net.minecraft.world.entity.decoration.ArmorStand> owned(
                  net.minecraft.server.level.ServerLevel level,BlockPos base,
                  net.minecraft.server.level.ServerPlayer player){
                return level.getEntitiesOfClass(net.minecraft.world.entity.decoration.ArmorStand.class,
                  new net.minecraft.world.phys.AABB(base).inflate(5D),
                  e -> e.entityTags().contains("xsxlabs_power_armor_suit_v17")
                    && e.entityTags().contains("xsxlabs_power_armor_owner_"+player.getUUID()));
              }
              private static void completeTransition(net.minecraft.server.level.ServerPlayer player){
                for(int i=0;i<20;i++)
                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.transitionTick(
                    new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(player));
              }
              @Override public void run(GameTestHelper helper){
                var level=(net.minecraft.server.level.ServerLevel)helper.getLevel();
                var profile=new com.mojang.authlib.GameProfile(
                  java.util.UUID.fromString("d69bf1ba-d852-4fa1-b293-89c7bd2a147e"),"XSXArmorCI");
                var player=net.neoforged.neoforge.common.util.FakePlayerFactory.get(level,profile);
                BlockPos base=helper.absolutePos(new BlockPos(5,3,5));
                // Give the player a private two-block-high air volume and four exit spots.
                for(int dx=-2;dx<=2;dx++)for(int dz=-2;dz<=2;dz++)
                  for(int dy=0;dy<3;dy++)
                    level.setBlock(base.offset(dx,dy,dz),Blocks.AIR.defaultBlockState(),3);
                player.setPos(base.getX()+0.5D,base.getY(),base.getZ()+0.5D);
                var slots=dev.obsidiannetwork.powerarmor.PowerArmorRuntime.SLOTS;
                var vanilla=new net.minecraft.world.item.Item[]{
                  net.minecraft.world.item.Items.IRON_HELMET,
                  net.minecraft.world.item.Items.IRON_CHESTPLATE,
                  net.minecraft.world.item.Items.IRON_LEGGINGS,
                  net.minecraft.world.item.Items.IRON_BOOTS
                };
                // The full five-level upgrade stack must survive every physical
                // suit transfer, even with vanilla armor saved/restored.
                final String protectionFive="protection,protection,protection,protection,protection";
                for(int tier=0;tier<2;tier++){
                  var parts=tier==0?new net.minecraft.world.item.Item[]{
                    ObsidianNetwork.POWER_ARMOR_HELMET.get(),
                    ObsidianNetwork.POWER_ARMOR_CHESTPLATE.get(),
                    ObsidianNetwork.POWER_ARMOR_LEGGINGS.get(),
                    ObsidianNetwork.POWER_ARMOR_BOOTS.get()
                  }:new net.minecraft.world.item.Item[]{
                    ObsidianNetwork.POWER_ARMOR_MK2_HELMET.get(),
                    ObsidianNetwork.POWER_ARMOR_MK2_CHESTPLATE.get(),
                    ObsidianNetwork.POWER_ARMOR_MK2_LEGGINGS.get(),
                    ObsidianNetwork.POWER_ARMOR_MK2_BOOTS.get()
                  };
                  check(owned(level,base,player).isEmpty(),"old world stand remains before tier "+tier);
                  for(int i=0;i<4;i++)player.setItemSlot(slots[i],new net.minecraft.world.item.ItemStack(parts[i]));
                  player.getItemBySlot(slots[1]).set(
                    dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),protectionFive);
                  check(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),"missing tier "+tier+" before first exit");
                  // First-ever V exit: no previous equipment backup exists.
                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,"first exit failed, tier "+tier);
                  completeTransition(player);
                  var stands=owned(level,base,player);
                  check(stands.size()==1,"first exit created "+stands.size()+" world suits, tier "+tier);
                  var stand=stands.get(0);
                  check(protectionFive.equals(stand.getItemBySlot(slots[1]).get(
                    dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get())),
                    "all five Protection cards must survive first exit");
                  check(!stand.isInvisible(),"exited suit is invisible, tier "+tier);
                  for(int i=0;i<4;i++){
                    check(player.getItemBySlot(slots[i]).isEmpty(),"player retains duplicated piece "+i);
                    check(stand.getItemBySlot(slots[i]).getItem()==parts[i],"stand missing original piece "+i);
                  }
                  // This vanilla armor must be saved, then restored after re-entry and exit.
                  for(int i=0;i<4;i++)player.setItemSlot(slots[i],new net.minecraft.world.item.ItemStack(vanilla[i]));
                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.tryEnter(player,stand.getId());
                  dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.tryEnter(player,stand.getId());
                  // Duplicated click packets are not permitted to mutate inventory mid-animation.
                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==vanilla[i],
                    "early item overwrite from repeated entry packet "+i);
                  completeTransition(player);
                  check(stand.isRemoved(),"entered world suit still exists, tier "+tier);
                  check(protectionFive.equals(player.getItemBySlot(slots[1]).get(
                    dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get())),
                    "all five Protection cards must survive re-entry");
                  check(owned(level,base,player).isEmpty(),"second owned stand after enter, tier "+tier);
                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==parts[i],
                    "player missing transferred piece "+i);
                  check(dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.exit(player)==1,
                    "exit after entering failed, tier "+tier);
                  completeTransition(player);
                  for(int i=0;i<4;i++)check(player.getItemBySlot(slots[i]).getItem()==vanilla[i],
                    "prior vanilla armor not restored "+i);
                  stands=owned(level,base,player);
                  check(stands.size()==1,"re-exit not exactly one world suit, tier "+tier);
                  check(protectionFive.equals(stands.get(0).getItemBySlot(slots[1]).get(
                    dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get())),
                    "all five Protection cards must survive second exit");
                  for(int i=0;i<4;i++)check(stands.get(0).getItemBySlot(slots[i]).getItem()==parts[i],
                    "re-exit corrupted original suit "+i);
                  stands.get(0).discard();
                  for(int i=0;i<4;i++)player.setItemSlot(slots[i],net.minecraft.world.item.ItemStack.EMPTY);
                  System.out.println("POWER_ARMOR_REAL_ROUNDTRIP_V69 PASS tier=MK"+(tier+1)+
                      " first_exit=true duplicate_click_guard=true previous_armor_restored=true protection5_roundtrip=true");
                }
                helper.succeed();
              }
            }

'''
s = s.replace(klass, test_class + klass, 1)
assert s.count(marker) == 2 and s.count("power_armor_real_roundtrip") == 1
p.write_text(s, encoding="utf-8")
print("POWER_ARMOR_REAL_ROUNDTRIP_V69 INJECTED")
