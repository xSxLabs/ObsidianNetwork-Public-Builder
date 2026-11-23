package com.xsxlabs.connectedwallsigns;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.WallSignBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Initial Forge 1.20.1 horizontal grouping implementation.
 * Original JAR uses additional tick caching and text propagation; those are not yet ported.
 */
public final class WallSignGroupResolver {
    private WallSignGroupResolver() {}

    public static WallSignGroup resolve(Level level, BlockPos pos) {
        BlockState origin = level.getBlockState(pos);
        if (!(origin.getBlock() instanceof WallSignBlock)) {
            return new WallSignGroup(List.of(pos), pos, Direction.NORTH, Direction.WEST, 1, 1);
        }
        Direction facing = origin.getValue(WallSignBlock.FACING);
        Direction right = facing.getClockWise();
        BlockPos leftmost = pos;
        for (int i = 0; i < 63; i++) {
            BlockPos next = leftmost.relative(right.getOpposite());
            if (!matches(level, next, facing)) break;
            leftmost = next;
        }
        List<BlockPos> members = new ArrayList<>();
        BlockPos cursor = leftmost;
        for (int i = 0; i < 64 && matches(level, cursor, facing); i++) {
            members.add(cursor.immutable());
            cursor = cursor.relative(right);
        }
        return new WallSignGroup(members, leftmost.immutable(), facing, right, members.size(), 1);
    }

    private static boolean matches(Level level, BlockPos pos, Direction facing) {
        if (!level.hasChunkAt(pos)) return false;
        BlockState state = level.getBlockState(pos);
        return state.getBlock() instanceof WallSignBlock && state.getValue(WallSignBlock.FACING) == facing;
    }
}
