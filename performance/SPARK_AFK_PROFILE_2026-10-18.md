# AFK Spark profile — 2026-10-18, post Drive16 client candidate

Source: user-uploaded `Z0twDwO83Q.sparkprofile` (16,225,838-byte protobuf). Recorded **2026-10-18 16:22:41.739–16:40:44.884 UTC**, approx. 18:22–18:40 Europe/Zurich; **21,655 ticks**, one aggregated Server thread, **67,774 stack nodes**, sample interval **4 ms**, 2 players. User was largely AFK.

Critical identification caveat: profile metadata does not include the installed executable JAR SHA-256. Capture began before Build #278 CI completed. Do not infer that #278 was installed; the observed `cachedEnergyEndpoint` method shows that the post-#273 ENERGY endpoint optimization was present, and the user states the Drive-fix JAR was in use.

## AFK tick health

- TPS 1m: **19.9998**; 5m: **20.0001**; 15m: **20.0000**.
- MSPT last 1m: mean **36.585**, median **33.399**, p95 **51.634**, max **114.882** ms.
- MSPT last 5m: mean **36.226**, median **32.717**, p95 **52.218**, max **397.648** ms.
- `MinecraftServer.tickServer` aggregated sampled time: **610,460 ms** across the profile. All percentages below are **inclusive samples divided by this path** and overlap for parent/child stacks, so they must not be summed as additive CPU shares.

## Top costs

| Path | Inclusive sampled milliseconds | % of tickServer | Main subcost |
|---|---:|---:|---|
| Obsidian `SolarGeneratorBlockEntity.serverTick` | 111,668 | 18.29 | `EnergyCable...insert`: 107,320 |
| Powah `SolarBlockEntity.postTick` | 73,028 | 11.96 | side extraction → ENERGY cable |
| Obsidian `ConduitBundleBlockEntity.tick` | 83,348 | 13.65 | `EnergyConduitTicker.tick`: 75,452 |
| Obsidian `ImporterBlockEntity.serverTick` | 34,648 | 5.68 | accessory runtime lookup: 27,692 |
| Obsidian `ExporterBlockEntity.serverTick` | 30,284 | 4.96 | periodic network transfer paths |
| `WorldTopologyBridge.runtimeForAccessory`, summed across contexts | 54,912 | 8.99 | repeated `stateAt`, `NetworkGraph.component` |
| `EnergyCable...insert`, summed across contexts | 206,472 | 33.82 | state/cut checks, live endpoint lookup; nested in solar/Powah |
| `WirelessNetworkBlockEntity.serverTick` | 488 | 0.08 | very small relative share |

Energy cable methods summed over all sampled occurrences (nested/overlapping in parent paths): `energyOpen` **72,956 ms**; `liveBoundaryEnergy` **64,336 ms**; `cachedEnergyEndpoint` **23,060 ms**; `EnergyCable...extract` **51,028 ms**. Cache lifecycle remains essential; no reduction in 20Hz FE budgets permitted to mask idle work.

The latest AFK capture does not reproduce high-volume terminal clicks or active autocraft; use the preceding `performance/SPARK_WIRELESS_PROFILE_2026-10-18.md` for previous observations of `MinecraftAutocraftingService.consumeReservedCraft` (including `StorageNetwork.insertExact` and `previewInsertExact`). User confirms those rapid-crafting symptoms remain. Never call this AFK capture proof of a crafting fix.

## Build #279 optimization choice

1. **Importer/Exporter topology:** enable the previously implemented fail-closed `perf-accessory-topology-rebuild-index.py`, indexing only active controller POSITIONS on successful graph rebuild. Invalidate/fallback on dirty batch, revision mismatch, rebuild failure or unexpected missing runtime. Aims at a measured 8.99% lookup path, not an asserted 8.99% server improvement.
2. **Autocraft duplicated preview:** enable `perf-autocraft-single-exact-insert-preflight.py` on reserved immutable craft outputs only. Public `insertExact`, per-cell exact accounting and all rollback semantics retained.
3. **Explicit release gates:** 89+ Python tests, pre/post 50 real drives and 800 cells, 16 real GUI cells after patch, optional Curios GameTests, same-world dedicated process restart, final JAR bytecode/GUI contract check. No claim of no regression without in-game exercise.
4. **Additional independent binary check:** compare unmodified critical class SHA-256 for StorageDriveBlockEntity, DriveMenu/DriveContainer, DriveScreen, WirelessPlayerCharging and WirelessNetworkBlockEntity against the frozen #277 JAR, alongside the existing compiled-JAR bytecode contract. This comparison should be performed on the built artifact before offering it for in-game tests.

Next profile recommendation: same world and hardware, old and new exact JAR SHA, 60–120-second isolated stages for idle, solar→cables, Powah→cables, 50-drive GUI, shift-crafting, mass deposit and active autocrafting. Report p95/p99 tick, GC and full inventory contents on world backup.
