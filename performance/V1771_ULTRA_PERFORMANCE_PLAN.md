# 1.7.7.1 Ultra Performance — release gates and work plan

Base: branch 1.7.7 at commit 70b40f1c0e1fcb7f63526b4f79ab5d63a1bcb58c (B1551).
Version 1.7.8 feature development is deferred.

## Non-regression contract
- No intentional change to gameplay behavior, item/fluid/FE accounting, FE/t rates, priorities, filters, recipes, GUI behavior, network persistence, redstone behavior, or public compatibility.
- No TPS throttling disguised as optimization; preserve 20Hz transfer semantics and exact production totals.
- No stale energy endpoint/topology caches. Invalidate on placement/removal, side configuration, capability changes, chunk load/unload, dimension changes, and machine replacement.
- Preserve atomic transfers and rollback. Validate mixed modded energy networks and both Energy Cables and Cable Conduits.
- Performance claims require matched in-game measurements (baseline vs candidate), not CI timing alone.
- Each patch must be independently revertible; no merge/release on failing tests or observed regressions.

## Prioritized performance investigation
1. Energy Cable hot path: repeated graph traversal, neighbor/blockstate reads, capability lookups, transaction overhead, allocation.
2. Conduit Bundle and EnergyConduitTicker: scaling with cable length; topology rebuild and invalidation frequency; idle work.
3. SolarGeneratorBlockEntity: 64+ panels, generation/export, full buffers, sky checks, neighbor cache.
4. Network Storage controllers, importer/exporter, autocrafting, drives, crafting terminal and backpack.
5. Power Armor, armor station, reactor, Powerbank, wireless links, fluid and item conduits.
6. Client render paths: held multitool, armor overlays, GUIs, particles, block entities and hologram-ready infrastructure.
7. Network packets, serialization, memory allocations and GC pressure.

## Baseline scenarios (measure median/p95 MSPT, TPS, allocation and client FPS)
- 64 solar panels with normal Energy Cables and with Cable Conduits, each at 64/128/256 segments.
- Connected/disconnected, full/empty consumer buffers, powered/unpowered, chunk boundary and chunk reload.
- Powerbank + reactors + full/partially full machines; energy conservation and steady-state throughput.
- 100+ idle/active machines, large storage, autocrafting, multiple clients, held multitool.
- Repeated cable add/remove, mode toggles, dimension unload and server restart.

## Proposed /xsxperf
- Server-authoritative opt-in profiler with bounded overhead, configurable sample windows and permissions.
- Per-subsystem counts and timing: solar, energy cables, conduits, topology, storage, crafting, powerbank, reactor.
- Report server tick mean/median/p95 where reliable; avoid attributing overlapping inclusive samples as additive shares.
- Diagnostics disabled or minimal-overhead by default.

## Historical evidence (not current build proof)
See performance/SPARK_ENERGY_DIAGNOSIS.md and performance/SPARK_AFK_PROFILE_2026-10-18.md.
Historical inclusive samples implicate solar exports, energy cable transfers and conduit tickers; current B1551 requires fresh profiling.

## Delivery order
Baseline -> narrow patch -> compile and unit/integration tests -> same-world Spark/observable throughput benchmark -> user test -> next patch.
No feature work from 1.7.8 until performance release approved.
