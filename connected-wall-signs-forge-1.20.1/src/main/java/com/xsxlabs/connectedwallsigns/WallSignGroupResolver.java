package com.xsxlabs.connectedwallsigns;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.WallSignBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * Reconstructed from the supplied 1.21.1 JAR's WallSignGroupResolver bytecode.
 * Connected signs must have identical facing and form a complete horizontal rectangle.
 * Deliberately no caching yet: correctness first, then benchmark tick-local caching.
 */
public final class WallSignGroupResolver {
    private static final int MAX_GROUP_SIZE = 64;
    private WallSignGroupResolver() {}

    public static WallSignGroup resolve(Level level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (!(state.getBlock() instanceof WallSignBlock)
                || !state.hasProperty(BlockStateProperties.HORIZONTAL_FACING)) {
            return singleton(pos, Direction.NORTH);
        }
        Direction facing = state.getValue(BlockStateProperties.HORIZONTAL_FACING);
        Direction right = facing.getCounterClockWise();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        Set<BlockPos> visited = new HashSet<>();
        queue.add(pos.immutable());
        while (!queue.isEmpty()) {
            BlockPos current = queue.removeFirst();
            if (!visited.add(current)) continue;
            if (visited.size() > MAX_GROUP_SIZE) return singleton(pos, facing);
            addIfMatching(level, queue, visited, current.relative(right), facing);
            addIfMatching(level, queue, visited, current.relative(right.getOpposite()), facing);
        }
        if (visited.size() == 1) return singleton(pos, facing);
        int min = Integer.MAX_VALUE, max = Integer.MIN_VALUE;
        for (BlockPos member : visited) {
            int local = (member.getX() - pos.getX()) * right.getStepX()
                    + (member.getZ() - pos.getZ()) * right.getStepZ();
            min = Math.min(min, local);
            max = Math.max(max, local);
        }
        int width = max - min + 1;
        if (width != visited.size()) return singleton(pos, facing);
        BlockPos anchor = pos.relative(right, min);
        List<BlockPos> members = new ArrayList<>(width);
        for (int i = 0; i < width; i++) {
            BlockPos member = anchor.relative(right, i);
            if (!visited.contains(member)) return singleton(pos, facing);
            members.add(member.immutable());
        }
        return new WallSignGroup(members, anchor.immutable(), facing, right, width, 1);
    }

    private static void addIfMatching(Level level, ArrayDeque<BlockPos> queue,
            Set<BlockPos> visited, BlockPos candidate, Direction facing) {
        if (visited.contains(candidate) || !level.hasChunkAt(candidate)) return;
        BlockState state = level.getBlockState(candidate);
        if (state.getBlock() instanceof WallSignBlock
                && state.hasProperty(BlockStateProperties.HORIZONTAL_FACING)
                && state.getValue(BlockStateProperties.HORIZONTAL_FACING) == facing) {
            queue.add(candidate.immutable());
        }
    }

    private static WallSignGroup singleton(BlockPos pos, Direction facing) {
        return new WallSignGroup(List.of(pos.immutable()), pos.immutable(),
                facing, facing.getCounterClockWise(), 1, 1);
    }
}
