package com.xsxlabs.connectedwallsigns.mixin;

import com.xsxlabs.connectedwallsigns.WallSignGroup;
import com.xsxlabs.connectedwallsigns.WallSignGroupResolver;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.SignBlockEntity;
import net.minecraft.world.level.block.entity.SignText;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Server text sharing reconstructed from the original 1.21.1 mixin bytecode.
 * Verify target method signatures against Forge 1.20.1 before release.
 */
@Mixin(SignBlockEntity.class)
public abstract class SignBlockEntityMixin extends BlockEntity {
    private static final ThreadLocal<Boolean> INTERNAL = ThreadLocal.withInitial(() -> false);

    protected SignBlockEntityMixin(BlockPos pos, BlockState state) {
        super(null, pos, state);
    }

    @Inject(method = "getText", at = @At("RETURN"), cancellable = true)
    private void connectedWallSigns$getSharedText(boolean front, CallbackInfoReturnable<SignText> cir) {
        Level world = this.level;
        if (INTERNAL.get() || world == null) return;
        WallSignGroup group = WallSignGroupResolver.resolve(world, worldPosition);
        if (!group.connected()) return;
        INTERNAL.set(true);
        try {
            SignText fallback = cir.getReturnValue();
            for (BlockPos member : group.members()) {
                if (world.getBlockEntity(member) instanceof SignBlockEntity sign) {
                    SignText candidate = sign.getText(front);
                    if (hasVisibleText(candidate)) {
                        cir.setReturnValue(candidate);
                        return;
                    }
                    fallback = candidate;
                }
            }
            cir.setReturnValue(fallback);
        } finally {
            INTERNAL.remove();
        }
    }

    @Inject(method = "setText", at = @At("HEAD"), cancellable = true)
    private void connectedWallSigns$replicateText(SignText text, boolean front,
            CallbackInfoReturnable<Boolean> cir) {
        Level world = this.level;
        if (INTERNAL.get() || world == null) return;
        WallSignGroup group = WallSignGroupResolver.resolve(world, worldPosition);
        if (!group.connected()) return;
        boolean changed = false;
        INTERNAL.set(true);
        try {
            for (BlockPos member : group.members()) {
                if (world.getBlockEntity(member) instanceof SignBlockEntity sign) {
                    changed |= sign.setText(text, front);
                    sign.setChanged();
                    BlockState state = world.getBlockState(member);
                    world.sendBlockUpdated(member, state, state, 3);
                }
            }
        } finally {
            INTERNAL.remove();
        }
        cir.setReturnValue(changed);
    }

    @Inject(method = "getMaxTextLineWidth", at = @At("RETURN"), cancellable = true)
    private void connectedWallSigns$canvasWidth(CallbackInfoReturnable<Integer> cir) {
        if (level == null) return;
        WallSignGroup group = WallSignGroupResolver.resolve(level, worldPosition);
        if (group.connected()) {
            cir.setReturnValue(Math.max(1, Math.round((float) cir.getReturnValue()
                    * group.width() / Math.max(1, group.height()))));
        }
    }

    private static boolean hasVisibleText(SignText text) {
        if (text == null) return false;
        for (Component line : text.getMessages(false)) {
            if (!line.getString().isBlank()) return true;
        }
        return false;
    }
}
