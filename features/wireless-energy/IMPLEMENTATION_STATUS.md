# Wireless Feature Implementation Status

Branch: `feature-wireless-energy-networks` (isolated from `projekt-performance`).

## Implemented as source patches (subject to CI)

- `apply-wireless-runtime.py`: registers only **Network Transmitter** and **Network Receiver** blocks/items/blockentities and NeoForge FE BLOCK capabilities.
- `WirelessNetworkData` (MinecraftServer SavedData, 26.1 format): named network IDs, owners, five charging-category bit flags, persistence. Main is a default public network.
- `WirelessEnergyRuntime`: loaded-transmitter registry keyed by network ID and MinecraftServer (across dimensions). No chunk forcing or world scan; FE withdrawal on caller's `TransactionContext`, per-sender `SnapshotJournal`, recursion guard.
- Network Transmitter has up to 1,000,000 FE local buffer; insert-only capability. Network Receiver has extract-only capability and pushes into adjacent real FE targets every five server ticks, bounded to 16,000 FE, using rollback-safe simulated/coupled transactions. Loaded chunks only.
- `apply-wireless-ui-charging.py`: shared server-validating screen/menu for both blocks, network selection and creating automatically numbered named networks, chat `/wirelessnet create <name>` and `/wirelessnet list`, five individual toggle controls. 20-tick per-player charging in hotbar / inventory / armor / offhand / optional Curios via FE item capability and existing Obsidian EnergyTool.
- `apply-antenna-assets.py`: derived from the existing original Wireless Antenna model, distinct transmitter/receiver signal textures, 4-direction blockstates, item models, loot tables, crafting recipes and English labels.
- Tests: source behavioral guards (permissions, conservation, type count, five categories), regression for antenna model and PNG files.
- `inject-wireless-gametest.py`: **prepared, not yet wired to the workflow**. Injects live placed EnergyCell-to-Transmitter / air gap / Receiver-to-EnergyCell test, FE total conservation and transaction rollback.

## CI history

- **#233 red** (https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39080158716): new source patches generated, first Java compile failed solely because `ServerPlayer.hasPermissions(int)` does not exist in MC26.1. Fixed by owner-only authorization.
- **#234 red** (https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39080561724): all 65 existing performance Python tests pass; one new source-regression assertion had a wrong Java local variable name (`level` instead of actual `server`). Fixed.
- **#235** (https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39080622874): full compile and GUI/charging phase in progress at documentation time; don't call it green until Actions success.

## Not yet released

No playable feature JAR is proven yet. In particular there is **no confirmed** NeoForge compile for the GUI/charging pass, nor live FE GameTest, two-dimension crossdim GameTest, dedicated server restart/persistence and Curios on/off integration check. Fix CI until green; do not edit protected performance history or mark #232 as wireless.

## Follow-up

Wire the live FE GameTest after the existing postpatch GameTest-source injection, then verify item network separation and dynamic GUI state. Resolve source-shape and Java-API failures in the isolated feature workflow only. Run load/reload/FE conservation tests before offering a test JAR. Only after wireless is stable resume autocrat/storage/controller GUI tick spikes, mass crafting/deposit and exclusive autocraft job reservation in `projekt-performance`.

## Verifizierter Fortschritt Build #238 (18.10.2026)

- **Actions GRÜN**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39082417823, Commit `b464ea2fecb90e40b7fb613fc3da1f7e65c356a2`.
- Fehler #237 war **kein Transferfehler**, sondern das vorbestehende StateMachineTest-Zeitlimit von 190 Ticks nach Hinzufügen der 35-Tick-Wireless-Prüfung. #238 verlängert nur das Testzeitlimit **dieses einen** kombinierten Tests auf 250 Ticks, ohne Prüfungen zu entfernen.
- Beide GameTest-Server-Durchläufe: **8/8 grün**. Log: `WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS`, `WIRELESS_NETWORK_CORE_V1 PASS`, `WIRELESS_NETWORK_UI_CHARGING_V1 PASS`, `WIRELESS_ANTENNA_MODELS_V1 PASS` und `BUILD 101 ALL AUTOMATABLE GATES PASS`.
- Build-Artefakt https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39082417823/artifacts/12119770996 ; extrahierte JAR `xSxLabs-Network-Storage-1.1.1.jar`: **1.575.544 Bytes**, SHA-256 `4a7cfb018074f38dc6fd57962d71e5c72ff8dffa1afddc0ceac85eb885fcdb45`. Gefundene Klassen: Transmitter-/Receiver-Block und BE, WirelessNetworkData, WirelessEnergyRuntime, WirelessNetworkMenu/Screen, WirelessPlayerCharging, WirelessCuriosCharging. Keine `build103`-Testklassen; `neoforge.mods.toml` enthalten.
- **Nicht nachgewiesen**: echter Zwei-Dimensionen-Test, Server-Neustart und Wiederaufnahme mehrerer Netzwerke, optionaler Curios-Mod-Installations-/Deinstallationsfall, GUIs mit Client und Multiplayer unter realer Last. Noch nicht als Ingame-stabil deklarieren.
- Performance-Branch `projekt-performance` bleibt unverändert im Quell-/Workflow-Code; dort wurden ausschließlich zusätzliche, vom Nutzer gemeldete GUI-/Autocraft-Performance-Probleme dokumentiert.


## Build #239: Owner protection and bounded sender scheduling (18.10.2026)

- **Actions success**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39083431169; workflow commit `ab8eb4adf76354093b456faf0687b9ccbd0ca66c`.
- Generated Java hardening: `features/wireless-energy/apply-wireless-hardening.py`. Transmitter/Receiver store owner UUID; placed devices are claimed by placer, legacy ownerless devices on first GUI use; only owner may open configuration / trigger menu actions; network selection additionally checks `WirelessNetworkData.canAccess`.
- Receiver obeys **one global 16,000 FE budget across all six faces per 5-tick dispatch**, retaining atomic withdrawal/insert rollback. `WirelessEnergyRuntime.pull` rotates its sender start cursor among loaded matching transmitters, so no fixed-first sender preference.
- Guard tests: `tests/test_wireless_hardening.py`, reconstructed Java compile and pre-existing two-pass GameTests under unchanged test semantics. No Ingame or Multiplayer confirmation.
- Artifact: `xsxlabs-network-storage-v1.6-performance-candidate`, ID `12119049265`; reported ZIP digest `sha256:ea7472f80b8de9ac33819a7175e30d2ed6be8c88fc493201aa8e45db9a477c21` is **not** a JAR checksum.

## Build #240: Actual second-dimension GameTest (pending verification)

- Workflow commit `ce4ef34eb64e84fea122c48ab8692b95e432781a`, Actions run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39083789547 was in progress when documented; **no success claim until job completes**.
- New test-only injector `features/wireless-energy/inject-wireless-crossdim-gametest.py` adds a real Nether transmitter, 12,000 FE funded via FE transaction, and an existing Overworld receiver/sink; requires sink FE rise above original 8,000 and exactly 20,000 FE across both dimensions.
- Test alone loads its Nether fixture chunk; **production runtime does not force-load chunks**. The timeout is extended only for the combined StateMachineTest from 250 to 380 ticks; other tests unchanged. Post-patch log must contain `WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS`.
- Still open: gameplay check on a client and dedicated server, owner permissions on actual multiplayer, world reload persistence, optional Curios compatibility, creating/renaming/deleting via polished GUI, load/performance under dense receiver layouts.


## Build #240 failure and #241 retry

- **#240 RED**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39083789547. Reconstruction, Java compilation and original `WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS` succeeded. **True-crossdim assertion failed**, `BUILD103 GAMETEST: WIRELESS Nether FE actually reached overworld receiver and sink`; no claim of crossdim success.
- Root-cause hypothesis: test setup loads the Nether transmitter's chunk once without an enduring ticket. This is **not yet proven**, because #240 did not log loaded state and FE counters at failure.
- **#241**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39084598036, workflow commit `201db79f9041ac09f71a2b7cd08b8ed9d502f6ba` (initial status pending). Test fixture alone calls `nether.setChunkForced(...,true)` before the 40-tick window, releases on success, and prints `WIRELESS_CROSSDIM_DIAG_V1` before assertions. **The shipped transmitter/receiver runtime is unchanged and creates no chunk tickets.** If red, inspect whether FE is missing due to load state, capability, or scheduling; do not weaken exact conservation assertions.

## Named network management implementation (unverified)

- `apply-wireless-network-management.py` adds saved-data name/owner/mask bounds, owner-only `rename` and `delete` with immutable IDs, default Main kept immutable for charging and undeletable, and server-side Brigadier `/wirelessnet rename <id> <name>`, `/wirelessnet delete <id>`. GUI supports `Create named`, `Rename`, `Delete` through server-validated commands and now sends both filtered stable IDs and visible names.
- Deletion immediately disables old network transfer by existing `find(id)==null` checks. **It does not erase a transmitter's persisted FE buffer**; owner may reselect a valid network. Main is public for energy but read-only for global charging settings.
- `tests/test_wireless_network_management.py` enforces basic source contracts. **Not yet Java-compiled, GameTest-verified or Ingame-tested**; add patch to the feature workflow only after #241 finishes.


## #241 verified cross-dimension FE proof and #242 scope

- **#241 GREEN:** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39084598036, workflow commit `201db79f9041ac09f71a2b7cd08b8ed9d502f6ba`. Post-patch GameTest server reported **8/8 passed**, `WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS`, `WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS`. Diagnostic: `WIRELESS_CROSSDIM_DIAG_V1 active=false source=0 bridgeTX=0 sink=20000 netherTX=0 available=0` after transfer, showing exactly 20,000 FE retained at receiver sink. Feature runtime has no force-load API; only CI's temporary Nether fixture ticket was changed. Prior #240 failure was compatible with a not-kept-loaded source; it is not sufficient by itself to establish why the source had failed without the ticket.
- **#242** workflow commit `07d28a99f6368690bd86a23a646cfcb6dcc7a084`, run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085031061 in progress at recording. It includes the management patch and a real crossdim FE pull/abort rollback assertion. No compilation or GameTest result claimed until complete.
- Follow-on **not yet built**: block removal/dimension validation for stale `WirelessNetworkMenu` actions was tightened in `apply-wireless-hardening.py` (commit `4b30fe29da33f1ffc7353d79356376be72effd1f`). Add to a later workflow run, after #242, to avoid concurrent builds.


## #242 RED, #243 retry – runtime unchanged

- **#242 RED** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085031061, commit `07d28a99f6368690bd86a23a646cfcb6dcc7a084`. Source patch and GUI passed `WIRELESS_NAMED_NETWORK_MANAGEMENT_V2 PASS`; compile / existing first GameTest pass succeeded (8/8). Second GameTest failed in the new `WIRELESS Overworld lookup can transact with Nether source` same-tick rollback step. It ran immediately after placing/filling the Nether BE, before the normal registration callback could run.
- **#243** workflow commit `51dcd95306a8770199591a9db89fcb30e162f1e4`, run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085403205 initially in progress. In the *test fixture only*, immediately register the new Nether sender before the transactional rollback probe; check loaded/available and unchanged stored FE after abort. The later 40-tick passive transport test and exact conservation remain unchanged. Also includes the stale/different-dimension GUI action guard.
- No production FE algorithm changes after #239; no private source or performance-branch modifications in this sequence.


## Additional pending UI safety patch

- After #243 started, `apply-wireless-network-management.py` gained two-click deletion confirmation keyed to the selected network ID (commit `d500cb555a171602372d4924b9adf44a75106279`), with matching source test commit `215a2e700ac5bb9bdc3b685db472772aace95f95`. This patch must be included in a *subsequent* CI run; it does **not** affect #243's already checked-out sources.
- Open for actual client tests: data-slot refresh for network labels during out-of-band rename/delete, manual multiplayer permissions and Curios optional-modded startup.


## #243 GREEN, #244 functional/performance build

- **#243 Actions SUCCESS** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085403205, workflow commit `51dcd95306a8770199591a9db89fcb30e162f1e4`. Both real GameTest passes **8/8**, named network management patch generated/compiled, `WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS` and `WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS`; earlier direct Nether transactional abort regression also passed. The FE diagnostic was `active=false source=0 bridgeTX=0 sink=20000 netherTX=0 available=0`. Artifact ZIP ID `12119974112`, digest `sha256:24f5be9ab924324be4135c912cb44e6646c81a46019c0314a548d3d44bb1647f` is ZIP digest **not** user JAR hash.
- **#244** workflow commit `83f9300f16c28bbbda09b602d215c6cb5d4f63db`, run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085875869 queued at documentation time. Adds the two-click same-ID delete confirmation and `apply-wireless-charging-single-pass.py`: once-per-player/20-tick inventory/hotbar/armor/offhand/Curios enumeration across all matching networks, global max 16,000 FE, preserving `chargeOne` transactional handling and individual charging category bitmasks.
- Still outstanding: real client GUI with keyboard entry and multiple players, Curios installed runtime, dedicated-server save/restart with several named networks and retained buffers, chunk unload/reload, loaded-grid performance with Spark. No Ingame stable designation.


## Prepared live NBT/Codec regression (not yet wired)

- `inject-wireless-persistence-gametest.py` (commit `427a5c5fa4cc241108f9e49d72ee50fafebabc2c`) tests the actual Minecraft 26.1 `saveWithFullMetadata` / `BlockEntity.loadStatic` roundtrip of a real 12,000 FE Nether transmitter, plus `WirelessNetworkData.Entry.CODEC` roundtrip of ID/name/owner/all five charging bits. `tests/test_wireless_persistence_codec.py` guards injection.
- This is **in-memory NBT/codec coverage only**, not a full dedicated-server filesystem save/restart. Run it in the next nonparallel CI build after #244, then separately verify real world persistence.


## #244 verified and #245 under test (18.10.2026)

- **#244 CI GREEN** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39085875869, workflow commit `83f9300f16c28bbbda09b602d215c6cb5d4f63db`. Both GameTest passes report **8/8**, real air-gap and Nether→Overworld conservation PASS, plus `WIRELESS_NAMED_NETWORK_MANAGEMENT_V3 PASS` and `WIRELESS_CHARGING_SINGLE_PASS_V1 PASS`. Archive artifact ID `12120952203`, ZIP digest `sha256:d9a79b576d0a8e1a8e6e61734cdd5d6a52f506fe580e1c35d334e92273f951f6` (not a JAR checksum). No in-game claim.
- **#245** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39086382012, workflow commit `df1f3e99bb3305023285b0ddc3e307149e5fbbc6`, in progress at documentation time. Runs live BlockEntity NBT + SavedData network-entry codec roundtrip inside unchanged crossdim GameTest. **Not a real disk-save/server-restart verification.**
- Prepared but **not yet CI wired**: `apply-wireless-index-hotpath.py` (`bf0c3086fa4b3a904083d10bf1f9982d4e77ac59`) makes the receiver sample available sender energy once per five-tick dispatch and unregister matching senders directly by network ID; no change to FE rollback/conservation. `tests/test_wireless_index_hotpath.py` source contracts. Next CI only after #245 outcome.


## #245 verified, #246 receiver/menu performance gate

- **#245 CI SUCCESS** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39086382012, workflow commit `df1f3e99bb3305023285b0ddc3e307149e5fbbc6`. Both GameTest passes report **8/8**, `WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1 PASS` confirms real Minecraft NBT 12,000 FE transmitter roundtrip and five-category network Entry CODEC roundtrip, crossdim real FE still PASS. Artifact ZIP ID `12121121504`, SHA-256 `7480a9884de64e272a2aa1abd2530c6c8597451ec8a5206072666721f34d3449` (ZIP, not JAR). **No real saved-disk restart performed**.
- **#246** workflow commit `537466cd9687db897f8d34c074cf482237f869e6`, https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39086905540 initially queued. Runs `apply-wireless-index-hotpath.py` and `apply-wireless-menu-sync-cache.py` after the proven wireless patch stack. One loaded-sender availability index walk per five-tick receiver dispatch, targeted unregister by network ID; one available-network list snapshot per Wireless menu/server tick rather than per polled data index. FE transactional rollback and global 16k budget unchanged. Final result pending.
- The standalone user-facing client/Curios/multiplayer/dedicated-server restart acceptance guide is now `features/wireless-energy/INGAME_ACCEPTANCE.md`.


## #246 red source-test assertion, #247 fix (18.10.2026)

- **#246 RED** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39086905540; failure during the first **Python source unit tests** only: `test_wireless_index_hotpath.py` incorrectly used `assertNotIn` on the patch file, which intentionally contains the obsolete code as an exact find-and-replace anchor. No Java compilation, FE transport or GameTest outcome was reached in this build. Existing optimized #245 remains the last green reference.
- Test corrected in commit `9d5b46fecf8acb24571b1830db1cb05d6599875b`. Additionally, #247 CI checks the **generated Java** for absence of the obsolete all-network unregister loop; this is the correct place for the negative assertion, not the patch's input matcher.
- **#247** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39087000101, workflow commit `4b0d1c3f044f619c41cd641a0dfb6a03b9e809a8`, running at documentation time. No success claim until both original eight-test GameTest passes.


## Receiver idle-path follow-up (not part of #247 pinned checkout)

- Review identified that the first `apply-wireless-index-hotpath.py` version eagerly queried the sender index even when none of the receiver's six faces had an FE capability. This would cause extra work for disconnected/idle receivers, contrary to the feature's performance target.
- Pending corrected patch commit `c3643a78bbb058690b61674cfe7d7f30f7616be8`: initialize `remainingSupply=-1` and resolve `WirelessEnergyRuntime.available` only after a real neighboring FE target is discovered. The first lookup remains cached for the rest of the receiver work tick, with the 16,000 FE budget and commit-only accounting unchanged.
- Contract adjustment `e04c1ab7f3a916675d29da19531b9460489655f0`. This fix is **not** in #247's already-pinned workflow revision; include it only in a later sequential run and check idle receiver source gates.


## #247 verified, #248 lazy receiver guard

- **#247 GREEN** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39087000101, workflow commit `4b0d1c3f044f619c41cd641a0dfb6a03b9e809a8`. Both passes **8/8 GameTests**, crossdim FE and persistence CODEC PASS. `WIRELESS_RECEIVER_SINGLE_INDEX_WALK_V1 PASS` and `WIRELESS_MENU_ONE_NETWORK_SNAPSHOT_PER_TICK_V1 PASS`. Archive artifact `12121103542`, ZIP digest `sha256:8921d0bac1cc1433613f1fc30bfc94aefde46b696aa8a4a45297c14c5f862ad4` (not JAR SHA). These passing assertions do not provide measured MSPT improvements.
- **#248** workflow commit `5a40ab13974b29450ef072a0c73bb15a16d5bb01`, run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39087363211 queued at reporting time. Adds lazy supply lookup only after a valid FE-capable neighbor, retaining the per-dispatch index cap and 16k FE conservation. Source gate checks target detection precedes index lookup and only one available() call in receiver tick.
- Branches `projekt-performance` and private source remain unmodified. Distinct in-game client, multiplayer, installed Curios and dedicated-server **disk restart** validation remain open.


## #248 GREEN and #249 loaded-sender isolation (18.10.2026)

- **#248 CI SUCCESS**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39087363211, workflow commit `5a40ab13974b29450ef072a0c73bb15a16d5bb01`; both GameTest runs **8/8**, real crossdim conservation `WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS`, NBT `WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1 PASS`, `WIRELESS_RECEIVER_LAZY_INDEX_WALK_V2 PASS` and `WIRELESS_MENU_ONE_NETWORK_SNAPSHOT_PER_TICK_V1 PASS`. Archive artifact `12120554421`, ZIP SHA-256 `382161a29a25571d441cabf3bfc8f96a43a0091af2ff5b056a421b37118e8f5b` (NOT a packaged-JAR hash). No Ingame confirmation.
- **#249**: fixed an accidentally commented-out source-regression assertion in `tests/test_wireless_index_hotpath.py` (commit `98333209f878be71edc0016671527fed854f9d03`). Added GameTest-only `inject-wireless-source-isolation-gametest.py` and source contract: using the real Nether 12,000 FE transmitter, attempts selecting an unknown network ID (must fail), explicitly unregisters loaded source (all available/pull returns 0, FE stays 12k), then re-registers (source becomes available). Existing remote rollback, NBT and 20,000 FE exact conservation checks unchanged. Workflow commit `76f9eadb24badb3737cbf4f659a9adc049a8c422`, Actions run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39088421283 running at documentation time. **No success claim until complete**.
- This detach/reattach test validates the loaded-sender registry lifecycle, **not** actual chunk unloading via player travel, not real server disk restart. Client/Curios/multiplayer, real Spark-load baseline remain open.


## #249 verified and #250 real two-process server restart (18.10.2026)

- **#249 Actions SUCCESS** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39088421283; workflow commit `76f9eadb24badb3737cbf4f659a9adc049a8c422`. The previously disabled Python source assertions were restored and the live Nether transmitter FE index detach/re-register + unknown-ID test was included; final Actions job succeeded. This models loaded-index lifecycle but is not a real chunk unload test.
- **#250** workflow commit `df28b988244a2f2b6682c370bfe1e545325c3c05`, Actions run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39088970886 started and was in progress when documented. `apply-wireless-dedicated-restart-probe.py` extends the existing successful two-dedicated-JVM same-world ITEM regression without altering its checks. The first JVM saves a real 12,000 FE Network Transmitter (without an active Receiver). The second JVM must read that same saved BlockEntity with **exactly** 12,000 FE, observe registered live FE, place a Receiver + actual Energy Cell **only after** restart, then prove FE arrives with total conservation = 12,000. This runs via the existing isolated CI-only subscriber, removed before final JAR packaging.
- Workflow gates reject absent after-restart FE or a false/missing same-world/distinct-JVM report and require an actual `WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS` line from the second JVM log. **Do not claim success before run #250 finishes**.
- Still outstanding: private named networks / owner permissions across a real disk restart, Curios installed and absent, full client GUI/multiplayer, unloaded chunk runtime lifecycle and Spark MSPT load comparisons.


## #250 verified and #251 private-network disk restart test (18.10.2026)

- **#250 Actions SUCCESS** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39088970886, commit `df28b988244a2f2b6682c370bfe1e545325c3c05`. Two distinct dedicated JVMs processed one actual saved world and the CI job passed mandatory `WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS` + persisted 12,000 FE / real new Receiver-to-Energy Cell conservation assertions. Existing two 8/8 GameTest passes and original ITEM restart regression remained required. Artifact archive ID `12121549809`, SHA-256 `a7eba24f264667cf305c2bc243e3929de196f00c2b1eba7f36c1d3a70aa2eac2` refers to the ZIP, not the contained JAR.
- **#251** source commit `6dd679797c2e6b2ce0e255c834d425bb7d90a53c` introduced CI-only `apply-wireless-private-network-restart-probe.py`. It seeds two private networks with distinct ID/name/UUID owner and category masks (17 and 6) using test-only reflection because the headless dedicated fixture has no ServerPlayer; the actual `WirelessNetworkData` persistence codec and server data storage remain real. Sender binds to the first private network before saving. In second JVM, SavedData and transmitter must restore; a Receiver bound to the **other** private ID must transfer zero FE for 20 ticks, then rebind and receive FE with exactly 12,000 FE conservation.
- Source regression adds a real combined injector dry-run against the committed Java restart fixture (`tests/test_wireless_private_network_restart.py`); **#251 workflow** commit `1d599019e44e18b3d542c1a8da8c122748b69797`, run https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39090092742 started. **Result not yet confirmed.** Existing FE/GameTests, original ITEM-restart assertions, second-JVM test and test-class exclusion are unchanged.
- Remaining distinct coverage: authorization using two real ServerPlayers (this fixture seeds owners but cannot test owner command permissions), GUI refresh and client key input, Curios absent/present runtime, chunk unload under player travel, and load-scaled Spark MSPT checks. Keep `projekt-performance` unchanged until wireless gates stable.
