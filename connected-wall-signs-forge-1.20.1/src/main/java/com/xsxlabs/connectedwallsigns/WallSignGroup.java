package com.xsxlabs.connectedwallsigns;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;

/** Immutable group geometry for a contiguous horizontal row of wall signs. */
public record WallSignGroup(List<BlockPos> members, BlockPos anchor,
                            Direction facing, Direction right, int width, int height) {
    public WallSignGroup {
        members = List.copyOf(members);
    }
    public boolean connected() { return members.size() > 1; }
    public double centerHorizontalOffsetBlocks() { return (width - 1) / 2.0; }
    public double centerVerticalOffsetBlocks() { return (height - 1) / 2.0; }
}
