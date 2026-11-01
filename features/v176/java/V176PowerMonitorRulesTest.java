package dev.obsidiannetwork.power;
import java.util.List;
import java.util.UUID;

public final class V176PowerMonitorRulesTest {
    private static void yes(boolean test) { if(!test) throw new AssertionError(); }
    public static void main(String[] args) {
        var reactor = new V176PowerMonitorRules.Device(UUID.randomUUID(), "network-A",
          V176PowerMonitorRules.DeviceType.REACTOR, "Reactor A", "minecraft:overworld", 1,
          true, true, true, 100, 1000, 50, 150);
        var bank = new V176PowerMonitorRules.Device(UUID.randomUUID(), "network-A",
          V176PowerMonitorRules.DeviceType.POWERBANK, "Powerbank B", "minecraft:overworld", 2,
          true, true, false, 500, 1000, 500, 0);
        var foreign = new V176PowerMonitorRules.Device(UUID.randomUUID(), "network-B",
          V176PowerMonitorRules.DeviceType.REACTOR, "Private Reactor", "minecraft:overworld", 3,
          true, true, true, 80, 1000, 100, 200);
        var visible = V176PowerMonitorRules.visible("network-A", List.of(foreign, bank, reactor));
        yes(visible.size() == 2);
        yes(V176PowerMonitorRules.totalOutput(visible) == 150);
        yes(V176PowerMonitorRules.totalInput(visible) == 50);
        yes(V176PowerMonitorRules.canToggle("network-A", bank, true));
        yes(!V176PowerMonitorRules.canToggle("network-A", foreign, true));
        yes(!V176PowerMonitorRules.canToggle("network-A", bank, false));
        yes(bank.state() == V176PowerMonitorRules.State.OFF);
        System.out.println("V176_POWER_MONITOR_NETWORK_ISOLATION_IO_RULES_PASS");
    }
}
