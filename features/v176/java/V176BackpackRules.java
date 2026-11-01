package dev.obsidiannetwork.backpack;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Server-side, dependency-free admission/transaction model for the three
 * storage cells of a Network Backpack. An ItemKey is the caller's exact,
 * stable item+component descriptor; never pass just the display name.
 *
 * Values and states are immutable. Simulated cable transfers, magnet pickup,
 * shift-click and real commits use the SAME insert/extract operations.
 *
 * This is a core rules module, not an item, GUI or block registration.
 */
public final class V176BackpackRules {
    public static final int CELL_SLOTS = 3;
    public static final int MAGNET_SLOTS = 1;
    public static final int VARIANTS = 24;
    public static final int TYPES_PER_CELL = 128;

    private V176BackpackRules() {}

    public enum FilterMode { WHITELIST, BLACKLIST }

    public record Magnet(boolean installed, boolean enabled,
                         FilterMode mode, Set<String> entries) {
        public Magnet {
            Objects.requireNonNull(mode);
            entries = Set.copyOf(Objects.requireNonNull(entries));
            if (!installed && enabled) throw new IllegalArgumentException("uninstalled magnet");
        }

        public boolean allows(String exactItemKey) {
            if (!installed || !enabled) return false;
            boolean listed = entries.contains(exactItemKey);
            return mode == FilterMode.WHITELIST ? listed : !listed;
        }
    }

    public record Cell(long capacity, Map<String, Long> stacks) {
        public Cell {
            if (capacity < 0) throw new IllegalArgumentException("negative cell capacity");
            stacks = Map.copyOf(Objects.requireNonNull(stacks));
            if (stacks.size() > TYPES_PER_CELL) throw new IllegalArgumentException("type limit");
            long used = 0L;
            for (var e : stacks.entrySet()) {
                if (e.getKey() == null || e.getKey().isBlank() || e.getValue() == null || e.getValue() <= 0)
                    throw new IllegalArgumentException("invalid stack");
                used = Math.addExact(used, e.getValue());
            }
            if (used > capacity) throw new IllegalArgumentException("cell over capacity");
        }

        public long used() {
            long sum = 0;
            for (long n : stacks.values()) sum = Math.addExact(sum, n);
            return sum;
        }

        public long free() { return capacity - used(); }
        public long count(String key) { return stacks.getOrDefault(key, 0L); }

        Cell with(String key, long count) {
            Map<String, Long> result = new HashMap<>(stacks);
            if (count == 0) result.remove(key);
            else result.put(key, count);
            return new Cell(capacity, result);
        }
    }

    /**
     * Exactly three real Cell positions. null means no cell installed.
     * No extra "backpack inventory" exists outside these cells.
     */
    public record State(List<Cell> cells, Magnet magnet, int color) {
        public State {
            Objects.requireNonNull(cells);
            Objects.requireNonNull(magnet);
            if (color < 1 || color > VARIANTS) throw new IllegalArgumentException("invalid variant");
            if (cells.size() != CELL_SLOTS) throw new IllegalArgumentException("exactly 3 slots required");
            cells = Collections.unmodifiableList(new ArrayList<>(cells));
        }

        public long capacity() {
            long sum = 0;
            for (Cell c : cells) if (c != null) sum = Math.addExact(sum, c.capacity());
            return sum;
        }

        public long used() {
            long sum = 0;
            for (Cell c : cells) if (c != null) sum = Math.addExact(sum, c.used());
            return sum;
        }

        public State withCells(List<Cell> replacements) { return new State(replacements, magnet, color); }
        public State withMagnet(Magnet replacement) { return new State(cells, replacement, color); }
    }

    public record Transfer(State state, long moved, long remainder) {
        public Transfer {
            if (moved < 0 || remainder < 0) throw new IllegalArgumentException("negative transfer");
        }
    }

    public static State empty(int color) {
        return new State(java.util.Arrays.asList(null, null, null),
            new Magnet(false, false, FilterMode.BLACKLIST, Set.of()), color);
    }

    /**
     * Place identical existing item types first, then open a new type in a
     * compatible cell. No item is inserted when cells are absent or full.
     */
    public static Transfer insert(State before, String exactItemKey, long amount) {
        Objects.requireNonNull(before);
        if (exactItemKey == null || exactItemKey.isBlank() || amount < 0)
            throw new IllegalArgumentException("invalid insert");
        if (amount == 0) return new Transfer(before, 0, 0);
        List<Cell> result = new ArrayList<>(before.cells());
        long remaining = amount;
        for (int phase = 0; phase < 2 && remaining > 0; phase++) {
            for (int i = 0; i < CELL_SLOTS && remaining > 0; i++) {
                Cell c = result.get(i);
                if (c == null || c.free() == 0) continue;
                boolean existing = c.stacks().containsKey(exactItemKey);
                if (phase == 0 && !existing) continue;
                if (phase == 1 && (existing || c.stacks().size() >= TYPES_PER_CELL)) continue;
                long insert = Math.min(remaining, c.free());
                result.set(i, c.with(exactItemKey, Math.addExact(c.count(exactItemKey), insert)));
                remaining -= insert;
            }
        }
        return new Transfer(before.withCells(result), amount - remaining, remaining);
    }

    /** The magnet and other input paths must leave the actual remainder outside. */
    public static Transfer magnetPickup(State before, String exactItemKey, long amount) {
        if (amount < 0) throw new IllegalArgumentException("negative pickup");
        if (!before.magnet().allows(exactItemKey)) return new Transfer(before, 0, amount);
        return insert(before, exactItemKey, amount);
    }

    /**
     * Bounded, non-destructive extraction. Return the new state only when the
     * calling server has actually committed the target transfer.
     */
    public static Transfer extract(State before, String exactItemKey, long wanted) {
        Objects.requireNonNull(before);
        if (exactItemKey == null || exactItemKey.isBlank() || wanted < 0)
            throw new IllegalArgumentException("invalid extract");
        if (wanted == 0) return new Transfer(before, 0, 0);
        List<Cell> result = new ArrayList<>(before.cells());
        long remaining = wanted;
        for (int i = 0; i < CELL_SLOTS && remaining > 0; i++) {
            Cell c = result.get(i);
            if (c == null) continue;
            long taken = Math.min(remaining, c.count(exactItemKey));
            if (taken > 0) {
                result.set(i, c.with(exactItemKey, c.count(exactItemKey) - taken));
                remaining -= taken;
            }
        }
        return new Transfer(before.withCells(result), wanted - remaining, remaining);
    }

    /** Safely replace/remove a cell. Existing contents must remain in that cell. */
    public static State replaceCell(State before, int slot, Cell replacement) {
        Objects.requireNonNull(before);
        if (slot < 0 || slot >= CELL_SLOTS) throw new IndexOutOfBoundsException(slot);
        Cell previous = before.cells().get(slot);
        if (previous != null && !previous.stacks().isEmpty())
            throw new IllegalStateException("empty cell contents before replacing or removing");
        List<Cell> next = new ArrayList<>(before.cells());
        next.set(slot, replacement);
        return before.withCells(next);
    }

    /** Only exact content keys are accepted; no recursive backpack storage. */
    public static boolean validItemKey(String key, String namespace) {
        return key != null && !key.isBlank() && namespace != null &&
            !key.startsWith(namespace + ":network_backpack");
    }

    public static Set<String> allDistinctKeys(State state) {
        Set<String> keys = new HashSet<>();
        for (Cell c : state.cells()) if (c != null) keys.addAll(c.stacks().keySet());
        return Set.copyOf(keys);
    }
}
