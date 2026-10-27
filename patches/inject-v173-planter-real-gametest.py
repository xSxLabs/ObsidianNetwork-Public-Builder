#!/usr/bin/env python3
"""Run real v1.7.3 legacy Planter migration on the existing 800-cell GameTest.

Only augments generated CI-only Java, never frozen 1.7.2 or player saves.
Fail closed when the known storage fixture changes.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])
target=root/"dev/obsidiannetwork/build103/Build103GameTests.java"
src=target.read_text(encoding="utf-8")
# Use a short semantically unique statement, not indentation or a two-line
# assertion rewritten by the earlier performance GameTest patch stages.
anchor='var stone=dev.obsidiannetwork.core.ItemKey.simple("minecraft:stone");'
marker="V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST"
if src.count(anchor)!=1 or marker in src:
    raise RuntimeError(f"Real storage fixture drift or repeated injection: anchors={src.count(anchor)}")
extra=r'''
                  // V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST: no mock cells.
                  // Different legacy and canonical keys must converge without loss.
                  var xsxCodec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
                  var xsxOakLegacy=dev.obsidiannetwork.core.ItemKey.simple("minecraft:oak_log");
                  var xsxOakExact=xsxCodec.describe(new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.OAK_LOG));
                  rt.descriptors().registerKnown(xsxOakExact.key(),xsxOakExact.canonicalPayload());
                  if(xsxOakLegacy.equals(xsxOakExact.key()))
                    throw new IllegalStateException("Test requires distinct legacy/canonical oak keys");
                  if(rt.storage().insert(xsxOakLegacy,1560L)!=1560L||
                     rt.storage().insertExact(xsxOakExact.key(),xsxOakExact.canonicalPayload(),19L)!=19L)
                    throw new IllegalStateException("Cannot seed actual 800-cell oak migration");
                  for(int xsxPass=0;xsxPass<4;xsxPass++)
                    if(!dev.obsidiannetwork.network.LegacyPlanterKeyMigration.migratePlainItem(
                         level,rt,net.minecraft.world.item.Items.OAK_LOG))
                      throw new IllegalStateException("Oak migration incomplete at batch "+xsxPass);
                  if(rt.storage().index().amount(xsxOakLegacy)!=0L||
                     rt.storage().index().amount(xsxOakExact.key())!=1579L||
                     rt.storage().cells().stream().mapToLong(c->c.amount(xsxOakLegacy)).sum()!=0L||
                     rt.storage().cells().stream().mapToLong(c->c.amount(xsxOakExact.key())).sum()!=1579L)
                    throw new IllegalStateException("Old+new oak logs did not unify/conserve in physical cells");
                  var xsxCarrotLegacy=dev.obsidiannetwork.core.ItemKey.simple("minecraft:carrot");
                  var xsxCarrotExact=xsxCodec.describe(new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.CARROT));
                  rt.descriptors().registerKnown(xsxCarrotExact.key(),xsxCarrotExact.canonicalPayload());
                  if(rt.storage().insert(xsxCarrotLegacy,520L)!=520L||
                     rt.storage().insertExact(xsxCarrotExact.key(),xsxCarrotExact.canonicalPayload(),11L)!=11L)
                    throw new IllegalStateException("Cannot seed carrot migration");
                  for(int xsxPass=0;xsxPass<2;xsxPass++)
                    if(!dev.obsidiannetwork.network.LegacyPlanterKeyMigration.migratePlainItem(
                         level,rt,net.minecraft.world.item.Items.CARROT))
                      throw new IllegalStateException("Carrot migration incomplete "+xsxPass);
                  if(rt.storage().index().amount(xsxCarrotLegacy)!=0L||
                     rt.storage().index().amount(xsxCarrotExact.key())!=531L||
                     rt.storage().cells().stream().mapToLong(c->c.amount(xsxCarrotExact.key())).sum()!=531L)
                    throw new IllegalStateException("Carrot migration duplicated or lost items");
                  var xsxWheatLegacy=dev.obsidiannetwork.core.ItemKey.simple("minecraft:wheat");
                  var xsxWheatExact=xsxCodec.describe(new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.WHEAT));
                  rt.descriptors().registerKnown(xsxWheatExact.key(),xsxWheatExact.canonicalPayload());
                  if(rt.storage().insert(xsxWheatLegacy,520L)!=520L||
                     rt.storage().insertExact(xsxWheatExact.key(),xsxWheatExact.canonicalPayload(),15L)!=15L)
                    throw new IllegalStateException("Cannot seed automatic wheat migration");
                  dev.obsidiannetwork.network.LegacyPlanterKeyMigration.tick(level,rt);
                  long xsxAfterTick=rt.storage().index().amount(xsxWheatLegacy);
                  if(xsxAfterTick!=8L)throw new IllegalStateException(
                     "Automatic tick did not migrate bounded first 512 wheat: remaining="+xsxAfterTick);
                  dev.obsidiannetwork.network.LegacyPlanterKeyMigration.tick(level,rt);
                  if(rt.storage().index().amount(xsxWheatLegacy)!=xsxAfterTick)
                    throw new IllegalStateException("Migration repeated within one server tick");
                  if(!dev.obsidiannetwork.network.LegacyPlanterKeyMigration.migratePlainItem(
                        level,rt,net.minecraft.world.item.Items.WHEAT)||
                     rt.storage().index().amount(xsxWheatLegacy)!=0L||
                     rt.storage().index().amount(xsxWheatExact.key())!=535L)
                    throw new IllegalStateException("Automatic wheat migration reconciliation failed");
                  var xsxUnrelated=dev.obsidiannetwork.core.ItemKey.simple("minecraft:diamond_sword");
                  if(rt.storage().insert(xsxUnrelated,7L)!=7L||
                     dev.obsidiannetwork.network.LegacyPlanterKeyMigration.migratePlainItem(
                        level,rt,net.minecraft.world.item.Items.DIAMOND_SWORD)||
                     rt.storage().index().amount(xsxUnrelated)!=7L||
                     rt.storage().extract(xsxUnrelated,7L)!=7L)
                    throw new IllegalStateException("Migration touched an unrelated item type");
                  System.out.println("V173_PLANTER_REAL_STORAGE_MIGRATION_GAME_TEST PASS"+
                    " cells=800 oak=1579 carrot=531 wheat=535 no_loss_or_duplication=true");
'''
target.write_text(src.replace(anchor,anchor+"\n"+extra,1),encoding="utf-8")
print("V173_PLANTER_REAL_GAMETEST_INJECTED: 800 real cells, mixed keys, auto tick, conservation")
