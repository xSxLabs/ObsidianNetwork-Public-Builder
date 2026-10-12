# Build 106 transport stress fixture

The existing frozen Build 106 JAR is loaded by the separate NeoForge server workflow.

## Required acceptance conditions

- Item importers pull from actual inventories.
- Item exporters send to actual inventories.
- Fluid importers pull from mod fluid tanks.
- Fluid exporters fill destination tanks.
- Item and fluid cables connect both sides.
- At least 100 simultaneous endpoints per transport type.
- Each direction has before/after inventory and tank volume measurements.
- Each scenario captures average/p95 MSPT and server logs.
- Zero transport results must fail the run, not be recorded as success.

The current RCON-only test does not configure these endpoints. A CI-only
NeoForge fixture with access to block entity APIs is required; do not
claim a transport benchmark before the fixture is executed.
