package com.xsxlabs.connectedwallsigns.client;

import net.minecraft.client.gui.Font;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.entity.SignText;

/**
 * Port of the original SignRendererMixin.calculateTextLayout bytecode.
 * Pure layout helper; not yet connected to the Forge 1.20.1 renderer.
 */
public final class CanvasTextLayout {
    private CanvasTextLayout() {}

    public record Result(float scale, double verticalCenterOffset) {}

    public static Result calculate(SignText text, Font font, int lineSpacing, int maxWidth) {
        Component[] lines = text.getMessages(false);
        int first = -1;
        int last = -1;
        int widest = 0;
        for (int i = 0; i < lines.length; i++) {
            Component line = lines[i];
            if (line == null || line.getString().isBlank()) continue;
            if (first < 0) first = i;
            last = i;
            widest = Math.max(widest, font.width(line));
        }
        if (first < 0) return new Result(1.0f, 0.0);
        int usedLines = Math.max(1, last - first + 1);
        int totalHeight = 9 + Math.max(0, usedLines - 1) * lineSpacing;
        float heightScale = 45.0f / totalHeight;
        float widthScale = widest <= 0 ? heightScale : (float) maxWidth / widest;
        float scale = Math.max(0.01f, Math.min(heightScale, widthScale));
        double middleLine = (first + last) * 0.5;
        double offset = (1.5 - middleLine) * lineSpacing;
        return new Result(scale, offset);
    }
}
