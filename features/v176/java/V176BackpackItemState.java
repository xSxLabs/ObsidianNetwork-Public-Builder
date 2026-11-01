package dev.obsidiannetwork.backpack;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

/**
 * Bridges the exact, versioned 3-cell snapshot to the real backpack ItemStack.
 * Writes only our nested payload; unrelated custom-data keys are preserved.
 * No global/static inventory or player-location keyed inventory is used.
 */
public final class V176BackpackItemState {
    private V176BackpackItemState() {}
    private static final String KEY = "xsxlabs_backpack_v176";

    public static V176BackpackRules.State read(ItemStack stack) {
        if (!(stack.getItem() instanceof NetworkBackpackItem bag))
            throw new IllegalArgumentException("not a Network Backpack");
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        var bytes = tag.getByteArray(KEY);
        if (bytes.isEmpty()) return V176BackpackRules.empty(bag.visualTier());
        var state = V176BackpackCodec.decode(bytes.get());
        if (state.color() != bag.visualTier())
            throw new IllegalStateException("backpack data/variant mismatch");
        return state;
    }

    public static void write(ItemStack stack, V176BackpackRules.State state) {
        if (!(stack.getItem() instanceof NetworkBackpackItem bag))
            throw new IllegalArgumentException("not a Network Backpack");
        if (bag.visualTier() != state.color())
            throw new IllegalArgumentException("cannot swap backpack color when saving");
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putByteArray(KEY, V176BackpackCodec.encode(state));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    public static V176BackpackRules.Transfer insert(ItemStack bag, String itemKey, long amount) {
        var moved = V176BackpackRules.insert(read(bag), itemKey, amount);
        if (moved.moved() > 0) write(bag, moved.state());
        return moved;
    }
    public static V176BackpackRules.Transfer extract(ItemStack bag, String itemKey, long wanted) {
        var moved = V176BackpackRules.extract(read(bag), itemKey, wanted);
        if (moved.moved() > 0) write(bag, moved.state());
        return moved;
    }
}
