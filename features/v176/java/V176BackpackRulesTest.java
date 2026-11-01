package dev.obsidiannetwork.backpack;

import java.util.List;
import java.util.Map;
import java.util.Set;

public final class V176BackpackRulesTest {
    private static void yes(boolean b) { if (!b) throw new AssertionError(); }
    private static V176BackpackRules.Cell cell(long cap) {
        return new V176BackpackRules.Cell(cap, Map.of());
    }
    public static void main(String[] args) {
        var empty = V176BackpackRules.empty(24);
        yes(empty.capacity() == 0 && empty.used() == 0);
        var base = empty.withCells(List.of(cell(256_000), cell(256_000), cell(256_000)));
        yes(base.capacity() == 768_000);
        var a = V176BackpackRules.insert(base, "minecraft:stone|components={}", 800_000);
        yes(a.moved() == 768_000 && a.remainder() == 32_000);
        yes(a.state().used() == 768_000);
        yes(base.used() == 0); // simulation does not mutate the source
        var b = V176BackpackRules.extract(a.state(), "minecraft:stone|components={}", 300_000);
        yes(b.moved() == 300_000 && b.state().used() == 468_000);
        yes(a.state().used() == 768_000);
        var off = V176BackpackRules.magnetPickup(base, "minecraft:diamond", 17);
        yes(off.moved() == 0 && off.remainder() == 17);
        var allowed = new V176BackpackRules.Magnet(true, true,
            V176BackpackRules.FilterMode.WHITELIST, Set.of("minecraft:diamond"));
        var white = base.withMagnet(allowed);
        yes(V176BackpackRules.magnetPickup(white, "minecraft:diamond", 17).moved() == 17);
        yes(V176BackpackRules.magnetPickup(white, "minecraft:dirt", 17).moved() == 0);
        var blocked = new V176BackpackRules.Magnet(true, true,
            V176BackpackRules.FilterMode.BLACKLIST, Set.of("minecraft:diamond"));
        var black = white.withMagnet(blocked);
        yes(V176BackpackRules.magnetPickup(black, "minecraft:diamond", 17).moved() == 0);
        yes(V176BackpackRules.magnetPickup(black, "minecraft:dirt", 17).moved() == 17);
        boolean refused = false;
        try { V176BackpackRules.replaceCell(a.state(), 0, null); }
        catch (IllegalStateException expected) { refused = true; }
        yes(refused);
        var removed = V176BackpackRules.replaceCell(base, 1, null);
        yes(removed.capacity() == 512_000 && removed.cells().get(1) == null);
        for (int i = 1; i <= 24; i++) yes(V176BackpackRules.empty(i).color() == i);
        yes(!V176BackpackRules.validItemKey("obsidiannetwork:network_backpack_mk1", "obsidiannetwork"));
        System.out.println("V176_BACKPACK_RULES_3_CELLS_24_VARIANTS_MAGNET_TRANSACTIONS_PASS");
    }
}
