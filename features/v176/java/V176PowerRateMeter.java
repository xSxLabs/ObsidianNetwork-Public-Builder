package dev.obsidiannetwork.power;

import java.util.Arrays;

/** Rolling 20-tick REAL committed FE transfers; no client-provided values. */
public final class V176PowerRateMeter {
    private final long[] ticks = new long[20];
    private final long[] inputs = new long[20];
    private final long[] outputs = new long[20];

    public V176PowerRateMeter() { Arrays.fill(ticks, Long.MIN_VALUE); }
    public synchronized void committed(long gameTick, long incoming, long outgoing) {
        if (incoming < 0 || outgoing < 0) throw new IllegalArgumentException("negative IO");
        int slot = Math.floorMod(gameTick, 20);
        if (ticks[slot] != gameTick) {
            ticks[slot] = gameTick;
            inputs[slot] = 0L;
            outputs[slot] = 0L;
        }
        inputs[slot] = Math.addExact(inputs[slot], incoming);
        outputs[slot] = Math.addExact(outputs[slot], outgoing);
    }
    public synchronized long inputPerTick(long now) {
        long sum = 0L;
        for (int i = 0; i < 20; i++)
            if (ticks[i] <= now && ticks[i] > now - 20)
                sum = Math.addExact(sum, inputs[i]);
        return sum / 20L;
    }
    public synchronized long outputPerTick(long now) {
        long sum = 0L;
        for (int i = 0; i < 20; i++)
            if (ticks[i] <= now && ticks[i] > now - 20)
                sum = Math.addExact(sum, outputs[i]);
        return sum / 20L;
    }
}
