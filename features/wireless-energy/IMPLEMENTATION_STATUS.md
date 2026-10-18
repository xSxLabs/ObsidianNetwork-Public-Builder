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
