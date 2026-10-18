# Spark: Wireless + Performance, 18 October 2026

## Provenance and limits

- Input: user-uploaded `NjeYDIr1Da.sparkprofile`, protobuf SamplerData (19,118,174 bytes).
- Recorded **2026-10-18 14:17:03–14:36:55 UTC** (16:17–16:36 Europe/Zurich); 23,499 ticks, one aggregated **Server thread**, 77,109 stack nodes; Java sampler interval 4,000 µs; 2 players; Minecraft 26.1.2 / NeoForge 26.1.2.106 / ObsidianNetwork metadata version 1.1.1.
- CRITICAL: Capture began **before** integrated CI Build #271 was triggered at 14:23 UTC. It **cannot verify the #271/#272 distributable**; the loaded JAR's SHA-256/name is not in this sampler metadata. Establish its hash first.
- All percentages below are **inclusive sampled time divided by MinecraftServer.tickServer (948,404 ms)**, not percentage of host CPU. Parent/child stacks overlap; do not sum nested percentages. Distinct sibling ticker paths may be summed for a rough sampled-work distribution only.
- No reproducible A/B run on identical workload/server has been captured. Do NOT claim a measured improvement/regression against #232/#269/#271.

## Recorded performance

- MSPT last 1 minute: mean **41.2351 ms**, median **34.0466 ms**, p95 **68.2696 ms**, max **174.382 ms**.
- MSPT last 5 minutes: mean **45.1138 ms**, median **34.3736 ms**, p95 **115.2699 ms**, max **389.1685 ms**.
- Final spark reported TPS 1m **20.2169**, 5m **19.2265**, 15m **19.6510**; minute windows vary down to ~18.5 TPS.
- A high 5m p95/max can cause visible spikes even when median is below 50ms.

## Highest confirmed server-thread paths (inclusive, relative to tickServer)

| Distinct sampled path | Inclusive ms | Tick-server share | Key expensive child |
|---|---:|---:|---|
| Obsidian SolarGeneratorBlockEntity.serverTick | 200,288 | 21.12% | EnergyCableBlockEntity$CableEnergyHandler.insert 195,020 (~97.4% of solar) |
| Powah SolarBlockEntity.postTick | 186,352 | 19.65% | Powah extractFromSides 182,452 then Obsidian EnergyCable insert 177,688 |
| Obsidian ConduitBundleBlockEntity.tick | 107,220 | 11.31% | EnergyConduitTicker.tick 99,440; cable extract 63,224 |
| Obsidian ImporterBlockEntity.serverTick | 38,836 | 4.09% | WorldTopologyBridge.runtimeForAccessory 29,804: TopologyBindingManager.stateAt and NetworkGraph.component |
| Obsidian ControllerBlockEntity.serverTick | 34,652 | 3.65% | MinecraftAutocraftingService.consumeReservedCraft 33,196; StorageNetwork.insertExact 21,840 and previewInsertExact 11,320 |
| WirelessPlayerCharging.tick | 1,724 | 0.18% | Curios charge 988, chargeOne 480 |
| WirelessNetworkBlockEntity.serverTick | 428 | 0.045% | Transaction.openRoot 152, commit 88, WirelessEnergyRuntime.pull 44 |
| Old WirelessChargerBlockEntity.serverTick | 1,756 | 0.19% | Reflection 1,260 |

Top cable-insert children **under Obsidian Solar** (do not add into solar percentage):
- ILevelExtension.getCapability 65,144 ms = 33.4% of that cable insert.
- EnergyCableBlockEntity.energyOpen 50,712 ms = 26.0%.
- Level.getBlockState 45,044 ms = 23.1%.
- EnergyCableBlockEntity.energyCable 13,936 ms = 7.1%.
The Powah-solar-to-Obsidian insert repeats the same ~34% capability / ~26% open / ~23% block-state pattern.

Key conduit ticker children: EnergyCableHandler.extract 63,224 ms (63.6% of EnergyConduitTicker), Transaction.openRoot 17,252 ms (17.3%), EnergyCableHandler.insert 8,816 ms (8.9%).

## Comparison with older Spark summary (different conditions)

The previous project Spark baseline `performance/SPARK_ENERGY_DIAGNOSIS.md` reports: 139 minutes; Obsidian Solar 21.09%, Conduit Bundle 20.89%, Powah→Obsidian cable 20.08%; tail 1m MSPT mean 58.7203 ms, p95 110.2987, max 688.9704. New sampling shows ~21.12% solar, ~11.31% conduit, ~19.65% Powah solar. **No controlled claim**: duration, load, sample time, JAR SHA and activity differ. Percentages can shift without any actual CPU improvement.

## Work prioritization (DO NOT lower Wireless FE rate merely to reduce tick frequency)

1. **EnergyCable insert/extract hot path**. Measure and investigate repeated BFS neighbor capability, block-state and cable openness checks on *the same validated built JAR*. Consider NeoForge BlockCapabilityCache with comprehensive invalidation (capability/BE replacement, block placement/break, faces/modes, chunk unload/reload), not unsafe long-lived direct handler caching. Preserve FE conservation/transactions, no infinite energy.
2. **Powah interaction**. Compare Powah solar on/off while preserving solar/Obsidian network density. Profile direct Powah→Obsidian versus other cable.
3. **Conduit ticker**. Transaction/capability frequency; keep real endpoint guards and sided transfer; verify performance gains via paired Spark MSPT p95/p99.
4. **Importer topology**. WorldTopologyBridge.runtimeForAccessory resolves graph/component frequently; require cache invalidation across topology mutation, network split/merge/unload and cross-dimension.
5. **Autocraft consumption and inserts**. Profiling confirms StorageNetwork.insertExact and previewInsertExact under consumeReservedCraft. Avoid changing reservation/cancellation/rollback semantics. GUI spikes must be sampled separately with deliberately opened GUI.
6. **Wireless**. Small sampled share in this capture, not the primary regression path. Retain 20Hz 64k FE/t receiver and legitimate tool-only charging. Repeat under 10/50/100 active receivers if wireless density is in question.

## Controlled next-run acceptance

- Record exact JAR filename + SHA-256 from client/server and GitHub artifact. Baseline before/after on identical world, same players and machine load.
- Separate phases: idle no GUI; Obsidian solar+energy cables; Powah solar→Obsidian cables; conduit network; wireless devices (0/10/50/100); charging enabled/disabled; small and 50-drive controller opening; autocrafter opening; mass crafting/deposit.
- At least 60–120 sec per sustained workload phase; record TPS, MSPT mean/p95/p99/max, lag spikes/GC and Spark server-thread profile. Keep item/FE conservation tests and dedicated save/restart gates.
- **Build lock**: no workflow run or test JAR from this diagnosis alone; user explicitly controls requests to build.
