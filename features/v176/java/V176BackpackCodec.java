package dev.obsidiannetwork.backpack;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

/**
 * Lossless versioned backpack payload, transportable inside a registered
 * ItemStack data component. The host adapter must store the bytes on the
 * ACTUAL backpack ItemStack, not in a global transient inventory.
 */
public final class V176BackpackCodec {
    public static final int FORMAT = 1;
    public static final int MAX_BYTES = 1_048_576;
    public static final int MAX_MAGNET_FILTERS = 54;
    private static final int MAGIC = 0x58534250; // XSBP
    private V176BackpackCodec() {}

    public static byte[] encode(V176BackpackRules.State state) {
        Objects.requireNonNull(state);
        try {
            var buf = new ByteArrayOutputStream();
            var out = new DataOutputStream(buf);
            out.writeInt(MAGIC);
            out.writeInt(FORMAT);
            out.writeInt(state.color());
            var magnet = state.magnet();
            out.writeBoolean(magnet.installed());
            out.writeBoolean(magnet.enabled());
            out.writeByte(magnet.mode().ordinal());
            if (magnet.entries().size() > MAX_MAGNET_FILTERS)
                throw new IllegalArgumentException("magnet filter overflow");
            out.writeShort(magnet.entries().size());
            for (String key : new java.util.TreeSet<>(magnet.entries())) out.writeUTF(key);
            for (var cell : state.cells()) {
                out.writeBoolean(cell != null);
                if (cell == null) continue;
                out.writeLong(cell.capacity());
                out.writeShort(cell.stacks().size());
                for (var entry : new TreeMap<>(cell.stacks()).entrySet()) {
                    out.writeUTF(entry.getKey());
                    out.writeLong(entry.getValue());
                }
            }
            out.flush();
            byte[] result = buf.toByteArray();
            if (result.length > MAX_BYTES)
                throw new IllegalArgumentException("payload too large");
            return result;
        } catch (IOException e) {
            throw new IllegalStateException("unable to encode backpack", e);
        }
    }

    public static V176BackpackRules.State decode(byte[] encoded) {
        if (encoded == null || encoded.length < 16 || encoded.length > MAX_BYTES)
            throw new IllegalArgumentException("invalid payload length");
        try {
            var in = new DataInputStream(new ByteArrayInputStream(encoded));
            if (in.readInt() != MAGIC || in.readInt() != FORMAT)
                throw new IllegalArgumentException("unknown backpack format");
            int color = in.readInt();
            boolean installed = in.readBoolean();
            boolean enabled = in.readBoolean();
            int mode = in.readUnsignedByte();
            var modes = V176BackpackRules.FilterMode.values();
            if (mode >= modes.length) throw new IllegalArgumentException("magnet mode");
            int count = in.readUnsignedShort();
            if (count > MAX_MAGNET_FILTERS) throw new IllegalArgumentException("filter count");
            var filters = new java.util.HashSet<String>();
            for (int i = 0; i < count; i++)
                if (!filters.add(in.readUTF())) throw new IllegalArgumentException("duplicate filter");
            var magnet = new V176BackpackRules.Magnet(installed, enabled, modes[mode], filters);
            List<V176BackpackRules.Cell> cells = new ArrayList<>(3);
            for (int slot = 0; slot < V176BackpackRules.CELL_SLOTS; slot++) {
                if (!in.readBoolean()) { cells.add(null); continue; }
                long capacity = in.readLong();
                int types = in.readUnsignedShort();
                if (types > V176BackpackRules.TYPES_PER_CELL)
                    throw new IllegalArgumentException("type count");
                Map<String, Long> stacks = new HashMap<>();
                for (int i = 0; i < types; i++) {
                    String key = in.readUTF();
                    long value = in.readLong();
                    if (stacks.putIfAbsent(key, value) != null)
                        throw new IllegalArgumentException("duplicate item key");
                }
                cells.add(new V176BackpackRules.Cell(capacity, stacks));
            }
            if (in.available() != 0) throw new IllegalArgumentException("trailing payload data");
            return new V176BackpackRules.State(cells, magnet, color);
        } catch (IOException e) {
            throw new IllegalArgumentException("corrupt backpack storage data", e);
        }
    }
}
