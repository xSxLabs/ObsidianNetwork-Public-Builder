# ITEM conduit process restart

Run after the final source patches, using Java 25 and the reconstructed NeoForge
Gradle project:

```sh
python3 tests/integration/item_conduit_restart.py --project work --output dist/item-conduit-restart.json
```

The harness starts and fully stops two dedicated server JVMs, reusing the same
world directory. It refuses to erase an existing test world or reuse old reports.
Each phase must finish normally, emit a successful probe result, and log both
server shutdown and saving chunks. A timeout or missing result fails the gate.
The combined JSON records both JVM IDs and start times, item inventories,
configuration, endpoint counts, capability availability, chunk state, and hashes
of level.dat and region files after each stop.

Four routes cross the x=15/16 chunk boundary: three bundles, three standalone
ITEM cables, bundle/standalone/bundle, and standalone/bundle/standalone. Each
route connects two chests; the destination already contains 37 cobblestone.
Before restart the probe sends five diamonds and three emeralds. The next JVM
checks persisted inventories and GUI/runtime modes before adding seven gold
ingots and nine redstone. Every source must drain and every destination must
match the exact expected inventory. The second JVM also removes each route's
middle conduit, proves that two coal stay in the source for 60 ticks, reconnects
the route, and checks the final exact inventory.

The test-only subscriber uses ordinary block-entity ticking and capability
transfers. It never calls a conduit ticker directly, reloads NBT into replacement
block entities, or resets a GameTest world. The subscriber is removed after the
test, including generated classes. Final artifact validation must independently
reject any `dev/obsidiannetwork/restarttest/` entry in the packaged JAR.

Coverage is limited to vanilla chests and the four configured routes. Forcing
both neighboring chunks proves transport across a persisted chunk boundary; it
does not cover an initially unloaded target chunk becoming loaded later, or an
actual chunk unload/reload during one server process. A passing gate does not
prove that every original user world reproduces the reported failure.
