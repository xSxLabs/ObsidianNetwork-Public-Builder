package dev.obsidiannetwork.restarttest;

import com.google.gson.GsonBuilder;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity;
import dev.obsidiannetwork.blockentity.LogisticsCableBlockEntity;
import dev.obsidiannetwork.conduit.ConduitNetworkManager;
import dev.obsidiannetwork.conduit.ConduitRuntime;
import dev.obsidiannetwork.conduit.ConduitType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.capabilities.Capabilities;

/** CI only. Exercises a real saved world across two independent server JVMs. */
@EventBusSubscriber(modid = "obsidiannetwork")
public final class ItemConduitRestartProbe {
    private static final String PHASE = System.getenv("ON_ITEM_RESTART_PHASE");
    private static final int Y = 100;
    private static int ticks;
    private static int stage;
    private static int stageStart;
    private static boolean done;
    private static final Map<String, Object> report = new LinkedHashMap<>();

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post event) {
        if (PHASE == null || done) return;
        MinecraftServer server = event.getServer();
        if (!server.isDedicatedServer()) throw new IllegalStateException("Restart probe requires a dedicated server");
        ticks++;
        try {
            ServerLevel level = server.overworld();
            if (ticks == 1) {
                check(PHASE.equals("before") || PHASE.equals("after"), "Unknown phase");
                report.put("phase", PHASE);
                report.put("server_jvm_pid", ProcessHandle.current().pid());
                report.put("server_jvm_started", ProcessHandle.current().info().startInstant().orElseThrow().toString());
                report.put("session", System.getenv("ON_ITEM_RESTART_SESSION"));
                report.put("topologies", new String[]{"three_bundles", "three_standalone", "bundle_standalone_bundle", "standalone_bundle_standalone"});
                // Actual chunk tickets make block entities tick without any connected players.
                server.getCommands().performPrefixedCommand(server.createCommandSourceStack(), "forceload add 0 0 31 31");
                return;
            }
            if (ticks < 40) return;
            if (stage == 0) {
                for (int lane = 0; lane < 4; lane++) {
                    if (PHASE.equals("before")) create(level, lane);
                    else {
                        verifyModes(level, lane);
                        verifyContents(level, lane, false);
                        chest(level, source(lane)).setItem(0, new ItemStack(Items.GOLD_INGOT, 7));
                        chest(level, source(lane)).setItem(1, new ItemStack(Items.REDSTONE, 9));
                    }
                }
                // Snapshot the actual world-derived connection state before any
                // post-restart transfer. This distinguishes lost NBT / broken
                // connectivity from a non-running standalone block-entity ticker.
                report.put("initial_cable_topology", diagnostics(level));
                stage = 1;
                stageStart = ticks;
            }
            if (stage == 1 && allDrained(level)) {
                for (int lane = 0; lane < 4; lane++) {
                    verifyModes(level, lane);
                    verifyContents(level, lane, PHASE.equals("after"));
                }
                report.put("transfer_ticks", ticks - stageStart);
                report.put("endpoint_diagnostics", diagnostics(level));
                if (PHASE.equals("before")) finish(server, true, null);
                else {
                    // Preserve the route's endpoints, physically disconnect the middle.
                    for (int lane = 0; lane < 4; lane++) {
                        level.setBlock(cable(lane, 1), Blocks.AIR.defaultBlockState(), 3);
                        chest(level, source(lane)).setItem(0, new ItemStack(Items.COAL, 2));
                    }
                    stage = 2;
                    stageStart = ticks;
                }
            } else if (stage == 2 && ticks - stageStart >= 60) {
                for (int lane = 0; lane < 4; lane++) {
                    check(count(chest(level, source(lane)), Items.COAL) == 2, "Disconnected source changed: lane=" + lane);
                    check(count(chest(level, target(lane)), Items.COAL) == 0, "Disconnected route transported: lane=" + lane);
                    placeCable(level, lane, 1);
                }
                report.put("disconnect_ticks", ticks - stageStart);
                stage = 3;
                stageStart = ticks;
            } else if (stage == 3 && allDrained(level)) {
                for (int lane = 0; lane < 4; lane++) {
                    Map<String, Integer> expected = expected(true);
                    expected.put(id(Items.COAL), 2);
                    check(contents(chest(level, target(lane))).equals(expected), "Reconnect integrity failed: lane=" + lane);
                    verifyModes(level, lane);
                }
                report.put("reconnect_ticks", ticks - stageStart);
                report.put("item_conservation", true);
                report.put("configuration_preserved", true);
                finish(server, true, null);
            }
            if (ticks > 1200) {
                // CI-only failure forensics, NEVER a transport workaround: collect
                // the blocked inventory, try exactly one direct invocation of the
                // existing private transport method, then still FAIL the test.
                // This distinguishes a missing automatic BE ticker invocation
                // from a broken endpoint scan/capability/insert path.
                if (PHASE.equals("after") && stage == 1) {
                    try {
                        report.put("standalone_direct_transfer_diagnostic", diagnoseStandaloneTransfer(level));
                    } catch (Throwable diagnosticError) {
                        report.put("standalone_direct_transfer_error", diagnosticError.toString());
                    }
                }
                throw new IllegalStateException("Transport timed out: " + diagnostics(level));
            }
        } catch (Throwable failure) {
            failure.printStackTrace();
            try { report.put("failure_diagnostics", diagnostics(server.overworld())); }
            catch (Throwable diagnosticFailure) { report.put("diagnostic_error", diagnosticFailure.toString()); }
            finish(server, false, failure.toString());
        }
    }

    private static void create(ServerLevel level, int lane) {
        level.setBlock(source(lane), Blocks.CHEST.defaultBlockState(), 3);
        level.setBlock(target(lane), Blocks.CHEST.defaultBlockState(), 3);
        for (int i = 0; i < 3; i++) placeCable(level, lane, i);
        for (int end : new int[]{0, 2}) {
            var entity = level.getBlockEntity(cable(lane, end));
            Direction side = end == 0 ? Direction.WEST : Direction.EAST;
            if (entity instanceof ConduitBundleBlockEntity bundle) {
                bundle.setConduitFlags(ConduitBundleBlockEntity.Layer.ITEM, side, end == 2, end == 0);
            } else if (entity instanceof LogisticsCableBlockEntity cable) {
                cable.setMode(side, end == 0 ? LogisticsCableBlockEntity.Mode.IMPORT : LogisticsCableBlockEntity.Mode.EXPORT);
            } else throw new IllegalStateException("Missing endpoint block entity");
        }
        chest(level, target(lane)).setItem(0, new ItemStack(Items.COBBLESTONE, 37));
        chest(level, source(lane)).setItem(0, new ItemStack(Items.DIAMOND, 5));
        chest(level, source(lane)).setItem(1, new ItemStack(Items.EMERALD, 3));
    }

    private static void placeCable(ServerLevel level, int lane, int index) {
        boolean bundle = lane == 0 || lane == 2 && index != 1 || lane == 3 && index == 1;
        level.setBlock(cable(lane, index), (bundle ? ObsidianNetwork.CONDUIT_BUNDLE.get() : ObsidianNetwork.ITEM_CABLE.get()).defaultBlockState(), 3);
        if (bundle) {
            var entity = (ConduitBundleBlockEntity) level.getBlockEntity(cable(lane, index));
            if (!entity.has(ConduitBundleBlockEntity.Layer.ITEM)) check(entity.add(ConduitBundleBlockEntity.Layer.ITEM), "Cannot install ITEM layer");
        }
    }

    private static void verifyModes(ServerLevel level, int lane) {
        for (int end : new int[]{0, 2}) {
            var entity = level.getBlockEntity(cable(lane, end));
            Direction side = end == 0 ? Direction.WEST : Direction.EAST;
            if (entity instanceof ConduitBundleBlockEntity bundle) {
                check(bundle.has(ConduitBundleBlockEntity.Layer.ITEM), "ITEM layer missing after restart");
                check(bundle.logisticsMode(ConduitBundleBlockEntity.Layer.ITEM, side) == (end == 0 ? 1 : 2), "Persisted GUI mode changed");
                check(bundle.conduitCanExtract(ConduitBundleBlockEntity.Layer.ITEM, side) == (end == 0), "Runtime extract mode changed");
                check(bundle.conduitCanInsert(ConduitBundleBlockEntity.Layer.ITEM, side) == (end == 2), "Runtime insert mode changed");
                var config = bundle.conduitNode(ConduitType.ITEM).config(side);
                check(config.extract() == (end == 0) && config.insert() == (end == 2), "Runtime node disagrees with persisted flags");
            } else if (entity instanceof LogisticsCableBlockEntity cable) {
                check(cable.mode(side) == (end == 0 ? LogisticsCableBlockEntity.Mode.IMPORT : LogisticsCableBlockEntity.Mode.EXPORT), "Standalone persisted mode changed");
            } else throw new IllegalStateException("Saved endpoint block entity missing at " + cable(lane, end));
        }
    }

    private static Map<String, Object> diagnoseStandaloneTransfer(ServerLevel level) throws ReflectiveOperationException {
        Map<String, Object> observation = new LinkedHashMap<>();
        observation.put("before_source", contents(chest(level, source(1))));
        observation.put("before_target", contents(chest(level, target(1))));
        var entity = level.getBlockEntity(cable(1, 0));
        check(entity instanceof LogisticsCableBlockEntity, "Pure standalone source no longer a logistics cable");
        var cable = (LogisticsCableBlockEntity) entity;
        observation.put("source_fluid", cable.isFluid());
        observation.put("source_west_mode", cable.mode(Direction.WEST).name());
        observation.put("filter_allows_gold", cable.cableAllows(Direction.WEST, BuiltInRegistries.ITEM.getKey(Items.GOLD_INGOT)));
        observation.put("filter_allows_redstone", cable.cableAllows(Direction.WEST, BuiltInRegistries.ITEM.getKey(Items.REDSTONE)));
        var exports = LogisticsCableBlockEntity.class.getDeclaredMethod("exports");
        exports.setAccessible(true);
        observation.put("discovered_exports", ((java.util.List<?>) exports.invoke(cable)).size());
        var transfer = LogisticsCableBlockEntity.class.getDeclaredMethod("transferItem", Direction.class);
        transfer.setAccessible(true);
        transfer.invoke(cable, Direction.WEST);
        observation.put("after_direct_source", contents(chest(level, source(1))));
        observation.put("after_direct_target", contents(chest(level, target(1))));
        System.out.println("ITEM_STANDALONE_FAILURE_DIRECT_INVOCATION_DIAGNOSTIC " + observation);
        return observation;
    }

    private static Map<String, Object> diagnostics(ServerLevel level) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int lane = 0; lane < 4; lane++) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("source", contents(chest(level, source(lane))));
            row.put("target", contents(chest(level, target(lane))));
            row.put("source_chunk_loaded", level.hasChunkAt(source(lane)));
            row.put("target_chunk_loaded", level.hasChunkAt(target(lane)));
            row.put("source_item_capability_available", level.getCapability(Capabilities.Item.BLOCK, source(lane), Direction.EAST) != null);
            row.put("target_item_capability_available", level.getCapability(Capabilities.Item.BLOCK, target(lane), Direction.WEST) != null);
            for (int end : new int[]{0, 2}) {
                Direction side = end == 0 ? Direction.WEST : Direction.EAST;
                String prefix = end == 0 ? "source_" : "target_";
                var endpoint = level.getBlockEntity(cable(lane, end));
                if (endpoint instanceof ConduitBundleBlockEntity bundle) {
                    row.put(prefix + "mode", bundle.logisticsMode(ConduitBundleBlockEntity.Layer.ITEM, side));
                    row.put(prefix + "flags", bundle.conduitFlags(ConduitBundleBlockEntity.Layer.ITEM, side));
                    var config = bundle.conduitNode(ConduitType.ITEM).config(side);
                    row.put(prefix + "node_extract", config.extract());
                    row.put(prefix + "node_insert", config.insert());
                } else if (endpoint instanceof LogisticsCableBlockEntity cable) {
                    row.put(prefix + "mode", cable.mode(side).name());
                }
            }
            row.put("mixed_component_positions",
                    ConduitRuntime.mixedPositions(level, cable(lane, 0), ConduitType.ITEM).toString());
            for (int i = 0; i < 3; i++) {
                var segment = level.getBlockEntity(cable(lane, i));
                row.put("cable_" + i + "_block", BuiltInRegistries.BLOCK.getKey(level.getBlockState(cable(lane, i)).getBlock()).toString());
                if (segment instanceof LogisticsCableBlockEntity standalone) {
                    row.put("cable_" + i + "_west", standalone.mode(Direction.WEST).name());
                    row.put("cable_" + i + "_east", standalone.mode(Direction.EAST).name());
                } else if (segment instanceof ConduitBundleBlockEntity b) {
                    row.put("cable_" + i + "_west", b.conduitFlags(ConduitBundleBlockEntity.Layer.ITEM, Direction.WEST));
                    row.put("cable_" + i + "_east", b.conduitFlags(ConduitBundleBlockEntity.Layer.ITEM, Direction.EAST));
                }
                if (segment instanceof ConduitBundleBlockEntity bundle) {
                    var network = ConduitNetworkManager.ensure(level, bundle.conduitNode(ConduitType.ITEM));
                    row.put("nodes", network.nodes().size());
                    row.put("extract_endpoints", network.endpoints(true).size());
                    row.put("insert_endpoints", network.endpoints(false).size());
                    break;
                }
            }
            result.put("lane_" + lane, row);
        }
        return result;
    }

    private static boolean allDrained(ServerLevel level) {
        for (int lane = 0; lane < 4; lane++) if (!chest(level, source(lane)).isEmpty()) return false;
        return true;
    }

    private static void verifyContents(ServerLevel level, int lane, boolean after) {
        check(chest(level, source(lane)).isEmpty(), "Source not empty: lane=" + lane);
        check(contents(chest(level, target(lane))).equals(expected(after)), "Exact item counts changed: lane=" + lane + ", contents=" + contents(chest(level, target(lane))));
    }

    private static Map<String, Integer> expected(boolean after) {
        Map<String, Integer> result = new LinkedHashMap<>();
        result.put(id(Items.COBBLESTONE), 37);
        result.put(id(Items.DIAMOND), 5);
        result.put(id(Items.EMERALD), 3);
        if (after) { result.put(id(Items.GOLD_INGOT), 7); result.put(id(Items.REDSTONE), 9); }
        return result;
    }

    private static String id(Item item) { return BuiltInRegistries.ITEM.getKey(item).toString(); }
    private static int count(ChestBlockEntity chest, Item item) { return contents(chest).getOrDefault(id(item), 0); }
    private static Map<String, Integer> contents(ChestBlockEntity chest) {
        Map<String, Integer> result = new LinkedHashMap<>();
        for (int slot = 0; slot < chest.getContainerSize(); slot++) {
            ItemStack stack = chest.getItem(slot);
            if (!stack.isEmpty()) result.merge(id(stack.getItem()), stack.getCount(), Integer::sum);
        }
        return result;
    }

    private static BlockPos source(int lane) { return new BlockPos(13, Y, 2 + lane * 4); }
    private static BlockPos cable(int lane, int index) { return new BlockPos(14 + index, Y, 2 + lane * 4); }
    private static BlockPos target(int lane) { return new BlockPos(17, Y, 2 + lane * 4); }
    private static ChestBlockEntity chest(ServerLevel level, BlockPos position) {
        var entity = level.getBlockEntity(position);
        if (!(entity instanceof ChestBlockEntity chest)) throw new IllegalStateException("Expected persisted chest at " + position);
        return chest;
    }
    private static void check(boolean ok, String message) { if (!ok) throw new IllegalStateException(message); }

    private static void finish(MinecraftServer server, boolean success, String error) {
        if (done) return;
        done = true;
        report.put("success", success);
        report.put("elapsed_ticks", ticks);
        if (error != null) report.put("error", error);
        try {
            Path output = Path.of(System.getenv("ON_ITEM_RESTART_REPORT"));
            Files.createDirectories(output.getParent());
            Files.writeString(output, new GsonBuilder().setPrettyPrinting().create().toJson(report));
            System.out.println("ITEM_CONDUIT_PROCESS_RESTART_PHASE phase=" + PHASE + " success=" + success + " pid=" + ProcessHandle.current().pid());
        } catch (Exception exception) {
            throw new IllegalStateException("Cannot write restart report", exception);
        } finally {
            // Vanilla's normal server shutdown saves and closes all world files.
            server.halt(false);
        }
    }
}
