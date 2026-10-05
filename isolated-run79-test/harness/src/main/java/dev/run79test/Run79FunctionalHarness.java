package dev.run79test;

import dev.obsidiannetwork.blockentity.FacadeCable;
import dev.obsidiannetwork.blockentity.MultiCableBlockEntity;
import dev.obsidiannetwork.blockentity.NetworkTeleporterBlockEntity;
import dev.obsidiannetwork.blockentity.ImporterBlockEntity;
import dev.obsidiannetwork.blockentity.ExporterBlockEntity;
import dev.obsidiannetwork.blockentity.FluidPortBlockEntity;
import net.neoforged.fml.common.Mod;

@Mod(Run79FunctionalHarness.MODID)
public final class Run79FunctionalHarness {
    public static final String MODID = "run79test";
    public Run79FunctionalHarness() {
        // Compile-time contract checks against the exact Run 79 jar.
        Class<?>[] required = {
            MultiCableBlockEntity.class,
            NetworkTeleporterBlockEntity.class,
            ImporterBlockEntity.class,
            ExporterBlockEntity.class,
            FluidPortBlockEntity.class,
            FacadeCable.class
        };
        System.out.println("[RUN79-HARNESS] loaded contracts=" + required.length);
    }
}
