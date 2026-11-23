package com.xsxlabs.connectedwallsigns.mixin.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.xsxlabs.connectedwallsigns.WallSignGroup;
import com.xsxlabs.connectedwallsigns.WallSignGroupResolver;
import com.xsxlabs.connectedwallsigns.client.CanvasTextLayout;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.SignRenderer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.SignBlockEntity;
import net.minecraft.world.level.block.entity.SignText;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Client canvas hooks reconstructed from the original 1.21.1 mixin.
 * Kept client-only in the mixin configuration.
 */
@Mixin(SignRenderer.class)
public abstract class SignRendererMixin {
    private static final ThreadLocal<WallSignGroup> GROUP = new ThreadLocal<>();
    private static final ThreadLocal<TextContext> TEXT = new ThreadLocal<>();

    private record TextContext(WallSignGroup group, boolean front, float scale, double verticalOffset) {}

    @Inject(method = "render", at = @At("HEAD"))
    private void connectedWallSigns$start(SignBlockEntity sign, float partialTick,
            PoseStack pose, MultiBufferSource buffers, int light, int overlay, CallbackInfo ci) {
        if (sign.getLevel() == null) return;
        WallSignGroup group = WallSignGroupResolver.resolve(sign.getLevel(), sign.getBlockPos());
        if (!group.connected()) return;
        // Preserve the board model for every sign; only the text is shared.
        GROUP.set(group);
    }

    @Inject(method = "render", at = @At("RETURN"))
    private void connectedWallSigns$end(SignBlockEntity sign, float partialTick,
            PoseStack pose, MultiBufferSource buffers, int light, int overlay, CallbackInfo ci) {
        GROUP.remove();
    }

    @Inject(method = "renderSignText", at = @At("HEAD"), cancellable = true)
    private void connectedWallSigns$startText(BlockPos pos, SignText text, PoseStack pose,
            MultiBufferSource buffers, int light, int lineSpacing, int maxWidth,
            boolean front, CallbackInfo ci) {
        WallSignGroup group = GROUP.get();
        if (group == null || !group.connected()) return;
        if (!pos.equals(group.anchor())) {
            // Suppress duplicate text without cancelling the wooden board.
            ci.cancel();
            return;
        }
        pose.pushPose();
        CanvasTextLayout.Result layout = CanvasTextLayout.calculate(
                text, Minecraft.getInstance().font, lineSpacing, maxWidth);
        TEXT.set(new TextContext(group, front, Math.min(1.0f, layout.scale()), layout.verticalCenterOffset()));
    }

    @Inject(method = "translateSignText", at = @At("RETURN"))
    private void connectedWallSigns$positionText(PoseStack pose, boolean front, Vec3 offset,
            CallbackInfo ci) {
        TextContext context = TEXT.get();
        if (context == null || context.front() != front) return;
        // The shared text width is supplied by SignBlockEntityMixin:
        // getMaxTextLineWidth() already grows with the number of connected signs.
        // Move the text origin from the anchor sign to the center of the group.
        // Vanilla's sign text transform uses 1/64 block per text unit.
        double offsetPixels = context.group().centerHorizontalOffsetBlocks() * 64.0;
        pose.translate(front ? offsetPixels : -offsetPixels, 0, 0);
        pose.scale(context.scale(), context.scale(), context.scale());
        pose.translate(0, context.verticalOffset(), 0);
    }

    @Inject(method = "renderSignText", at = @At("RETURN"))
    private void connectedWallSigns$endText(BlockPos pos, SignText text, PoseStack pose,
            MultiBufferSource buffers, int light, int lineSpacing, int maxWidth,
            boolean front, CallbackInfo ci) {
        if (TEXT.get() != null) {
            TEXT.remove();
            pose.popPose();
        }
    }
}
