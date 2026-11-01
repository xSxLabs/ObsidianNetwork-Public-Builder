package dev.obsidiannetwork.power;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

/**
 * Authorization and snapshot rules for the central Power Monitor.
 * Actual world adapters supply LIVE, same-network controllers/ports; no
 * untrusted client-provided metrics or target lists are accepted.
 */
public final class V176PowerMonitorRules {
    private V176PowerMonitorRules() {}
    public enum DeviceType { REACTOR, POWERBANK }
    public enum State { ACTIVE, OFF, UNFORMED, DISCONNECTED }
    public record Device(UUID id, String network, DeviceType type, String label,
                         String dimension, long position,
                         boolean online, boolean formed, boolean enabled,
                         long storedFe, long capacityFe, long inputFePerTick,
                         long outputFePerTick) {
        public Device {
            Objects.requireNonNull(id);
            Objects.requireNonNull(network);
            Objects.requireNonNull(type);
            Objects.requireNonNull(label);
            Objects.requireNonNull(dimension);
            if (network.isBlank()) throw new IllegalArgumentException("network");
            if (storedFe < 0 || capacityFe < 0 || storedFe > capacityFe
                || inputFePerTick < 0 || outputFePerTick < 0)
                throw new IllegalArgumentException("negative/invalid power");
        }
        public State state() {
            if (!online) return State.DISCONNECTED;
            if (!formed) return State.UNFORMED;
            return enabled ? State.ACTIVE : State.OFF;
        }
    }
    public static List<Device> visible(String network, List<Device> observed) {
        Objects.requireNonNull(network);
        Objects.requireNonNull(observed);
        List<Device> result = new ArrayList<>();
        for (Device entry : observed)
            if (entry.network().equals(network) && entry.online()) result.add(entry);
        result.sort(Comparator.comparing(Device::type).thenComparing(Device::label)
                    .thenComparing(Device::id));
        return List.copyOf(result);
    }
    /** Server-side guard before any per-reactor/per-powerbank on/off command. */
    public static boolean canToggle(String requestingNetwork, Device target,
                                    boolean authorized) {
        return authorized && target != null && target.online() && target.formed()
            && target.network().equals(requestingNetwork);
    }
    public static long totalInput(List<Device> devices) {
        long sum = 0L;
        for (Device d : devices) if (d.state() == State.ACTIVE)
            sum = Math.addExact(sum, d.inputFePerTick());
        return sum;
    }
    public static long totalOutput(List<Device> devices) {
        long sum = 0L;
        for (Device d : devices) if (d.state() == State.ACTIVE)
            sum = Math.addExact(sum, d.outputFePerTick());
        return sum;
    }
}
