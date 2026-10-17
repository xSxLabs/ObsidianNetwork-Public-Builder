package dev.obsidiannetwork.build103;

import com.google.gson.GsonBuilder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** CI-only server tick timing. Writes once on shutdown; never logs per operation. */
@EventBusSubscriber(modid = "obsidiannetwork")
public final class ServerTickProbe {
    private static final String OUTPUT = System.getenv("ON_SERVER_TICK_REPORT");
    private static final ArrayList<Map<String, Object>> SAMPLES = new ArrayList<>();
    private static final LinkedHashSet<String> LABELS = new LinkedHashSet<>();
    private static long started;
    private static long wallTime;

    /** Call within the measured server operation, so its containing tick is labelled. */
    public static void mark(String workload) {
        if (OUTPUT != null) LABELS.add(workload);
    }

    @SubscribeEvent
    public static void before(ServerTickEvent.Pre event) {
        if (OUTPUT == null) return;
        LABELS.clear();
        wallTime = System.currentTimeMillis();
        started = System.nanoTime();
    }

    @SubscribeEvent
    public static void after(ServerTickEvent.Post event) {
        if (OUTPUT == null || started == 0L) return;
        long elapsed = System.nanoTime() - started;
        Map<String, Object> sample = new LinkedHashMap<>();
        sample.put("sequence", SAMPLES.size());
        sample.put("wall_time_ms", wallTime);
        sample.put("duration_ns", elapsed);
        sample.put("workloads", new ArrayList<>(LABELS));
        SAMPLES.add(sample);
        started = 0L;
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent event) {
        if (OUTPUT == null) return;
        try {
            Map<String, Object> report = new LinkedHashMap<>();
            report.put("schema_version", 1);
            report.put("server_jvm_pid", ProcessHandle.current().pid());
            report.put("measurement", "ServerTickEvent.Pre to ServerTickEvent.Post; includes all server work in that tick");
            report.put("tick_budget_ns", 50_000_000L);
            report.put("samples", SAMPLES);
            Map<String, Object> workloads = new LinkedHashMap<>();
            LinkedHashSet<String> names = new LinkedHashSet<>();
            for (var row : SAMPLES) names.addAll((java.util.List<String>) row.get("workloads"));
            names.add("all_server_ticks");
            for (String name : names) {
                long[] values = SAMPLES.stream()
                    .filter(row -> name.equals("all_server_ticks") || ((java.util.List<?>)row.get("workloads")).contains(name))
                    .mapToLong(row -> (Long)row.get("duration_ns")).sorted().toArray();
                if (values.length == 0) continue;
                Map<String, Object> stats = new LinkedHashMap<>();
                stats.put("ticks", values.length);
                stats.put("median_ns", values[(int)Math.ceil(values.length * 0.50) - 1]);
                stats.put("p95_ns", values[(int)Math.ceil(values.length * 0.95) - 1]);
                stats.put("max_ns", values[values.length - 1]);
                stats.put("total_ns", java.util.Arrays.stream(values).sum());
                stats.put("over_budget_ticks", java.util.Arrays.stream(values).filter(ns -> ns > 50_000_000L).count());
                workloads.put(name, stats);
            }
            report.put("workloads", workloads);
            Path path = Path.of(OUTPUT);
            Files.createDirectories(path.toAbsolutePath().getParent());
            Files.writeString(path, new GsonBuilder().setPrettyPrinting().create().toJson(report) + "\n");
            System.out.println("SERVER_TICK_PROBE_V1 samples=" + SAMPLES.size() + " report=" + path);
        } catch (Exception failure) {
            throw new IllegalStateException("Could not write required server tick timings", failure);
        }
    }
}
