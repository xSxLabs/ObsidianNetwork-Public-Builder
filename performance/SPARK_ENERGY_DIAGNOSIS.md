# Spark ENERGY investigation, 2026-10-17

The user provided a 42,075,318-byte Spark protobuf sampler file, decoded
locally (never uploaded). Minecraft 26.1.2; NeoForge 26.1.2.106;
server thread sampled for 139 minutes, 73,271 stack trace nodes,
161,280 total server ticks.

CRITICAL SOURCE NOTE: the profile identifies installed mod filename
"xSxLabs-Network-Storage-1.1.1 final performance v2.jar".
This is NOT proof of identical SHA-256 to public Builder #215; compare
binaries before attributing measured differences to Builder builds.

Inclusive time percentages on the sampled server thread:
SolarGeneratorBlockEntity.serverTick: 21.09%; child CableEnergyHandler.insert
20.66% (getCapability 7.80%, energyOpen 3.78%, energyCable 3.50%,
getBlockState 3.30%). ConduitBundleBlockEntity.tick: 20.89%;
child EnergyConduitTicker.tick 18.81% (CableEnergyHandler.extract 12.14%,
Transaction.openRoot 2.74%, ConduitTopology.invalidateIfChanged 1.78%).
Direct Powah-to-Obsidian CableEnergyHandler.insert: 20.08%.
ExporterBlockEntity.serverTick: 2.57%; ImporterBlockEntity.serverTick:
1.78%. Outside Obsidian: SophisticatedCore ItemStackKey.clearCache
10.05% SELF time under server tick-end handler.

Inclusive parent/child figures must NOT be added. None are proof
of actual MSPT saved by a particular patch.

Initial safe modification: hoist the constant Direction.values() lookup
and ENERGY_CABLE registry block lookup out of each inner BFS loop. The
same per-call BFS, capability queries, amounts, transactions and cable
cut/connection tests are preserved. This is NOT a replacement for
proper topology and NeoForge capability caching.

For dramatic gains, next test a topology/endpoint cache with complete
invalidation across face mode changes, cable placement/destruction,
adjacent block/capability replacement, chunks unloading/reloading, and
transactions. Prefer NeoForge BlockCapabilityCache to raw handler
caching, and require controlled real Powah+Obsidian energy benchmarking.
Do not publish to stable until user GUI and mixed-network tests pass.
