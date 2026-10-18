# Performance + Wireless — Green checkpoint #277 (2026-10-18)

- **Verified CI:** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39142786613
- **Branch and commit:** `projekt-performance-wireless` @ `4b8da1a19bcc1d81ee01e90719bf2505f66ef81c`
- **Immutable recovery branch:** `freeze/performance-wireless-b277-drive16-green`
- **Status:** final Gradle build successful; 89 Python regression tests successful; postpatch Minecraft GameTests and optional Curios-present GameTests successful. This is a **CI checkpoint**, not a passed Minecraft client/render benchmark.

## Critical Drive regression fixed

- Prior failing #274 checked the unoptimized 8-slot DriveMenu **before** the patch. Its GameTest reported `Drive GUI backing container truncated to 8`.
- #275 additionally failed on test-string quoting, #276 on injecting while the CI-only GameTest source was temporarily removed.
- #277 correctly restores the fixture and checks the **compiled postpatch DriveMenu$DriveContainer** with 16 real inserted cells and 16 nonempty readable GUI slots. GameTest marker `DRIVE_GUI_ALL_16_REAL_CELLS_GAMETEST_V1 PASS` appears in the successful Java logs.
- The original 50-drive fixture populates 800 real StorageCellItems; DriveMenu uses `CELL_SLOTS=16`, ejection starts at slot `StorageDriveRuntime.SLOTS-1`, and BE `cell_inventory` save/load is unchanged. No inventory migration or bulk cell deletion is introduced.
- Other preserved checks: FE conservation and wireless sender/receiver, Curios absent/present, smithing-upgraded-only tool charging, autocraft reservation, terminal and conduit test gates.

## Non-regression release checklist (still needs player/server test)

1. Backup world; compare cell counts **all 16 slots including 8..15** before and after re-opening GUI, block break/replacement and dedicated-server stop/restart.
2. Verify client visually renders and allows inserting/removing cells 8..15 (server backing GameTest does not prove texture/widget visibility).
3. Compare storage counts, items and tools after heavy extraction/insertion; no duplication or lost cell NBT.
4. Mass-craft and bulk-deposit bursts, autocrafting job reservation and cancel/refund, GUI open/close on 50 full drives and controller; record TPS/MSPT mean, p95/p99/max and GC.
5. Test wireless charging with unupgraded ordinary tools (must remain durability-based) and only owner on the network; ensure no FE duplication.
6. ITEM conduit physical transfer after real server shutdown/restart using the same persisted world.

## Next performance measurement

The last supplied `NjeYDIr1Da.sparkprofile` was sampled before the #271–#273 improvements. It **cannot** establish the hotpaths or gains of Build #277. Do not apply an additional caching shortcut just on the older percentages.

A/B measurement should use exact #277 JAR filename/SHA-256, same saved test world and hardware, fixed workload durations of 60–120 s: idle; Obsidian Solar -> ENERGY cable; Powah Solar -> ENERGY cable; conduit transfer; 0/10/50/100 wireless receivers; GUI opening 1 and 50 drives; burst crafting/deposit; autocrafter reservation job/cancel. For each phase collect server-thread Spark, TPS, MSPT mean/p95/p99/max, GC, FE conservation and item counts. Use the prior version on the same setup as baseline if safely available; never test on the only copy of a valuable world.

Only after the #277 paired profile identifies a still-dominant and regression-testable hotspot should the next runtime patch be applied to `projekt-performance-wireless`, with a separate CI green gate and explicit rollback to the frozen branch.

## Observed CI storage benchmark: not a no-regression certificate

The #277 CI log ran its 50-drive benchmark twice, once on the pre-patch reconstruction and once on the postpatch source (9 trials × 2,000 operations; **these are task timings, not server MSPT**):

| Metric | pre-patch #277 | postpatch #277 |
|---|---:|---:|
| 50-drive median per trial (ns) | 3,577,163 | 8,195,914 |
| 50-drive p90 per trial (ns) | 7,521,425 | 8,991,528 |
| 20-tick storage-work p95 (ns) | 650,329 | 1,191,727 |
| Bulk deposit 100-cycle total (ns) | 7,902,149 | 8,154,638 |

The higher postpatch readings are a **potential performance regression signal**, not a verified server-level regression: the baseline and postpatch source/configuration differ, the run phases are short, JVM/JIT/GC warming and co-running GameTests are uncontrolled, and the benchmark explicitly logs `not_server_MSPT=true`. In comparison, the older successful #273 reported 50-drive medians of 8,204,112 ns prepatch and 5,941,614 ns postpatch, indicating substantial run-to-run variance. Do not claim #277 improves overall MSPT or claim that it is regression-free on the strength of green functional tests alone.

Next performance change must be gated by a controlled, identical-JAR-world-load A/B measurement and 50-drive/GUI persistence tests. Preserve the green #277 recovery ref for rollback.
